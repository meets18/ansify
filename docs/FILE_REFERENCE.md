# Ansify — File Reference

This document explains **what every file does** and **what the code inside it does**,
function by function. Read `WORKFLOW.md` first if you want the end-to-end flow.

```
ansify/
├── pyproject.toml
├── README.md
├── LICENSE
├── requirements.txt
├── MANIFEST.in
├── .gitignore
├── .github/workflows/   ← release.yml (builds wheel, attaches to GitHub Releases)
├── ansify/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── models/          ← in-memory playbook objects (the core data)
│   ├── modules/         ← 18 module definitions that drive the wizard
│   ├── generators/      ← Playbook object → YAML text
│   ├── commands/        ← create / check / vault CLI commands
│   ├── validators/      ← YAML parse + ansible syntax-check wrappers
│   ├── utils/           ← inventory reader, yaml writer, verification builder
│   └── templates/       ← drop Jinja2 templates for `template` tasks here
└── tests/               ← pytest unit tests
```

---

## 1. Top-level files

### `pyproject.toml`
The packaging and dependency manifest (PEP 621).

| Section | What it does |
|---|---|
| `[build-system]` | Declares setuptools as the build backend, so `pip install .` works |
| `[project]` | Name, version (0.1.0), description, license |
| `requires-python` | `>=3.9` — deliberately RHEL-9-friendly (RHEL 9 ships Python 3.9; RHEL 10 ships 3.11) |
| `dependencies` | `typer` (CLI), `rich` (terminal UI), `PyYAML` (serialization) — nothing else |
| `[project.scripts]` | Registers the `ansify` executable → `ansify.cli:app` (the Typer app object) |
| `[tool.setuptools.packages.find]` | Discovers the `ansify` package for installation |
| `[tool.pytest.ini_options]` | Points pytest at the `tests/` directory |

### `requirements.txt`
Runtime dependencies for a manual install (`pip install -r requirements.txt`):
`typer`, `rich`, `PyYAML`.

### `MANIFEST.in`
Ensures the sdist (source tarball) includes docs, LICENSE, README, and the
`ansify/templates/` directory.

### `.github/workflows/release.yml`
GitHub Actions workflow: on every `v*` tag push it builds the wheel + sdist
with `python -m build` and attaches them to a GitHub Release, so users install
with `pip install <release wheel URL>`.

### `README.md`
User-facing documentation: features, RHEL 9/10 install steps
(including `ansible-galaxy collection install ansible.posix community.general`),
usage examples, project layout, requirements.

### `LICENSE`
MIT license text.

### `.gitignore`
Excludes `.venv/`, `__pycache__/`, build artifacts, egg-info, `.pytest_cache/`.

---

## 2. Package root: `ansify/`

### `ansify/__init__.py`
The package marker. Defines the single source of truth for the version:
```python
__version__ = "0.1.0"
```
`cli.py` imports it for `ansify --version`.

### `ansify/__main__.py`
Enables `python -m ansify` (mirrors the installed `ansify` command):
```python
from ansify.cli import app
if __name__ == "__main__":
    app()          # Typer app objects are callable → runs the CLI
```

### `ansify/cli.py`
The Typer entry point. What each piece does:

| Code | Purpose |
|---|---|
| `app = typer.Typer(...)` | Creates the app. `invoke_without_command=True` allows running with **no** subcommand, which opens the interactive hub |
| `app.command("create")(create.create)` | Registers `ansify create` → wizard in `commands/create.py` |
| `app.command("check")(check.check)` | Registers `ansify check <file>` |
| `app.add_typer(vault.app, name="vault")` | Nests the vault sub-app → `ansify vault encrypt/decrypt/view` |
| `@app.callback(...)` | Runs before any command. `--version`/`-V` prints the version and exits. If **no** subcommand was given, calls `create.menu()` — the interactive hub |

---

## 3. `ansify/models/` — the in-memory playbook

The design principle (per the project brief): **never write YAML by hand**.
Everything is built as Python objects; YAML is produced only at generation time.

