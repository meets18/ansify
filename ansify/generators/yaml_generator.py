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


class AnsibleDumper(yaml.SafeDumper):
    """SafeDumper that quotes strings Ansible would mis-parse."""


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
    return yaml.dump(
        document,
        Dumper=AnsibleDumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    )
