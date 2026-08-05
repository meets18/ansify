# Ansify — Workflow

This document explains how Ansify works end to end: the internal architecture,
each CLI workflow step by step, and how data flows through the code.

---

## 1. Architecture at a glance

```
                ┌────────────────────────────────────────────────┐
                │                    USER (terminal)             │
                └───────────────────────┬────────────────────────┘
                                        │  ansify / ansify create / check / run / vault
                                        ▼
                                ┌────────────────┐
                                │  ansify/cli.py │   Typer app, command routing,
                                └───────┬────────┘   --version, interactive hub
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
                ▼                       ▼                       ▼
        ┌───────────────┐      ┌───────────────┐      ┌─────────────────┐
        │  commands/    │      │  commands/    │      │  commands/      │
        │  create.py    │      │  check.py     │      │  run.py         │
        │  (wizard)     │      │  run.py       │      │  vault.py       │
        └───────┬───────┘      │  vault.py     │      └────────┬────────┘
                │              └──────┬────────┘               │
                │                     │                        │
                ▼                     ▼                        ▼
        ┌───────────────┐    ┌────────────────┐       ┌────────────────┐
        │  modules/     │    │  validators/   │       │  subprocess    │
        │  18 defs      │    │  parser.py     │──────▶│  ansible-playbook
        └──────┬────────┘    │  syntax.py     │       │  ansible-vault │
               │             └────────────────┘       └────────────────┘
               ▼                      ▲
        ┌───────────────┐            │  save to disk
        │  models/      │            │
        │  Playbook     │            │
        │  Task         │            │
        └──────┬────────┘            │
               │  generate_yaml()    │
               ▼                     │
        ┌───────────────┐            │
        │ generators/   │────────────┘
        │ yaml_generator│
        └───────────────┘
```

**The golden rule**: the playbook exists as a Python object (`Playbook` +
`Task`) for its entire life inside Ansify. YAML is produced *once*, at the end,
by the generator. Nothing ever writes YAML by string concatenation.

---

## 2. Workflow A — Create a playbook (`ansify create`)

### 2.1 Flowchart

```
Start
 │
 ├─ 1. Playbook name                     ──► _ask_text
 ├─ 2. Inventory file (optional)         ──► _ask_hosts → inventory_reader
 ├─ 3. Hosts (group or "all")
 ├─ 4. Become (sudo)?  yes/no
 │
 ├─ TASK LOOP (repeat until "Generate")
 │    ├─ a. Select category              ──► _pick_module  (walks CATEGORIES)
 │    ├─ b. Select module
 │    ├─ c. Ask each field               ──► _collect_task (walks ModuleDef.fields,
 │    │        (conditions/if_module/       honors condition, if_module,
 │    │         bool/int conversion,         validates input, converts types)
 │    │         __module__ selection)
 │    ├─ d. Suggested task name          ──► task_name.format(**values)
 │    ├─ e. Add verification?            ──► apply_verification → VerifySteps
 │    ├─ f. "Task Added" panel
 │    └─ g. Next? Add / Edit / Delete / Reorder / Generate
 │              └── Playbook.add_task / remove_task / move_task
 │
 ├─ 5. Filename (default: name.yml)     ──► ensure_yaml_extension
 ├─ 6. generate_yaml(playbook)           ──► generators/yaml_generator.py
 ├─ 7. PREVIEW in Rich panel
 ├─ 8. Save?                            ──► write_playbook (utils/yaml_writer.py)
 ├─ 9. Check with --syntax-check?       ──► commands/check.py
 └─ 10. Run now?                        ──► commands/run.py
```

### 2.2 What happens inside each step

**Step 1–4 — Playbook metadata.** The wizard collects `name`, `hosts`, and
`become`. For hosts it optionally reads an inventory file first:
`inventory_reader.read_inventory()` extracts INI group names
(`[webservers]` → `webservers`) and offers them as a menu; if no file is given
or none is found, the user types the group manually (default `all`).

