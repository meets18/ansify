"""File module (ansible.builtin.file)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="file",
    module="ansible.builtin.file",
    label="File",
    category="File Management",
    task_name="Ensure {path} is {state}",
    needs_become=True,
    fields=[
        Field("path", "Path", kind="text", required=True, help="e.g. /etc/motd, /srv/www"),
        Field("state", "State", kind="choice", choices=["touch", "directory", "file", "link", "absent"], default="directory", required=True),
        Field("src", "Link target (only for state=link)", kind="optional", condition=("state", "link")),
        Field("mode", "Permissions", kind="optional", help="e.g. 0644, u=rw,g=r,o=r"),
        Field("owner", "Owner", kind="optional"),
        Field("group", "Group", kind="optional"),
        Field("recurse", "Recurse into directories", kind="bool", default="no", condition=("state", "directory")),
    ],
)
