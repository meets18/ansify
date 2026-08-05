"""Cron module (ansible.builtin.cron)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="cron",
    module="ansible.builtin.cron",
    label="Cron",
    category="Scheduling",
    task_name="Schedule cron job {name}",
    needs_become=True,
    fields=[
        Field("name", "Cron job name", kind="text", required=True),
        Field("job", "Command to run", kind="text", required=True, help="e.g. /usr/bin/backup.sh"),
        Field("minute", "Minute", kind="text", default="*", help="0-59, */5, ranges"),
        Field("hour", "Hour", kind="text", default="*", help="0-23, */2, ranges"),
        Field("day", "Day of month", kind="text", default="*", help="1-31, */3"),
        Field("month", "Month", kind="text", default="*", help="1-12, jan-dec"),
        Field("weekday", "Weekday", kind="text", default="*", help="0-6, sun-sat"),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
    ],
)
