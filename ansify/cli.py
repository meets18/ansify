"""Ansify CLI entry point."""

import typer
from rich.console import Console

from ansify import __version__
from ansify.commands import check, create, run, vault

app = typer.Typer(
    name="ansify",
    add_completion=False,
    invoke_without_command=True,
    help="Interactive Ansible playbook generation, validation, execution, and Vault.",
)

app.command("create")(create.create)
app.command("check")(check.check)
app.command("run")(run.run)
app.add_typer(vault.app, name="vault")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
) -> None:
    """Entry point; opens the interactive menu when no command is given."""
    if version:
        Console().print(f"ansify {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        create.menu()
