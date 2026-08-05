"""Reboot module (ansible.builtin.reboot)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="reboot",
    module="ansible.builtin.reboot",
    label="Reboot",
    category="System",
    task_name="Reboot the system",
    needs_become=True,
    fields=[
        Field("pre_reboot_delay", "Delay before reboot (seconds)", kind="int", default=None, help="Optional"),
        Field("reboot_timeout", "Wait for reboot (seconds)", kind="int", default="600", help="Optional"),
        Field("post_reboot_delay", "Delay after reboot (seconds)", kind="int", default=None, help="Optional"),
    ],
)
