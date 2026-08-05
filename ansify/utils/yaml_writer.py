"""Save generated YAML to disk."""

from __future__ import annotations

from pathlib import Path


def ensure_yaml_extension(name: str) -> str:
    """Append ``.yml`` when the name has no YAML extension."""
    return name if name.endswith((".yml", ".yaml")) else f"{name}.yml"


def write_playbook(path: str | Path, content: str, overwrite: bool = True) -> Path:
    """Write playbook content to ``path``. Returns the resolved Path."""
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
