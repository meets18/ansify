"""Authorized key module (ansible.posix.authorized_key)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="authorized_key",
    module="ansible.posix.authorized_key",
    label="Authorized Key",
    category="User Management",
    task_name="Manage SSH key for {user}",
    needs_become=True,
    fields=[
        Field("user", "Username", kind="text", required=True),
        Field("key", "SSH public key (paste, empty line to finish)", kind="multiline", required=True),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
        Field("exclusive", "Remove all other keys", kind="bool", default="no"),
    ],
)
