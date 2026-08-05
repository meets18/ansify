"""Playbook validation: YAML parse + ansible-playbook --syntax-check."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ansify.validators import parser, syntax

console = Console()
err = Console(stderr=True)


def check(path: str) -> None:
    """Validate YAML, then run ``ansible-playbook --syntax-check``."""
    _, yaml_errors = parser.parse_playbook(path)

    if yaml_errors:
        table = Table(title=f"YAML validation: {path}", title_style="bold red")
        table.add_column("Error", style="red")
        for message in yaml_errors:
            table.add_row(message)
        console.print(table)
        raise typer.Exit(code=1)

    console.print(f"[green]YAML OK[/] - {path}")
    ok, messages = syntax.syntax_check(path)
    table = Table(title=f"Syntax check: {path}")
    table.add_column("Level", style="bold")
    table.add_column("Message")
    for message in messages:
        level = "ERROR" if "ERROR" in message.upper() else "WARNING"
        table.add_row(level, message)
    console.print(table)

    if not ok:
        err.print("[red]Syntax check failed.[/]")
        raise typer.Exit(code=1)
    console.print("[green]Playbook is valid.[/]")