**Step a–b — Module selection.** `_pick_module` shows categories
(Package Management, Service Management, ...) then modules. The menu is built
dynamically from the `CATEGORIES` dict — no hardcoded menus anywhere.

**Step c — Field collection (the generic engine).** `_collect_task` iterates
`module.fields` and, for each field:

1. Skips it if `field.if_module` doesn't match the currently selected module
   (LVM: `lv`/`size` only for `lvol`).
2. Skips it if `field.condition` isn't satisfied (file: `src` only when
   `state=link`; copy: `src` vs `content` based on `source_type`).
3. Prompts per `kind`:
   - `choice` → numbered menu
   - `bool` → yes/no → stored as Python `True/False`
   - `int` → validated whole number → stored as Python `int`
   - `multiline` → read lines until empty line (SSH keys, file content)
   - `text`/`optional` → plain prompt; required fields re-prompt on empty
4. The special `__module__` field (command/shell) switches the module FQCN
   itself and is never emitted as a parameter.

**Step d — Task naming.** The module's `task_name` template is filled from the
collected values: `"Install {name}"` + `{name: httpd}` → **"Install httpd"**.
The user can accept or edit it.

**Step e — Verification (the differentiator).** If the module defines
`verify` steps, the wizard asks "Add verification?". If yes,
`utils/verification.apply_verification()`:

- sets `task.register` when a step declares `register` (service → the main
  task gets `register: svc_result`);
- formats `{field}` placeholders using the task's own params (package → the
  debug var becomes `ansible_facts.packages['httpd']`);
- appends each step as a `Task` into `task.verify`.

At generation time the verify tasks are flattened in right after their main
task, so Ansible runs `package_facts` + `debug` immediately after the install.

**Step f–g — Task management.** The loop offers Add / Edit / Delete / Reorder.
Edit re-runs the same `_collect_task` engine against the module definition;
delete and reorder call `Playbook.remove_task`/`move_task`. Task order is
preserved because `Playbook.tasks` is a list and the generator respects it.

**Step 5–8 — Generation & preview.** The playbook object is serialized by
`generate_yaml()`:

```
Playbook ──► dict {name, hosts, become, tasks: [Task.to_dict() × N]} ──► AnsibleDumper ──► YAML text
```

The custom representer is what keeps the output Ansible-safe:

| Input | Output | Why |
|---|---|---|
| `"yes"` | `'yes'` | unquoted `yes` = boolean in YAML 1.1 |
| `"8080/tcp"` | `'8080/tcp'` | leading digit looks like a number |
| `"0644"` | `'0644'` | leading zero = octal |
| `"*/5"` | `'*/5'` | leading `*` = YAML alias syntax |
| `"<h1>...\nline2"` | `content: \|-` block scalar | preserves newlines safely |
| `True` | `true` | real boolean |

The preview is shown in a Rich panel **before** anything is written, so the
user can abandon at any time without side effects.

**Step 9–10 — Check / Run handoff.** Saving is followed by optional
`check` and `run`, reusing the same code paths as the standalone commands
(lazy imports keep `commands/` free of circular imports).

---

## 3. Workflow B — Check a playbook (`ansify check web.yml`)

```
web.yml ──► parser.parse_playbook ──► structural errors? ──► red table + exit 1
                │                        (file/YAML syntax/hosts/tasks)
                │ OK
                ▼
        green "YAML OK"
                │
                ▼
        syntax.syntax_check ──► subprocess ansible-playbook --syntax-check
        (60s timeout, ANSI stripped)          │
                                              ▼
                               ERROR/WARNING lines → table
                                              │
                    ┌─────────────────────────┴──────────┐
                    │ failed                             │ OK
                    ▼                                    ▼
             red "Syntax check failed."          green "Playbook is valid."
             exit 1
```

Two layers of validation:
1. **Local** (parser.py) — works on any OS, no Ansible needed. Catches broken
   YAML, missing `hosts`, missing `tasks`, empty files.
