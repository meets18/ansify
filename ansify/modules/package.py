"""Package module (ansible.builtin.package)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="package",
    module="ansible.builtin.package",
    label="Package",
    category="Package Management",
    task_name="Install {name}",
    needs_become=True,
    fields=[
        Field("name", "Package name", kind="text", required=True, help="e.g. httpd, nginx, vim"),
        Field("state", "State", kind="choice", choices=["present", "absent", "latest"], default="present", required=True),
    ],
    verify_prompt="Add verification (collect package facts and show the result)?",
    verify=[
        VerifyStep("ansible.builtin.package_facts", name="Gather package facts"),
        VerifyStep("ansible.builtin.debug", {"var": "ansible_facts.packages['{name}']"}, name="Show package version"),
    ],
)
