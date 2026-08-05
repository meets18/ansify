"""Wait_for module (ansible.builtin.wait_for)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="wait_for",
    module="ansible.builtin.wait_for",
    label="Wait For",
    category="System",
    task_name="Wait for {host}:{port}",
    needs_become=False,
    fields=[
        Field("host", "Host", kind="text", default="127.0.0.1", help="Empty to use current host"),
        Field("port", "Port", kind="int", required=True),
        Field("state", "State", kind="choice", choices=["started", "stopped"], default="started", required=True),
        Field("delay", "Delay before checking (seconds)", kind="int", default=None, help="Optional"),
        Field("timeout", "Timeout (seconds)", kind="int", default="300", help="Optional"),
    ],
)
