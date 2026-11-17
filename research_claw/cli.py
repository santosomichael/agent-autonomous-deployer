import sys,os,subprocess,json,shlex,stat
from pathlib import Path
from urllib.request import urlopen
from .core import *
INV=ROOT/'inventory/target.yaml'
def mark(ok,label,detail=''):print(f" [{'x' if ok else ' '}] {label}"+(f": {detail}" if detail else ''))
def ensure_key(path):
 p=Path(path).expanduser();
 if p.exists():return True
 print('\nNo SSH key found. Creating one now.')
 p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 return subprocess.run(['ssh-keygen','-t','ed25519','-f',str(p),'-N','','-C','research-claw-controller']).returncode==0
def make_inventory():
 print('\nONE-CLICK SETUP\nThe wizard will create the inventory, prepare SSH, check Ollama, configure restricted sudo, then deploy.')
 host=ask('Target IP or hostname');user=ask('Target Linux username');port=int(ask('SSH port','22'))
 key=ask('SSH private key','~/.ssh/id_ed25519');ollama=ask('Ollama URL','http://127.0.0.1:11434');model=ask('Ollama model','qwen3:14b')
 c={'project':ask('Project name','research-lab'),'target':{'host':host,'port':port,'user':user,'identity_file':key,'accept_new_host_key':True,'connect_timeout_seconds':8},'inference':{'base_url':ollama,'model':model,'timeout_seconds':10},'deployment':{'workspace':'~/research-stack','recipes':['00_discovery','10_base_linux','20_python','30_docker','40_gpu_validate','50_pytorch','60_sionna','90_final_verify']}}
 save(INV,c);return c
def setup_access(c):
 t=c['target'];key=Path(t['identity_file']).expanduser()
 if not ensure_key(key):return False
 os.chmod(key,0o600)
 print('\nConnecting once to record the target host key. Verify the fingerprint shown by SSH.')
 subprocess.run(ssh_base(t,batch=False)+['exit'])
 r=remote(t,"printf '%s' READY")
 if r['exit_code']!=0:
  print('\nPublic-key login is not ready. The target password may be requested once to install your public key.')
  cp=subprocess.run(['ssh-copy-id','-p',str(t.get('port',22)),'-i',str(key)+'.pub',f"{t['user']}@{t['host']}"])
  if cp.returncode:return False
 r=remote(t,"printf '%s' READY");mark(r['exit_code']==0,'Non-interactive SSH',(r['stdout']+r['stderr']).strip())
 if r['exit_code']:return False
 print('\nConfiguring restricted passwordless sudo. The target password may be requested once.')
 user=t['user'];rule=f"{user} ALL=(root) NOPASSWD: /usr/bin/apt-get, /usr/bin/systemctl, /usr/sbin/usermod, /usr/bin/docker\n"
 cmd="sudo sh -c "+shlex.quote("printf %s "+shlex.quote(rule)+" > /etc/sudoers.d/research-claw && chmod 440 /etc/sudoers.d/research-claw && visudo -cf /etc/sudoers.d/research-claw")
 rc=subprocess.run(ssh_base(t,batch=False)+['-tt',cmd]).returncode
 return rc==0
def preflight(c):
 t=c['target'];checks=[]
 key=Path(t['identity_file']).expanduser(); checks.append(('SSH private key',key.is_file(),str(key)))
 try:socket.create_connection((t['host'],t['port']),8).close();checks.append(('Target TCP',True,f"{t['host']}:{t['port']}"))
 except Exception as e:checks.append(('Target TCP',False,str(e)))
 r=remote(t,"printf '%s' READY");checks.append(('Non-interactive SSH',r['exit_code']==0,(r['stdout']+r['stderr']).strip()))
 r=remote(t,"uname -srm; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader");checks.append(('Target and GPU',r['exit_code']==0,(r['stdout']+r['stderr']).strip()))
 sudo="sudo -n /usr/bin/apt-get --version >/dev/null && sudo -n /usr/bin/systemctl --version >/dev/null && sudo -n /usr/sbin/usermod --help >/dev/null"
 r=remote(t,sudo);checks.append(('Autonomous sudo',r['exit_code']==0,(r['stdout']+r['stderr']).strip() or 'ready'))
 try:
  data=json.load(urlopen(c['inference']['base_url'].rstrip('/')+'/api/tags',timeout=10));names=[x.get('name','') for x in data.get('models',[])];checks.append(('Ollama API',True,c['inference']['base_url']));checks.append(('Ollama model',c['inference']['model'] in names,f"wanted={c['inference']['model']}; available={', '.join(names)}"))
 except Exception as e:checks.append(('Ollama API',False,str(e)))
 for n,ok,d in checks:mark(ok,n,d)
 return all(x[1] for x in checks)
def deploy(c,resume=False):
 slug=c['project'].replace(' ','_');statef=ROOT/'state'/f'{slug}.json';logf=ROOT/'logs'/f'{slug}.jsonl';reportf=ROOT/'reports'/f'{slug}.md'
 state=json.loads(statef.read_text()) if resume and statef.exists() else {'status':'running','completed':[],'failed':None}
 for rec in recipes(c):
  name=rec['name']
  if name in state['completed']:continue
  print(f"\n=== {name}: {rec.get('description','')} ===")
  for kind in ('precheck','commands','verify'):
   for raw in rec.get(kind,[]):
    cmd=raw.replace('{{ workspace }}',c['deployment']['workspace']);print(f"[{kind}] {cmd}")
    res=remote(c['target'],cmd,timeout=int(rec.get('timeout_seconds',1800)))
    with logf.open('a') as f:f.write(json.dumps({'phase':name,'kind':kind,**res})+'\n')
    if res['stdout']:print(res['stdout'],end='')
    if res['stderr']:print(res['stderr'],end='',file=sys.stderr)
    if res['exit_code']:
     state.update(status='failed',failed={'phase':name,'command':cmd,'exit_code':res['exit_code']});statef.write_text(json.dumps(state,indent=2));reportf.write_text(f"# Deployment report\n\nStatus: failed\n\nPhase: {name}\n\nLog: {logf}\n");return False
  state['completed'].append(name);statef.write_text(json.dumps(state,indent=2))
 state.update(status='completed',failed=None);statef.write_text(json.dumps(state,indent=2));reportf.write_text(f"# Deployment report\n\nStatus: completed\n\nCompleted: {', '.join(state['completed'])}\n\nLog: {logf}\n");return True
def main():
 print('Research Claw One-Click Deployer')
 c=load(INV) if INV.exists() and ask('Use existing inventory?','Y').lower().startswith('y') else make_inventory()
 if not setup_access(c):print('SSH or sudo setup failed. Fix the displayed target-side error and run ./run.sh again.');return 2
 print('\nPreflight checklist:')
 if not preflight(c):print('\nPreflight failed. Nothing was installed.');return 2
 print('\nDeployment plan:');[print(f" [ ] {x['name']} - {x.get('description','')}") for x in recipes(c)]
 if ask('Start deployment now? Type DEPLOY')!='DEPLOY':print('Stopped before installation.');return 0
 ok=deploy(c);print('\nDeployment completed.' if ok else '\nDeployment stopped. Run ./run.sh and choose the existing inventory after fixing the logged error.');return 0 if ok else 3
if __name__=='__main__':raise SystemExit(main())