### `ansify/models/task.py` — one task

```python
@dataclass
class Task:
    module: str                  # FQCN, e.g. "ansible.builtin.package"
    params: dict                 # module arguments, e.g. {"name": "httpd", "state": "present"}
    name: str                    # human-readable task name
    verify: list["Task"]         # verification sub-tasks (package_facts + debug, etc.)
    register: str | None         # var name if the result must be stored
```

Key method:

| Method | What it does |
|---|---|
| `to_dict()` | Serializes the task into an Ansible task mapping: `{"name": ..., "<module>": {params}, "register": ...}`. `register` is placed at **task level** (Ansible keyword), not inside module params — a common mistake the tests guard against |

### `ansify/models/playbook.py` — the whole playbook

```python
@dataclass
class Playbook:
    name: str            # play title
    hosts: str           # target host group, e.g. "webservers"
    become: bool         # sudo for the whole play
    tasks: list[Task]    # ordered task list
```

| Method | What it does |
|---|---|
| `add_task(task)` | Appends a task |
| `remove_task(index)` | Removes and returns a task (used by wizard "Delete a task") |
| `move_task(index, direction)` | Swaps a task with its neighbour, `direction` = -1 (up) or +1 (down) — powers the "Reorder tasks" menu; validates bounds so it never crashes |

`models/__init__.py` just re-exports both classes for clean imports.

---

## 4. `ansify/modules/` — the module registry (the heart)

### `ansify/modules/base.py` — the configuration schema
Defines the three dataclasses that make the wizard **data-driven**. Lives in its
own file (not `__init__.py`) to avoid the circular import that would otherwise
occur when module files import these types.

| Dataclass | Fields | Purpose |
|---|---|---|
| `Field` | `key`, `label`, `kind` (`text/choice/bool/int/multiline/optional`), `choices`, `default`, `required`, `help`, `condition` (ask only if earlier field == value), `if_module` (ask only for a chosen sub-module), `validate` | Describes one prompt in the wizard |
| `VerifyStep` | `module`, `params`, `name`, `register` | Describes one built-in verification task. `register` makes the main task store its result in that var |
| `ModuleDef` | `key`, `module` (FQCN), `label`, `category`, `fields`, `verify`, `verify_prompt`, `needs_become`, `task_name` (e.g. `"Install {name}"` for auto-naming) | The complete definition of one supported module |

### `ansify/modules/__init__.py` — the registry
| Code | Purpose |
|---|---|
| `MODULES = [package.MODULE, service.MODULE, ...]` | Collects all 18 definitions in one ordered list |
| `CATEGORIES` | Groups modules by category → drives the wizard's two-level menu (category → module) |
| `get_module(key)` | Looks up a definition by key (used when editing an existing task) |

### The 18 module definition files
Every file follows the identical shape. Example — `package.py`:

```python
MODULE = ModuleDef(
    key="package",
    module="ansible.builtin.package",          # FQCN → plays are collection-portable
    label="Package",
    category="Package Management",
    task_name="Install {name}",                # auto-suggested task name
    needs_become=True,
    fields=[
        Field("name", "Package name", kind="text", required=True),
        Field("state", "State", kind="choice",
              choices=["present", "absent", "latest"], default="present"),
    ],
    verify_prompt="Add verification (collect package facts and show the result)?",
    verify=[
        VerifyStep("ansible.builtin.package_facts", name="Gather package facts"),
        VerifyStep("ansible.builtin.debug",
                   {"var": "ansible_facts.packages['{name}']"},   # {name} filled later
                   name="Show package version"),
    ],
)
```

Special module files worth calling out:

