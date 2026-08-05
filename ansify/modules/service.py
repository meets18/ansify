"""Service module (ansible.builtin.service)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="service",
    module="ansible.builtin.service",
    label="Service",
    category="Service Management",
    task_name="Ensure {name} is {state}",
    needs_become=True,
    fields=[
        Field("name", "Service name", kind="text", required=True, help="e.g. httpd, sshd, firewalld"),
        Field("state", "State", kind="choice", choices=["started", "stopped", "restarted", "reloaded"], default="started", required=True),
        Field("enabled", "Enable at boot", kind="bool", default="yes"),
    ],
    verify_prompt="Add verification (register the result and show service state)?",
    verify=[
        VerifyStep(
            "ansible.builtin.debug",
            {"var": "svc_result.state"},
            name="Show service state",
            register="svc_result",
        ),
    ],
)
