import argparse, sys, shutil
from pathlib import Path
from .config import load_inventory, repo_root
from .preflight import run_checks
from .runner import Runner

GREEN='\033[32m'; RED='\033[31m'; CYAN='\033[36m'; RESET='\033[0m'
def c(text,color): return color+text+RESET if sys.stdout.isatty() else text
def show_checks(checks):
    for x in checks: print(f" [{'x' if x['ok'] else ' '}] {x['name']}: {x['detail']}")
    return all(x['ok'] for x in checks)
def choose_inventory():
    default='inventory/target.yaml'; value=input(f'Inventory path [{default}]: ').strip() or default; return value
def wizard():
    print(c('Research Claw autonomous deployer',CYAN)); print('Preflight first. No target command runs until every required connection check passes.\n')
    path=choose_inventory()
    if not Path(path).exists():
        src=repo_root()/'inventory/examples/ubuntu-nvidia.yaml'; Path(path).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,path); print(f'Created {path}. Edit host, user, key, Ollama URL, and model; then run again.'); return 0
    return command_preflight(path,deploy_prompt=True)
def command_preflight(path,deploy_prompt=False):
    _,cfg=load_inventory(path); checks=run_checks(cfg); ok=show_checks(checks)
    if not ok: print(c('\nPreflight failed. Deployment was not started.',RED)); return 2
    print(c('\nAll preflight checks passed.',GREEN))
    if deploy_prompt:
        r=Runner(path,cfg); show_plan(r)
        if input('\nStart autonomous deployment? Type DEPLOY: ').strip()=='DEPLOY': return do_deploy(path,False,True)
    return 0
def show_plan(r):
    print('\nDeployment checklist:')
    for i,x in enumerate(r.recipes(),1): print(f" [ ] {i:02d}. {x['name']} - {x.get('description','')}")
def do_deploy(path,resume,yes):
    _,cfg=load_inventory(path); checks=run_checks(cfg)
    if not all(x['ok'] for x in checks): show_checks(checks); print(c('Deployment blocked by preflight.',RED)); return 2
    r=Runner(path,cfg); show_plan(r)
    if not yes and input('Type DEPLOY to continue: ').strip()!='DEPLOY': print('Cancelled.'); return 1
    ok=r.execute(resume=resume); print(('Completed.' if ok else 'Stopped on failure.')+f'\nLog: {r.log}\nReport: {r.report}\nState: {r.state}'); return 0 if ok else 3
def init_inventory(path):
    src=repo_root()/'inventory/examples/ubuntu-nvidia.yaml'; p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): print(f'{p} already exists'); return 1
    shutil.copy2(src,p); print(f'Created {p}. Edit it, then run: research-claw preflight {p}'); return 0
def main():
    ap=argparse.ArgumentParser(prog='research-claw'); sub=ap.add_subparsers(dest='cmd')
    x=sub.add_parser('init'); x.add_argument('inventory')
    for name in ('preflight','plan','status'):
        x=sub.add_parser(name); x.add_argument('inventory')
    for name in ('deploy','resume'):
        x=sub.add_parser(name); x.add_argument('inventory'); x.add_argument('--yes',action='store_true')
    a=ap.parse_args()
    try:
        if not a.cmd: return wizard()
        if a.cmd=='init': return init_inventory(a.inventory)
        if a.cmd=='preflight': return command_preflight(a.inventory)
        _,cfg=load_inventory(a.inventory); r=Runner(a.inventory,cfg)
        if a.cmd=='plan': show_plan(r); return 0
        if a.cmd=='status': print(r.state.read_text() if r.state.exists() else 'No deployment state yet.'); return 0
        return do_deploy(a.inventory,a.cmd=='resume',a.yes)
    except KeyboardInterrupt: print('\nCancelled.'); return 130
    except Exception as e: print(c(f'Error: {e}',RED),file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
