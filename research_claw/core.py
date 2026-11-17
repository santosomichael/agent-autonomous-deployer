from pathlib import Path
from urllib.request import urlopen
import subprocess, socket, shlex, json, time, yaml, os
ROOT=Path(__file__).resolve().parent.parent

def ask(label,default=None,secret=False):
    prompt=f"{label}"+(f" [{default}]" if default else "")+": "
    if secret:
        import getpass; v=getpass.getpass(prompt)
    else:v=input(prompt).strip()
    return v or default

def ssh_base(c,batch=True):
    a=['ssh','-p',str(c.get('port',22)),'-i',str(Path(c['identity_file']).expanduser()),'-o','IdentitiesOnly=yes','-o',f"ConnectTimeout={c.get('connect_timeout_seconds',8)}",'-o',f"StrictHostKeyChecking={'accept-new' if c.get('accept_new_host_key') else 'yes'}"]
    if batch:a += ['-o','BatchMode=yes']
    return a+[f"{c['user']}@{c['host']}"]
def remote(c,cmd,batch=True,tty=False,timeout=1800):
    a=ssh_base(c,batch)
    if tty:a.insert(1,'-tt')
    start=time.time();p=subprocess.run(a+["bash -lc "+shlex.quote(cmd)],text=True,capture_output=not tty,timeout=timeout)
    return {'command':cmd,'exit_code':p.returncode,'stdout':'' if tty else p.stdout,'stderr':'' if tty else p.stderr,'duration_seconds':round(time.time()-start,2)}
def load(path):return yaml.safe_load(Path(path).read_text())
def save(path,c):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(yaml.safe_dump(c,sort_keys=False))
def recipes(c):
 out=[]
 for n in c['deployment']['recipes']:
  p=ROOT/'recipes'/f'{n}.yaml';d=yaml.safe_load(p.read_text());d['_file']=str(p);out.append(d)
 return out
