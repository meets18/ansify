"""SELinux module (ansible.posix.selinux)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="selinux",
    module="ansible.posix.selinux",
    label="SELinux",
    category="Security",
    task_name="Set SELinux to {state}",
    needs_become=True,
    fields=[
        Field("state", "Mode", kind="choice", choices=["enforcing", "permissive", "disabled"], default="enforcing", required=True),
        Field("policy", "Policy", kind="text", default="targeted", help="e.g. targeted, mls"),
    ],
)
