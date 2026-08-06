"""Convert a Playbook object into Ansible-ready YAML.

The playbook is never hand-written as YAML strings; it lives as a Python
object and is serialized here, with custom representers that keep values
Ansible-safe (quoting "yes"/"no"/number-like strings, block scalars for
multiline content, etc.).
"""

from __future__ import annotations

import re

import yaml

from ansify.models.playbook import Playbook

_AMBIGUOUS = {
    "yes", "no", "on", "off", "true", "false", "y", "n",
    "null", "none", "~", "nan", "inf", "-inf", "+inf",
}
_LEADING_DIGIT = re.compile(r"^[-+]?\d")
_LEADING_SYMBOL = re.compile(r"^[{*&!|>\[\]?#@`'\"-]")


class _IndentedEmitter(yaml.emitter.Emitter):
    """Emit block sequences indented under their mapping key."""

    def expect_block_sequence(self) -> None:
        self.increase_indent(flow=False, indentless=False)
        self.state = self.expect_first_block_sequence_item


class AnsibleDumper(
    _IndentedEmitter,
    yaml.serializer.Serializer,
    yaml.representer.SafeRepresenter,
    yaml.resolver.Resolver,
):
    """SafeDumper variant producing course-style playbook formatting."""

    def __init__(
        self,
        stream,
        default_style=None,
        default_flow_style=False,
        canonical=None,
        indent=None,
        width=None,
        allow_unicode=None,
        line_break=None,
        encoding=None,
        explicit_start=None,
        explicit_end=None,
        version=None,
        tags=None,
        sort_keys=True,
    ):
        _IndentedEmitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
        )
        yaml.serializer.Serializer.__init__(
            self,
            encoding=encoding,
            explicit_start=explicit_start,
            explicit_end=explicit_end,
            version=version,
            tags=tags,
        )
        yaml.representer.SafeRepresenter.__init__(
            self,
            default_style=default_style,
            default_flow_style=default_flow_style,
            sort_keys=sort_keys,
        )
        yaml.resolver.Resolver.__init__(self)


def _represent_bool(dumper: yaml.Dumper, data: bool) -> yaml.Node:
    """Render booleans as yes/no instead of true/false."""
    return dumper.represent_scalar(
        "tag:yaml.org,2002:bool", "yes" if data else "no"
    )


def generate_yaml(playbook: Playbook) -> str:
    """Serialize a Playbook into a YAML document string."""
    tasks: list[dict] = []
    for task in playbook.tasks:
        tasks.append(task.to_dict())
        tasks.extend(verify.to_dict() for verify in task.verify)
    document = {
        "name": playbook.name,
        "hosts": playbook.hosts,
        "become": playbook.become,
        "tasks": tasks,
    }
    text = yaml.dump(
        [document],
        Dumper=AnsibleDumper,
        explicit_start=True,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    )
    return text.replace("\n  tasks:\n", "\n\n  tasks:\n", 1)


def _should_quote(value: str) -> bool:
    """Return True when a plain scalar would be misinterpreted by YAML/Ansible."""
    if value.strip() == "":
        return True
    if value.lower() in _AMBIGUOUS:
        return True
    if _LEADING_DIGIT.match(value) and not _is_number(value):
        return True
    if value.startswith("0") and value[1:].isdigit():  # 0644-style perms
        return True
    if _LEADING_SYMBOL.match(value):
        return True
    if value.startswith("- ") or ": " in value or value.endswith(":"):
        return True
    if " #" in value:
        return True
    return False


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.Node:
    style = None
    if "\n" in data:
        style = "|"  # block scalar (chomped with |- when no trailing newline)
    elif _should_quote(data):
        style = "'"
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


AnsibleDumper.add_representer(str, _represent_str)
AnsibleDumper.add_representer(bool, _represent_bool)
