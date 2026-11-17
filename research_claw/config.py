from pathlib import Path
import os, yaml

def load_inventory(path):
    p=Path(path).expanduser().resolve()
    data=yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for key in ("project","target","inference","deployment"):
        if key not in data: raise ValueError(f"Missing inventory section: {key}")
    t=data["target"]
    for key in ("host","user"):
        if not t.get(key): raise ValueError(f"Missing target.{key}")
    inf=data["inference"]
    for key in ("base_url","model"):
        if not inf.get(key): raise ValueError(f"Missing inference.{key}")
    dep=data["deployment"]
    if not dep.get("recipes"): raise ValueError("deployment.recipes must not be empty")
    t["identity_file"] = str(Path(t.get("identity_file","~/.ssh/id_ed25519")).expanduser())
    return p,data

def repo_root():
    return Path(__file__).resolve().parent.parent
