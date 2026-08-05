"""LVM module (community.general.lvg / lvol)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="lvm",
    module="community.general.lvg",
    label="LVM",
    category="Storage",
    task_name="Manage LVM {lv}",
    needs_become=True,
    fields=[
        Field("__module__", "Action", kind="choice", choices=["create volume group (lvg)", "create logical volume (lvol)"], default="create volume group (lvg)", required=True),
        Field("vg", "Volume group name", kind="text", required=True, help="e.g. vg_data"),
        Field("pvs", "Physical devices", kind="optional", if_module="community.general.lvg", help="e.g. /dev/sdb1,/dev/sdc1 (empty for lv tasks)"),
        Field("lv", "Logical volume name", kind="text", required=True, if_module="community.general.lvol", help="e.g. lv_data"),
        Field("size", "Size", kind="text", if_module="community.general.lvol", help="e.g. 10g, 512m"),
        Field("state", "State", kind="choice", choices=["present", "absent"], default="present", required=True),
    ],
)
