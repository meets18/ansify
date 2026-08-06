"""Group module (ansible.builtin.group)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="group",
    module="ansible.builtin.group",
    label="Group",
    category="User Management",
    task_name="Create group {name}",
    task_name_absent="Delete group {name}",
    needs_become=True,
    fields=[
        Field("name", "Group name", kind="text", required=True),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
        Field("gid", "GID", kind="int", default=None, help="Optional numeric GID"),
    ],
)
