from pathlib import Path
from datetime import datetime, timezone
import json, yaml, shlex
from .config import repo_root
from .ssh import SSH
from .security import validate_command

class Runner:
    def __init__(self,inv_path,cfg):
        self.inv_path=Path(inv_path); self.cfg=cfg; self.root=repo_root(); self.ssh=SSH(cfg['target'])
        slug=''.join(c if c.isalnum() or c in '-_' else '_' for c in cfg['project'])
        self.log=self.root/'logs'/f'{slug}.jsonl'; self.state=self.root/'state'/f'{slug}.json'; self.report=self.root/'reports'/f'{slug}.md'
    def recipes(self):
        out=[]
        for name in self.cfg['deployment']['recipes']:
            p=self.root/'recipes'/f'{name}.yaml'
            if not p.exists(): raise FileNotFoundError(f'Recipe not found: {p}')
            data=yaml.safe_load(p.read_text()) or {}; data['_path']=str(p); out.append(data)
        return out
    def load_state(self):
        if self.state.exists(): return json.loads(self.state.read_text())
        return {'status':'ready','completed':[],'failed':None,'updated_at':None}
    def save_state(self,s):
        s['updated_at']=datetime.now(timezone.utc).isoformat(); self.state.write_text(json.dumps(s,indent=2))
    def log_record(self,phase,kind,result):
        rec={'timestamp':datetime.now(timezone.utc).isoformat(),'phase':phase,'kind':kind,**result}
        with self.log.open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    def render(self,text):
        return text.replace('{{ workspace }}',self.cfg['deployment'].get('workspace','~/research-stack'))
    def execute(self,resume=False):
        state=self.load_state() if resume else {'status':'running','completed':[],'failed':None}; self.save_state(state)
        for recipe in self.recipes():
            name=recipe['name']
            if name in state['completed']: continue
            for kind in ('precheck','commands','verify'):
                for raw in recipe.get(kind,[]):
                    cmd=validate_command(self.render(raw),self.cfg['deployment'].get('allow_destructive',False))
                    result=self.ssh.run(cmd,timeout=int(recipe.get('timeout_seconds',1800))); self.log_record(name,kind,result)
                    if result['exit_code']!=0:
                        state.update(status='failed',failed={'phase':name,'kind':kind,'command':cmd,'exit_code':result['exit_code']}); self.save_state(state); self.write_report(state); return False
            state['completed'].append(name); state['failed']=None; self.save_state(state)
        state['status']='completed'; self.save_state(state); self.write_report(state); return True
    def write_report(self,state):
        lines=[f"# Deployment report: {self.cfg['project']}","",f"- Status: **{state['status']}**",f"- Target: `{self.cfg['target']['user']}@{self.cfg['target']['host']}`",f"- Updated: {state.get('updated_at')}",f"- Log: `{self.log}`","","## Completed phases"]
        lines += [f"- {x}" for x in state.get('completed',[])] or ['- None']
        if state.get('failed'): lines += ["","## Failure","",f"```json\n{json.dumps(state['failed'],indent=2)}\n```"]
        self.report.write_text('\n'.join(lines)+'\n')