2. **Ansible** (syntax.py) — the authoritative check. Error lines are filtered
   to `ERROR`/`[WARNING]` and ANSI codes are stripped so output is readable.

---

## 4. Workflow C — Run a playbook (`ansify run web.yml`)

```
run web.yml [-i inventory] [-t tags] [-e var]...
        │
        ▼
build: ansible-playbook web.yml [-i inv] [-t tags] [-e v]
        │
        ▼
subprocess.run (timed with time.monotonic)
        │
        ▼
execution summary table: exit code | elapsed seconds | SUCCESS / FAILED
        │
        └── exit code propagated (non-zero → typer.Exit(code))
```

Ansible's own output streams straight to the terminal, so the user sees full
task progress (`TASK [Install Apache] ... ok/changed/failed`). Ansify adds the
summary table on top. If `ansible-playbook` is missing, the user gets a clear
message instead of a traceback.

---

## 5. Workflow D — Vault (`ansify vault encrypt/decrypt/view secrets.yml`)

```
ansify vault encrypt secrets.yml ──► subprocess ansible-vault encrypt secrets.yml
ansify vault decrypt secrets.yml ──► subprocess ansible-vault decrypt secrets.yml
ansify vault view    secrets.yml ──► subprocess ansible-vault view    secrets.yml
```

All three share `_vault(args)`: build the command → run → propagate exit code,
with a friendly error when `ansible-vault` is not installed. Password prompts
are delegated to Ansible itself (it reads from the terminal), so no secret ever
passes through Ansify.

---

## 6. Workflow E — Interactive hub (`ansify` with no arguments)

```
ansify
 └─ hub menu (loops):
     1 Create a playbook  ──► Workflow A
     2 Check a playbook   ──► ask path → Workflow B
     3 Run a playbook     ──► ask path → Workflow C
     4 Vault              ──► ask action + path → Workflow D
     5 Quit
```

---

## 7. Example generated output (what the wizard produces)

Input via the wizard: package `httpd` with verification, then service
`httpd` started+enabled with verification.

```yaml
name: Webserver Setup
hosts: webservers
become: true
tasks:
- name: Install Apache
  ansible.builtin.package:
    name: httpd
    state: present
- name: Gather package facts
  ansible.builtin.package_facts: {}
- name: Show package version
  ansible.builtin.debug:
    var: ansible_facts.packages['httpd']
- name: Start httpd
  ansible.builtin.service:
    name: httpd
    state: started
    enabled: true
  register: svc_result
- name: Show service state
  ansible.builtin.debug:
    var: svc_result.state
```

Notes:
- Every module uses a **FQCN** — portable across Ansible environments.
- `register` sits at **task level**, a sibling of the module key (Ansible
  keyword, not a module parameter).
- Verification tasks are inserted **immediately after** their main task.
- `package_facts` with no args serializes as `{}` — valid Ansible.

---

## 8. Data flow summary (one paragraph)

A user gesture in the terminal lands in `cli.py`, which routes to a command in
`commands/`. `create.py`'s wizard asks questions by *reading* module
definitions from `modules/` (pure data, zero per-module logic), so every answer
becomes a field in a `Task`, and every `Task` is appended to a `Playbook`
object in `models/`. Verification steps are attached by `utils/verification.py`
from the same module definitions. Only when the user says "Generate" does
`generators/yaml_generator.py` serialize the object tree into YAML via a
custom PyYAML dumper, and `utils/yaml_writer.py` writes it to disk. From that
point on, `check`, `run`, and `vault` are thin, fault-tolerant subprocess
wrappers around Ansible itself — Ansify never reimplements Ansible, it
orchestrates it.

---

## 9. Tests → workflow mapping

| Workflow stage | Covered by |
|---|---|
| Module definitions (all 18, FQCN, unique) | `tests/test_registry.py` |
| Object → YAML (quoting, block scalars, register, verify) | `tests/test_yaml_generator.py` |
| YAML → object + structural validation | `tests/test_parser.py` |
| Verification task building (register + placeholder fill) | `tests/test_verification.py` |
