import subprocess, socket, shlex, time
from pathlib import Path

class SSH:
    def __init__(self,cfg): self.cfg=cfg
    def args(self):
        c=self.cfg; strict='accept-new' if c.get('accept_new_host_key',False) else 'yes'
        return ['ssh','-p',str(c.get('port',22)),'-i',c['identity_file'],
          '-o','BatchMode=yes','-o',f'ConnectTimeout={int(c.get("connect_timeout_seconds",8))}',
          '-o',f'StrictHostKeyChecking={strict}',f'{c["user"]}@{c["host"]}']
    def tcp_check(self):
        with socket.create_connection((self.cfg['host'],int(self.cfg.get('port',22))),timeout=int(self.cfg.get('connect_timeout_seconds',8))): return True
    def run(self,command,timeout=1800):
        start=time.time()
        p=subprocess.run(self.args()+['bash','-lc',command],text=True,capture_output=True,timeout=timeout)
        return {'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'duration_seconds':round(time.time()-start,2)}
