"""Mount module (ansible.builtin.mount)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="mount",
    module="ansible.builtin.mount",
    label="Mount",
    category="Storage",
    task_name="Manage mount at {path}",
    needs_become=True,
    fields=[
        Field("path", "Mount point", kind="text", required=True, help="e.g. /mnt/data"),
        Field("src", "Source device or UUID", kind="text", required=True, help="e.g. /dev/sdb1, UUID=..."),
        Field("fstype", "Filesystem type", kind="text", required=True, help="e.g. xfs, ext4, nfs"),
        Field("opts", "Mount options", kind="optional", help="e.g. defaults, ro, noatime"),
        Field("state", "State", kind="choice", choices=["mounted", "present", "unmounted", "absent"], default="mounted", required=True),
        Field("boot", "Add to fstab", kind="bool", default="yes"),
    ],
)
