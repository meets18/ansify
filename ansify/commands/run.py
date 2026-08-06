"""Playbook execution via ansible-playbook."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()
err = Console(stderr=True)


def run(
    path: str,
    inventory: Optional[str] = typer.Option(None, "--inventory", "-i", help="Inventory file"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Only run tagged tasks"),
    extra_vars: list[str] = typer.Option(None, "--extra-vars", "-e", help="Extra variables (repeatable)"),
) -> None:
    """Execute a playbook and show a pass/fail summary."""
    playbook = Path(path)
    if not playbook.is_file():
        err.print(f"[red]Playbook not found:[/] {playbook}")
        raise typer.Exit(code=1)

    command = ["ansible-playbook", str(playbook)]
    if inventory:
        command += ["--inventory", inventory]
    if tags:
        command += ["--tags", tags]
    if extra_vars:
        for var in extra_vars:
            command += ["--extra-vars", var]

    start = time.monotonic()
    try:
        proc = subprocess.run(command, text=True)
    except FileNotFoundError:
        err.print("[red]ansible-playbook not found. Install Ansible (Linux/WSL only).[/]")
        raise typer.Exit(code=1)
    elapsed = time.monotonic() - start

    summary = Table(title=f"Execution summary: {playbook.name}")
    summary.add_column("Result", style="bold")
    summary.add_column("Detail")
    summary.add_row("Exit code", str(proc.returncode))
    summary.add_row("Elapsed", f"{elapsed:.1f}s")
    if proc.returncode == 0:
        summary.add_row("Status", "[green]SUCCESS[/]")
        console.print(summary)
    else:
        summary.add_row("Status", "[red]FAILED[/]")
        console.print(summary)
        raise typer.Exit(code=proc.returncode)
