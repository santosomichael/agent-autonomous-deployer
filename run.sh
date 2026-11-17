#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Python 3 is required."; exit 1; }
if [ ! -d .venv ]; then
  python3 -m venv .venv || { echo "Install python3-venv, then run ./run.sh again."; exit 1; }
fi
. .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -e .
exec research-claw
