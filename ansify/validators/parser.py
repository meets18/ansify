"""YAML parsing/validation with simplified error messages."""

from __future__ import annotations

from typing import Optional

import yaml

from ansify.models.playbook import Playbook
from ansify.models.task import Task


def parse_playbook(path: str) -> tuple[Optional[Playbook], list[str]]:
    """Parse a playbook file into a Playbook object.

    Returns (playbook, errors); errors is a list of human-readable messages.
    """
    errors: list[str] = []
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        return None, [f"File not found: {path}"]
    except yaml.YAMLError as exc:
        return None, [f"YAML error: {exc}"]
    except Exception as exc:  # noqa: BLE001
        return None, [f"Could not read file: {exc}"]

    if data is None:
        return None, ["File is empty"]
    if isinstance(data, dict):
        data = [data]  # Ansible accepts a single play written as a mapping
    elif not isinstance(data, list):
        return None, ["Playbook must be a list of plays (missing leading '-')"]

    errors.extend(_validate_plays(data))
    return None, errors if errors else []


def _validate_plays(data: list) -> list[str]:
    errors: list[str] = []
    for idx, play in enumerate(data, start=1):
        if not isinstance(play, dict):
            errors.append(f"Play {idx}: expected a mapping, got {type(play).__name__}")
            continue
        if "hosts" not in play:
            errors.append(f"Play {idx}: missing required key 'hosts'")
        if "tasks" not in play or not isinstance(play["tasks"], list):
            errors.append(f"Play {idx}: missing or invalid 'tasks' list")
    return errors


def load_playbook(path: str) -> Playbook:
    """Load a generated playbook file back into a Playbook object."""
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    plays = data if isinstance(data, list) else [data]
    play = plays[0]
    return Playbook(
        name=str(play.get("name", "Untitled")),
        hosts=str(play.get("hosts", "all")),
        become=bool(play.get("become", False)),
        tasks=[_task_from_dict(t) for t in play.get("tasks", [])],
    )


def _task_from_dict(data: dict) -> Task:
    module = next(
        (k for k in data if k not in ("name", "register", "when", "loop", "tags")),
        "ansible.builtin.debug",
    )
    return Task(
        name=str(data.get("name", "")),
        module=module,
        params=dict(data.get(module, {})),
        register=data.get("register"),
    )
