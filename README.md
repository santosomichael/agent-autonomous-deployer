# Research Claw One-Click Deployer

This version performs controller setup, SSH-key creation, host trust, public-key installation, restricted sudo setup, preflight checks, and deployment from one wizard.

## Start

On the i7 WSL/Linux controller:

```bash
cd ~/agent-autonomous-deployer
./run.sh
```

That is the only command required. `run.sh` creates/activates `.venv`, installs the CLI, and opens the wizard. On the first run, answer the prompts for the target and Ollama server. The target password may be requested up to twice: once to install the SSH public key and once to create `/etc/sudoers.d/research-claw`. Passwords are not stored.

The wizard then checks:

- SSH key and target TCP connection
- Non-interactive SSH
- NVIDIA GPU and driver
- restricted passwordless sudo for `apt-get`, `systemctl`, `usermod`, and `docker`
- Ollama API and selected model

If all checks pass, type `DEPLOY`. It installs Ubuntu prerequisites, Python environment, Docker, PyTorch, and Sionna, then verifies the result.

## Later runs

```bash
./run.sh
```

Choose the existing inventory. No manual environment activation is required because `run.sh` handles it.

## Output

- `logs/PROJECT.jsonl`: every command, output, duration, and exit code
- `state/PROJECT.json`: completed and failed phases
- `reports/PROJECT.md`: final status

## Important constraints

- The default recipes support Ubuntu targets.
- The target must allow an initial password-based SSH login or an administrator must install your public key.
- The user must be allowed to use `sudo` during initial setup.
- Isaac Sim is not included yet. The detected 16 GB RAM and about 111 GB free disk are tight; use at least 32 GB RAM and preferably 150–250 GB free disk before adding a pinned Isaac Sim recipe.
- If an organization blocks password login or sudoers changes, an administrator must perform those two bootstrap actions. No program can bypass that policy safely.

## If the wizard stops

Read the displayed error and the latest record in `logs/`. Fix only the external blocker, then run `./run.sh` again. Typical blockers are wrong username, VPN/firewall, disabled password login, no sudo rights, unsupported non-Ubuntu OS, package-manager locks, insufficient disk, or incompatible GPU packages.
