from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import URLError
import json, os, stat
from .ssh import SSH

def run_checks(cfg):
    results=[]
    def add(name,ok,detail): results.append({'name':name,'ok':bool(ok),'detail':str(detail)})
    key=Path(cfg['target']['identity_file'])
    add('SSH private key',key.is_file(),key)
    if key.is_file() and os.name!='nt':
        mode=stat.S_IMODE(key.stat().st_mode); add('SSH key permissions',(mode & 0o077)==0,oct(mode))
    ssh=SSH(cfg['target'])
    try: ssh.tcp_check(); add('Target TCP connection',True,f"{cfg['target']['host']}:{cfg['target'].get('port',22)}")
    except Exception as e: add('Target TCP connection',False,e); return results
    r=ssh.run('printf READY',timeout=30); add('Non-interactive SSH',r['exit_code']==0,(r['stdout']+r['stderr']).strip())
    if r['exit_code']==0:
        d=ssh.run("uname -srm; printf '\n'; id -un; printf '\n'; df -Pk / | tail -1; printf '\n'; free -m | awk '/Mem:/{print $2}'; printf '\n'; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || echo NO_NVIDIA_GPU",timeout=60)
        add('Target discovery',d['exit_code']==0,(d['stdout']+d['stderr']).strip())
        if cfg['deployment'].get('require_passwordless_sudo',True):
            s=ssh.run('sudo -n true',timeout=20); add('Passwordless sudo',s['exit_code']==0,(s['stdout']+s['stderr']).strip() or 'available')
    url=cfg['inference']['base_url'].rstrip('/')+'/api/tags'
    try:
        with urlopen(Request(url,headers={'Accept':'application/json'}),timeout=int(cfg['inference'].get('timeout_seconds',10))) as resp: payload=json.load(resp)
        names=[m.get('name','') for m in payload.get('models',[])]
        add('Ollama API',True,url); wanted=cfg['inference']['model']
        add('Ollama model',wanted in names or any(n.split(':')[0]==wanted.split(':')[0] for n in names),f"wanted={wanted}; available={', '.join(names) or 'none'}")
    except Exception as e: add('Ollama API',False,e)
    return results
