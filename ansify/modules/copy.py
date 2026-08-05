"""Copy module (ansible.builtin.copy)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="copy",
    module="ansible.builtin.copy",
    label="Copy",
    category="File Management",
    task_name="Copy to {dest}",
    needs_become=True,
    fields=[
        Field("source_type", "Source", kind="choice", choices=["local file (src)", "inline content"], default="local file (src)", required=True),
        Field("src", "Local source path", kind="text", required=True, condition=("source_type", "local file (src)")),
        Field("content", "Inline content (empty line to finish)", kind="multiline", condition=("source_type", "inline content")),
        Field("dest", "Destination path", kind="text", required=True, help="e.g. /etc/nginx/nginx.conf"),
        Field("mode", "Permissions", kind="optional", help="e.g. 0644, u=rw,g=r,o=r"),
        Field("owner", "Owner", kind="optional"),
        Field("group", "Group", kind="optional"),
    ],
)
