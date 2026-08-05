"""Lineinfile module (ansible.builtin.lineinfile)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="lineinfile",
    module="ansible.builtin.lineinfile",
    label="Lineinfile",
    category="File Management",
    task_name="Ensure line in {path}",
    needs_become=True,
    fields=[
        Field("path", "File path", kind="text", required=True),
        Field("regexp", "Regexp to match", kind="text", required=True, help="e.g. ^SELINUX="),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
        Field("line", "Replacement line", kind="optional", help="Required when state=present", condition=("state", "present")),
        Field("backup", "Create a backup", kind="bool", default="no"),
    ],
)
