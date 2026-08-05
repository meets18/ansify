"""Firewalld module (ansible.posix.firewalld)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="firewalld",
    module="ansible.posix.firewalld",
    label="Firewalld",
    category="Security",
    task_name="Manage firewall rule",
    needs_become=True,
    fields=[
        Field("target_type", "Rule type", kind="choice", choices=["service", "port"], default="service", required=True),
        Field("service", "Service name", kind="text", required=True, condition=("target_type", "service"), help="e.g. http, https, ssh"),
        Field("port", "Port (with protocol)", kind="text", required=True, condition=("target_type", "port"), help="e.g. 8080/tcp"),
        Field("state", "State", kind="choice", choices=["enabled", "disabled"], default="enabled", required=True),
        Field("permanent", "Permanent (persist across reboot)", kind="bool", default="no"),
        Field("zone", "Zone", kind="optional", help="e.g. public, trusted (default zone if empty)"),
        Field("immediate", "Apply immediately (needed with permanent)", kind="bool", default="yes"),
    ],
    verify_prompt="Add verification (register the result and show it)?",
    verify=[
        VerifyStep(
            "ansible.builtin.debug",
            {"var": "fw_result"},
            name="Show firewall result",
            register="fw_result",
        ),
    ],
)
