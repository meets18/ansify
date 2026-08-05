"""Command/Shell module (ansible.builtin.command / ansible.builtin.shell).

One menu entry; the wizard asks which of the two to use.
"""

from ansify.modules.base import Field, ModuleDef, VerifyStep

_MODULE_KEY = "__module__"  # special field that selects the module itself

MODULE = ModuleDef(
    key="command",
    module="ansible.builtin.command",
    label="Command / Shell",
    category="Commands",
    task_name="Run: {command}",
    needs_become=False,
    fields=[
        Field(_MODULE_KEY, "Type", kind="choice", choices=["command", "shell"], default="command", required=True),
        Field("command", "Command to run", kind="text", required=True, help="e.g. uptime, curl -s http://localhost"),
        Field("chdir", "Working directory", kind="optional"),
        Field("creates", "Skip if this file exists", kind="optional", help="e.g. /etc/example.conf"),
    ],
)
