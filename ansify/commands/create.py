"""Interactive playbook creation wizard."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ansify import __version__
from ansify.generators.yaml_generator import generate_yaml
from ansify.models.playbook import Playbook
from ansify.models.task import Task
from ansify.modules import CATEGORIES, ModuleDef, get_module
from ansify.utils import inventory_reader, verification
from ansify.utils.yaml_writer import ensure_yaml_extension, write_playbook

console = Console()
err = Console(stderr=True)


def create() -> None:
    """Walk through the wizard and produce a playbook file."""
    playbook = Playbook(name=_ask_text("Playbook name", default="My Playbook"))
    playbook.hosts = _ask_hosts()
    playbook.become = _ask_bool("Enable become (sudo) for this playbook?", default=True)

    while True:
        module = _pick_module()
        task = _collect_task(module)
        playbook.add_task(task)
        console.print(Panel(f"[green]Added task:[/] {task.name}", title="Task Added"))
        action = _menu(
            "What next?",
            ["Add another task", "Edit a task", "Delete a task", "Reorder tasks", "Generate playbook"],
        )
        if action == 5:
            break
        _manage_tasks(playbook, action)

    _save(playbook)


_BANNER = """    _    _   _ ____ ___ _______   __
   / \\  | \\ | / ___|_ _|  ___\\ \\ / /
  / _ \\ |  \\| \\___ \\| || |_   \\ V /
 / ___ \\| |\\  |___) | ||  _|   | |
