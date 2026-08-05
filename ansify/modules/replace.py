"""Replace module (ansible.builtin.replace)."""

from ansify.modules.base import Field, ModuleDef, VerifyStep

MODULE = ModuleDef(
    key="replace",
    module="ansible.builtin.replace",
    label="Replace",
    category="File Management",
    task_name="Replace pattern in {path}",
    needs_become=True,
    fields=[
        Field("path", "File path", kind="text", required=True),
        Field("regexp", "Regexp to find", kind="text", required=True),
        Field("replace", "Replacement text", kind="text", required=True, help="Backreferences like \\1 supported"),
        Field("backup", "Create a backup", kind="bool", default="no"),
    ],
)
