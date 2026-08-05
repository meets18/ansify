"""Read host groups from an Ansible inventory file."""

from __future__ import annotations

from pathlib import Path


def read_inventory(path: str | Path) -> list[str]:
    """Return group names defined in an inventory file.

    Handles INI-style inventories. Returns an empty list on any failure.
    """
    groups: list[str] = []
    try:
        for raw in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                name = line[1:-1].split(":")[0].strip()
                if name and name != "all":
                    groups.append(name)
    except (OSError, UnicodeDecodeError):
        return []
    return groups
