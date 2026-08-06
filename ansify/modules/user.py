"""User module (ansible.builtin.user)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="user",
    module="ansible.builtin.user",
    label="User",
    category="User Management",
    task_name="Create user {name}",
    task_name_absent="Delete user {name}",
    needs_become=True,
    fields=[
        Field("name", "Username", kind="text", required=True),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
        Field("groups", "Groups (comma-separated)", kind="optional", help="e.g. wheel, developers"),
        Field("shell", "Shell", kind="text", default="/bin/bash", help="e.g. /bin/bash, /sbin/nologin"),
        Field("uid", "UID", kind="int", default=None, help="Optional numeric UID"),
        Field("create_home", "Create home directory", kind="bool", default="yes"),
    ],
)
