"""Template module (ansible.builtin.template)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="template",
    module="ansible.builtin.template",
    label="Template",
    category="File Management",
    task_name="Render template to {dest}",
    needs_become=True,
    fields=[
        Field("src", "Template path (Jinja2)", kind="text", required=True, help="e.g. templates/nginx.conf.j2"),
        Field("dest", "Destination path", kind="text", required=True),
        Field("mode", "Permissions", kind="optional", help="e.g. 0644, u=rw,g=r,o=r"),
        Field("owner", "Owner", kind="optional"),
        Field("group", "Group", kind="optional"),
    ],
)
