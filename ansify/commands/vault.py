"""Vault subcommands wrapping ansible-vault."""

from __future__ import annotations

import subprocess

import typer
from rich.console import Console

app = typer.Typer(name="vault", help="Encrypt, decrypt, and view secrets with ansible-vault.")
console = Console()
err = Console(stderr=True)


@app.command("encrypt")
def encrypt(path: str) -> None:
    """Encrypt a file with ansible-vault."""
    _vault(["encrypt", path])


@app.command("decrypt")
def decrypt(path: str) -> None:
    """Decrypt a file with ansible-vault."""
    _vault(["decrypt", path])


@app.command("view")
def view(path: str) -> None:
    """View an encrypted file's content with ansible-vault."""
    _vault(["view", path])


def _vault(args: list[str]) -> None:
    command = ["ansible-vault", *args]
    try:
        proc = subprocess.run(command, text=True)
    except FileNotFoundError:
        err.print("[red]ansible-vault not found. Install Ansible (Linux/WSL only).[/]")
        raise typer.Exit(code=1)
    if proc.returncode != 0:
        raise typer.Exit(code=proc.returncode)
