# Ansify

A Python CLI tool that simplifies common Ansible workflows through interactive
playbook generation, validation, and Vault management.

**Developer:** Meet Sharma

## Features

- **Create** — guided interactive wizard that builds playbooks from 18 supported
  modules (User, Group, Package, Service, File, Copy, Template, Lineinfile,
  Replace, SELinux, Firewalld, Cron, Mount, LVM, Reboot, Wait For, Command/Shell,
  Authorized Key), with built-in per-module verification tasks.
- **Check** — local YAML validation plus `ansible-playbook --syntax-check` with
  simplified error output.
- **Vault** — encrypt, decrypt, and view secrets via `ansible-vault`.

## Install (GitHub Releases)

The project is distributed as a Python wheel attached to GitHub Releases
(built automatically by `.github/workflows/release.yml`). Install on any OS
with Python 3.9+:

```bash
pip install https://github.com/meets18/ansify/releases/download/v0.1.0/ansify_cli-0.1.0-py3-none-any.whl

ansify --version
```

> Dependencies (typer, rich, PyYAML) are pulled from PyPI automatically.
> For an isolated global install, use `pipx install <same URL>`.

## Install from source (any OS)

Clone and install with the same commands on any machine (RHEL, Ubuntu, WSL,
Windows):

```bash
git clone https://github.com/meets18/ansify.git ~/ansify
cd ~/ansify

python3 -m venv .venv && source .venv/bin/activate   # Windows: python -m venv .venv; .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -e .
ansify --version
```

> The `pip install --upgrade pip setuptools wheel` step is required on
> RHEL 9: its bundled setuptools (59.6) predates PEP 660 and will otherwise
> fail with "setup.py or setup.cfg not found".

## Install on RHEL 9 / 10

```bash
# 1. Ansible (needed for check / vault)
sudo dnf install -y ansible-core

# 2. Ansible collections used by generated playbooks
ansible-galaxy collection install ansible.posix community.general

# 3. Ansify (same GitHub Release URL as above, or git clone + install
#    from source as shown in the previous section)
pip install https://github.com/meets18/ansify/releases/download/v0.1.0/ansify_cli-0.1.0-py3-none-any.whl
```

> RHEL 9 ships Python 3.9 by default, which is supported. RHEL 10 ships 3.11.
> For Python 3.11 on RHEL 9: `sudo dnf install python3.11 python3.11-pip`.

## Releasing a new version

```bash
git tag v0.1.0            # bump as needed
git push origin v0.1.0    # GitHub Actions builds and attaches the wheel to a Release
```

## Usage

```bash
ansify                # interactive mode (menu hub)
ansify create         # guided playbook wizard
ansify check web.yml  # validate + syntax check
ansify vault encrypt secrets.yml
ansify vault decrypt secrets.yml
ansify vault view secrets.yml
```

Generated playbooks use only `ansible.builtin.*`, `ansible.posix.*`, and
`community.general.*` modules (FQCN), so they run anywhere Ansible is installed.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Project layout

```
ansify/
├── cli.py                  # Typer entry point (ansify command)
├── models/                 # Playbook + Task objects (in-memory playbook)
├── modules/                # 18 module definitions driving the wizard
├── generators/             # Playbook object -> YAML serialization
├── commands/               # create / check / vault
├── validators/             # YAML parsing + syntax check wrappers
├── utils/                  # inventory reader, yaml writer, verification
└── templates/              # drop Jinja2 templates referenced by template tasks
```

## Requirements

- Python 3.9+
- Ansible (ansible-core) for `check` and `vault` commands —
  Ansify builds playbooks on any OS, but validating and managing secrets
  requires a Linux environment (RHEL, WSL, or a managed Linux host).