| File | Special feature |
|---|---|
| `command.py` | Has a `__module__` field — a wizard choice between `command` and `shell` that **selects the module itself**; remaining fields (command, chdir, creates) apply to either |
| `service.py` | `verify` includes `register="svc_result"` → the main task automatically gets `register: svc_result`, then a `debug` task shows `svc_result.state` |
| `firewalld.py` | Same register+debug pattern; also a `target_type` field (`service` vs `port`) with conditional `service`/`port` fields via `condition` |
| `lvm.py` | Two sub-modules via `__module__` (`lvg`/`lvol`); fields use `if_module` so e.g. `lv`/`size` only appear for `lvol` |
| `copy.py` | Choice "local file (src)" vs "inline content"; `content` is a `multiline` field → becomes a `|-` block scalar in YAML |
| `file.py` | `src` asked only when `state=link` (condition); `recurse` only for `state=directory` |
| `lineinfile.py` | `state` is listed **before** `line` because `line`'s condition reads `state` |
| `wait_for.py` | `needs_become=False` (the only module besides command that doesn't need root) |
| `reboot.py` | All fields optional → a bare `ansible.builtin.reboot:` task is valid |

Full category→module map:

| Category | Files |
|---|---|
| Package Management | `package.py` |
| Service Management | `service.py` |
| User Management | `user.py`, `group.py`, `authorized_key.py` |
| File Management | `file.py`, `copy.py`, `template.py`, `lineinfile.py`, `replace.py` |
| Security | `selinux.py`, `firewalld.py` |
| Scheduling | `cron.py` |
| Storage | `mount.py`, `lvm.py` |
| System | `reboot.py`, `wait_for.py` |
| Commands | `command.py` |

---

## 5. `ansify/generators/` — YAML serialization

### `ansify/generators/yaml_generator.py`
The only place where playbook objects become YAML text.

| Piece | What it does |
|---|---|
| `_AMBIGUOUS` set | `yes/no/on/off/true/false/y/n/null/none/~` — values that YAML 1.1 would turn into booleans/null. Ansible parses YAML 1.1, so these MUST be quoted |
| `_should_quote(value)` | Decision function: quotes strings that (a) match ambiguous words, (b) start with a digit but aren't numbers (`8080/tcp`), (c) look like perms (`0644` — leading zero would be parsed as octal int), (d) start with YAML syntax chars (`{`, `*`, `&`, `- `...), (e) contain `: ` or ` #`. Returns `True` → single-quoted |
| `_represent_str()` | Custom PyYAML representer: **multiline strings → `|` block scalar** (`|-` when no trailing newline), ambiguous strings → single quotes, everything else plain |
| `AnsibleDumper` | Custom `SafeDumper` built on an `_IndentedEmitter` subclass that emits block sequences indented under their mapping key (course-style `tasks:` + indented `- name:` items). Also registers a bool representer rendering `yes`/`no` instead of `true`/`false` |
| `generate_yaml(playbook)` | Builds the top-level document dict (`name`, `hosts`, `become`, `tasks`), wraps it in a list (single-play list form, like hand-written playbooks), and flattens each task **plus its verify sub-tasks** into one `tasks` list. Dumps with `explicit_start=True` (`---` header), `sort_keys=False` (preserve field order), `allow_unicode=True`, `width=1000` (no wrapping of long SSH keys), `default_flow_style=False` (block style), then inserts a blank line before `tasks:` |

The `generators/__init__.py` re-exports `generate_yaml`.

---

## 6. `ansify/validators/` — validation

### `ansify/validators/parser.py`
Validates playbook **structure** locally (no Ansible needed).

| Function | What it does |
|---|---|
| `parse_playbook(path)` | Reads the file, `yaml.safe_load`s it, and returns `(playbook_or_None, errors)`. Handles: missing file, YAML syntax errors, empty files, non-playbook documents. Accepts both the list-of-plays form and Ansible's single-play-mapping form (normalizes `dict → [dict]`). Per play: checks `hosts` and `tasks` presence with 1-based "Play N" line numbers |
| `_validate_plays(data)` | The structural checks listed above |
| `load_playbook(path)` | Reverse operation: parses a generated file back into a `Playbook` object (name, hosts, become, tasks) — used by tests and useful for round-trip checks |
| `_task_from_dict(data)` | Picks the module key by excluding Ansible keywords (`name`, `register`, `when`, `loop`, `tags`); falls back to `ansible.builtin.debug` so it never raises |

### `ansify/validators/syntax.py`
Wraps `ansible-playbook --syntax-check` (subprocess → Ansible, requires Linux/WSL).

| Function | What it does |
|---|---|
| `syntax_check(path)` | Runs `ansible-playbook --syntax-check <path>` with a 60s timeout, capturing stdout+stderr. Returns `(ok: bool, messages: list[str])` |
| `_strip_ansi(text)` | Strips ANSI escape codes with a regex → clean, readable error lines |
| error extraction | Keeps only `ERROR` / `[WARNING]` lines so Ansible's noise is filtered to what matters |
| graceful failure | `FileNotFoundError` → friendly "ansible-playbook not found. Install Ansible (Linux/WSL only)." instead of a crash |

`validators/__init__.py` exposes both submodules.

---

## 7. `ansify/commands/` — CLI behavior

### `ansify/commands/create.py` — the wizard (largest file)
Everything the user sees when running `ansify` / `ansify create`.

| Function | What it does |
|---|---|
| `create()` | Main wizard: name → hosts → become → **task loop** → save. Each step calls a small helper |
| `menu()` | The interactive hub (`ansify` with no args): Create / Check / Vault / Quit, looping until Quit |
| `_save(playbook)` | Asks filename (default = playbook name slugged to `snake_case.yml`), prints the **YAML preview** in a Rich panel, asks to save, then offers Check |
| `_manage_tasks()` | Routes edit/delete/reorder actions |
| `_edit_task()` | Re-collects a chosen task's fields via `_collect_task(module, defaults)` and replaces it |
| `_delete_task()` / `_reorder_task()` | Thin wrappers over `Playbook.remove_task` / `move_task` |
| `_pick_task()` / `_list_tasks()` | Shows the task list with numbers and returns the picked index |
| `_pick_module()` | Two-level menu: category → module, walking `CATEGORIES` |
| `_collect_task(module, defaults)` | **The generic engine**: loops over `module.fields`, skipping fields whose `condition`/`if_module` doesn't match, converts `bool` fields to Python booleans and `int` fields to integers, handles the `__module__` field (command vs shell), builds the `Task`, suggests a name from `task_name.format(**values)`, asks for an optional **register** variable (Enter = skip), then optionally calls `apply_verification` |
| `_suggest_name()` | Formats the module's `task_name` template with collected values; falls back to the module label if a placeholder is missing |
| `_ask_field()` | One prompt per field kind: choice → numbered menu, bool → yes/no confirm, int → integer validation loop, multiline → lines until an empty line, text/optional → plain prompt with required-loop |
| `_ask_text` / `_ask_bool` / `_ask_multiline` / `_menu` / `_menu_multi` | Low-level I/O helpers over `typer.prompt`/`typer.confirm` with Rich-printed menus and error messages; `_menu_multi` accepts several numbers (e.g. `1,3`) and returns the matching options |
| `_ask_hosts()` | Optionally reads an inventory file via `inventory_reader` to offer group names plus an always-present `all` option; multi-select (`1,3`) — choosing `all` wins, multiple groups are joined with commas (`web,db`); falls back to manual entry (default `all`) |
| `_check_flow` / `_vault_flow` | Hub sub-menus that delegate to the other commands (lazy imports avoid circular imports). `_check_flow` scans the current directory for `*.yml`/`*.yaml` files and offers them as a menu (with a "Enter path manually" fallback); if none are found it says so and returns |

### `ansify/commands/check.py`
| Function | What it does |
|---|---|
| `check(path)` | Runs `parser.parse_playbook` — if structural errors: red Rich table + exit 1. If OK: green "YAML OK", then `syntax.syntax_check`; shows a Level/Message table (ERROR vs WARNING), red failure + exit 1, or green "Playbook is valid." |

### `ansify/commands/vault.py`
| Function | What it does |
|---|---|
| `app = typer.Typer(...)` | Nested sub-app (`ansify vault`) |
| `encrypt(path)` | Runs `ansible-vault encrypt <path>` |
| `decrypt(path)` | Runs `ansible-vault decrypt <path>` |
| `view(path)` | Runs `ansible-vault view <path>` (asks password, prints content) |
| `_vault(args)` | Shared subprocess wrapper: builds the command, handles `FileNotFoundError` gracefully, propagates non-zero exit codes |

`commands/__init__.py` re-exports the four command modules.

---

## 8. `ansify/utils/` — helpers

### `ansify/utils/inventory_reader.py`
| Function | What it does |
|---|---|
| `read_inventory(path)` | Parses INI-style inventory files: lines like `[webservers]` or `[webservers:children]` → returns the group names (skips `all`). Returns `[]` on any read error so the wizard can fall back to manual input |

### `ansify/utils/yaml_writer.py`
| Function | What it does |
|---|---|
| `ensure_yaml_extension(name)` | Appends `.yml` unless the name already ends in `.yml`/`.yaml` |
| `write_playbook(path, content, overwrite=True)` | Creates parent directories, writes the YAML text (UTF-8), returns the resolved `Path`; refuses to overwrite when `overwrite=False` |

### `ansify/utils/verification.py` — the differentiator feature
Turns a module's `VerifyStep` definitions into real verification tasks.

| Function | What it does |
|---|---|
| `apply_verification(task, steps)` | For each step: if `step.register` is set, assigns it to `task.register` — unless the user already registered a variable, which takes precedence and replaces the built-in name inside step params (e.g. `svc_result.state` → `myvar.state`). Formats `{field}` placeholders in params from the **main task's own params** (e.g. `"ansible_facts.packages['{name}']"` → `['httpd']`). Appends each as a `Task` to `task.verify` |
| `_format(value, context)` | `str.format_map` with `KeyError` fallback — never crashes on a missing placeholder |

This is what replaces "ad-hoc verification commands": `package` → `package_facts` + `debug`, `service`/`firewalld` → `register` + `debug`.

### `ansify/templates/README.md`
Placeholder documentation: users drop Jinja2 templates (referenced by `template` module tasks) into this directory. Empty by design.

---

## 9. `tests/` — unit tests (no Ansible needed, run anywhere)

| File | What it verifies |
|---|---|
| `test_registry.py` | Exactly 18 modules; unique keys; every module is a FQCN (2+ dots); every field has key+label; `CATEGORIES` covers all modules; `get_module` lookup; expected categories exist |
| `test_yaml_generator.py` | Round-trip: generated YAML parses back to the same structure; `yes`/`on`/`0644` values are quoted; multiline content becomes `|-` block scalar; `register` lands at task level (not inside module params); verify sub-tasks serialize after the main task |
| `test_parser.py` | Valid playbooks pass; single-play-mapping form accepted; missing `hosts` reported; broken YAML → single friendly error; missing file → "not found"; `load_playbook` round-trip |
| `test_verification.py` | Service verify sets `task.register` and builds the debug task; package verify formats `{name}` placeholder into the real package name; facts+debug ordering |

`tests/__init__.py` marks the directory as a package.

---

## Quick mental map: which file answers which question

| Question | Look at |
|---|---|
| "How does `ansify` start?" | `cli.py` → `__main__.py` |
| "How is a playbook represented?" | `models/playbook.py`, `models/task.py` |
| "How does the wizard know what to ask?" | `modules/base.py` + the 18 `modules/*.py` files |
| "How is YAML produced?" | `generators/yaml_generator.py` |
| "How do tasks get verification steps?" | `utils/verification.py` |
| "How is a file validated?" | `validators/parser.py` (structure), `validators/syntax.py` (ansible) |
| "How are secrets handled?" | `commands/vault.py` |
| "How do I add module #19?" | New `modules/my_module.py` + one line in `modules/__init__.py` |