/_/   \\_\\_| \\_|____/___|_|     |_|"""


def menu() -> None:
    """Interactive hub shown when running `ansify` with no arguments."""
    console.print(_BANNER, style="bold cyan")
    console.print(f"Ansible playbook tool - v{__version__}\n", style="dim")
    while True:
        choice = _menu(
            "Choose an action",
            ["Create a playbook", "Check a playbook", "Vault", "Quit"],
        )
        if choice == 1:
            create()
        elif choice == 2:
            _check_flow()
        elif choice == 3:
            _vault_flow()
        else:
            break


def _save(playbook: Playbook) -> None:
    from ansify.commands.check import check as check_cmd

    filename = _ask_text(
        "Filename to save", default=ensure_yaml_extension(playbook.name.lower().replace(" ", "_"))
    )
    filename = ensure_yaml_extension(filename)
    yaml_text = generate_yaml(playbook)
    console.print(Panel(yaml_text.rstrip(), title="Preview", border_style="cyan"))
    if not _ask_bool("Save this playbook?", default=True):
        return
    try:
        path = write_playbook(filename, yaml_text)
    except FileExistsError as exc:
        err.print(f"[red]Error:[/] {exc}")
        return
    console.print(f"[green]Saved to {path}[/]")
    if _ask_bool("Check it with ansible-playbook --syntax-check?", default=True):
        check_cmd(str(path))


def _check_flow() -> None:
    from ansify.commands.check import check as check_cmd

    candidates = sorted(Path.cwd().glob("*.yml")) + sorted(Path.cwd().glob("*.yaml"))
    if not candidates:
        err.print("[red]No playbooks (.yml/.yaml) found in the current directory.[/]")
        return
    names = [p.name for p in candidates]
    pick = _menu("Select a playbook to check", [*names, "Enter path manually"])
    if pick <= len(names):
        check_cmd(str(candidates[pick - 1]))
    else:
        check_cmd(_ask_text("Playbook path"))


def _vault_flow() -> None:
    from ansify.commands import vault

    action = _menu("Vault action", ["Encrypt", "Decrypt", "View"])
    path = _ask_text("File path")
    if action == 1:
        vault.encrypt(path)
    elif action == 2:
        vault.decrypt(path)
    else:
        vault.view(path)


def _manage_tasks(playbook: Playbook, action: int) -> None:
    if action == 2:
        _edit_task(playbook)
    elif action == 3:
        _delete_task(playbook)
    elif action == 4:
        _reorder_task(playbook)


def _edit_task(playbook: Playbook) -> None:
    idx = _pick_task(playbook, "Edit which task?")
    if idx is None:
        return
    task = playbook.tasks[idx]
    module = get_module(task.module)
    if module:
        replacement = _collect_task(module, defaults=task.params)
        playbook.tasks[idx] = replacement


def _delete_task(playbook: Playbook) -> None:
    idx = _pick_task(playbook, "Delete which task?")
    if idx is not None:
        removed = playbook.remove_task(idx)
        console.print(f"[yellow]Deleted:[/] {removed.name}")


def _reorder_task(playbook: Playbook) -> None:
    idx = _pick_task(playbook, "Move which task?")
    if idx is None:
        return
    direction = _menu("Move where?", ["Up", "Down"])
    playbook.move_task(idx, -1 if direction == 1 else 1)
    _list_tasks(playbook)


def _pick_task(playbook: Playbook, prompt: str) -> Optional[int]:
    if not playbook.tasks:
        console.print("[yellow]No tasks yet.[/]")
        return None
    _list_tasks(playbook)
    return _menu(prompt, [t.name for t in playbook.tasks]) - 1


def _list_tasks(playbook: Playbook) -> None:
    for i, task in enumerate(playbook.tasks, start=1):
        console.print(f"  {i}. {task.name}")


def _pick_module() -> ModuleDef:
    while True:
        categories = list(CATEGORIES)
        cat = _menu("Select a category", categories)
        modules = CATEGORIES[categories[cat - 1]]
        pick = _menu("Select a module", [m.label for m in modules])
        return modules[pick - 1]


def _collect_task(module: ModuleDef, defaults: Optional[dict] = None) -> Task:
    defaults = defaults or {}
    values: dict = {}
    effective_module = module.module
    for field in module.fields:
        if field.if_module and field.if_module != effective_module:
            continue
        if field.condition and values.get(field.condition[0]) != field.condition[1]:
            continue
        value = _ask_field(field)
        if field.key == "__module__":
            effective_module = (
                "ansible.builtin.shell"
                if value == "shell"
                else "ansible.builtin.command"
            )
            continue
        if field.kind == "bool":
            values[field.key] = value == "yes"
            continue
        if field.kind == "int":
            if value is not None:
                values[field.key] = int(value)
            continue
        if value is not None and value != "":
            values[field.key] = value
    name = _suggest_name(module, values)
    name = _ask_text("Task name", default=name) or name
    task = Task(name=name, module=effective_module, params=values)
    if _ask_bool("Register this task's output?", default=False):
        while True:
            registered = _ask_text("Variable name", default="")
            if registered:
                task.register = registered
                break
            err.print("[red]Variable name cannot be empty.[/]")
    if module.verify and _ask_bool(module.verify_prompt or "Add verification steps?", default=True):
        verification.apply_verification(task, module.verify)
    return task


def _suggest_name(module: ModuleDef, values: dict) -> str:
    template = (
        module.task_name_absent
        if values.get("state") == "absent" and module.task_name_absent
        else module.task_name
    )
    if not template:
        return module.label
    try:
        return template.format(**values)
    except (KeyError, IndexError):
        return module.label


def _ask_field(field) -> Optional[str]:
    label = f"{field.label}" + (" [required]" if field.required else "")
    while True:
        if field.kind == "choice":
            value = field.choices[_menu(label, field.choices) - 1]
        elif field.kind == "bool":
            value = "yes" if _ask_bool(label, default=(field.default == "yes")) else "no"
        elif field.kind == "int":
            raw = typer.prompt(label, default=field.default or "")
            if raw == "":
                return None
            try:
                return str(int(raw))
            except ValueError:
                err.print("[red]Please enter a whole number.[/]")
                continue
        elif field.kind == "multiline":
            value = _ask_multiline(label)
        else:
            value = typer.prompt(label, default=field.default or "")
        if value or not field.required:
            return value
        err.print("[red]This field is required.[/]")


def _ask_text(label: str, default: Optional[str] = None) -> str:
    return typer.prompt(label, default=default or "").strip()


def _ask_bool(label: str, default: bool = True) -> bool:
    return typer.confirm(label, default=default)


def _ask_multiline(label: str) -> str:
    console.print(f"{label} (press Enter on an empty line to finish):")
    lines: list[str] = []
    while True:
        line = typer.prompt("", prompt_suffix="") or ""
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def _ask_hosts() -> str:
    inventory = _ask_text(
        "Path to inventory file (optional, to list groups)", default=""
    )
    if inventory:
        groups = inventory_reader.read_inventory(inventory)
        if groups:
            picked = _menu_multi(
                "Select host groups (multiple allowed, e.g. 1,3)",
                ["all", *groups],
            )
            if "all" in picked:
                return "all"
            return ",".join(picked)
    return _ask_text("Hosts", default="all")


def _menu_multi(prompt: str, options: list[str]) -> list[str]:
    """Numbered menu allowing several selections (e.g. '1,3')."""
    console.print(f"\n[bold cyan]{prompt}[/]")
    for i, option in enumerate(options, start=1):
        console.print(f"  [bold]{i}[/] {option}")
    while True:
        raw = typer.prompt("", prompt_suffix="> ") or ""
        try:
            picks = {int(part) for part in raw.replace(",", " ").split()}
        except ValueError:
            picks = set()
        if picks and all(1 <= p <= len(options) for p in picks):
            return [options[p - 1] for p in sorted(picks)]
        err.print(f"[red]Enter numbers between 1 and {len(options)} (e.g. 1,3).[/]")


def _menu(prompt: str, options: list[str]) -> int:
    console.print(f"\n[bold cyan]{prompt}[/]")
    for i, option in enumerate(options, start=1):
        console.print(f"  [bold]{i}[/] {option}")
    while True:
        raw = typer.prompt("", prompt_suffix="> ")
        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        err.print(f"[red]Choose a number between 1 and {len(options)}.[/]")
