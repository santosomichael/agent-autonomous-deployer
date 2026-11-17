# Research Claw

Portable autonomous SSH deployer for an OpenClaw controller, a remote Ollama GPU inference server, and Linux target machines.

## Safety model

- Recipes, not the LLM, contain executable installation commands.
- Every remote command, output, duration, and exit code is logged.
- The CLI tests SSH and Ollama before deployment.
- Destructive shell patterns are blocked unless explicitly enabled.
- `sudo -n` is checked before autonomous installation. Configure narrowly scoped passwordless sudo on the target.
- Secrets and private keys are never stored in this repository.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp inventory/examples/ubuntu-nvidia.yaml inventory/my-lab.yaml
research-claw init inventory/my-lab.yaml
research-claw preflight inventory/my-lab.yaml
research-claw deploy inventory/my-lab.yaml
```

Running `research-claw` with no subcommand starts the interactive checklist wizard.

## What the wizard checks

1. Inventory parses correctly.
2. SSH key exists and has safe permissions.
3. Target resolves and TCP port 22 is reachable.
4. Host key is already trusted, unless `accept_new_host_key: true` is configured.
5. Non-interactive SSH works.
6. Target OS, architecture, disk, RAM, GPU and NVIDIA driver can be discovered.
7. `sudo -n true` succeeds when selected recipes require root.
8. Ollama `/api/tags` is reachable on the RTX server.
9. The configured planning model is present.
10. Recipes are resolved and shown before execution.

## Commands

```bash
research-claw                 # interactive wizard
research-claw init FILE       # create/edit inventory interactively
research-claw preflight FILE  # connection checks only
research-claw plan FILE       # show exact phases and commands
research-claw deploy FILE     # preflight, confirmation, execute, verify
research-claw resume FILE     # continue after the last completed phase
research-claw status FILE
```

Use `--yes` with `deploy` only after you trust the inventory and recipes. The first deployment should be attended.

## OpenClaw integration

Point an OpenClaw shell-capable agent at this repository and instruct it to run only:

```bash
research-claw deploy inventory/my-lab.yaml --yes
```

The agent prompt in `agents/coordinator.md` forbids inventing shell commands and requires it to use the recipe runner.

## Important scope

The included recipes provide a functioning base, Python virtual environment, Docker, GPU validation, PyTorch, Sionna and final verification. Isaac Sim is represented by a guarded placeholder because its installation method, license acceptance, release, and container registry credentials vary. Pin and review an Isaac Sim recipe before enabling it. Omniverse Launcher is not treated as a current Linux server dependency; use NVIDIA's supported Isaac Sim distribution for your selected version.
