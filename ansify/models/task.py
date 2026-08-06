"""Internal representation of a single playbook task."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """A task backed by a registered module."""

    module: str  # fully qualified collection name, e.g. ansible.builtin.package
    params: dict = field(default_factory=dict)
    name: str = ""
    verify: list["Task"] = field(default_factory=list)  # verification sub-tasks
    register: Optional[str] = None  # variable storing this task's result

    def to_dict(self) -> dict:
        """Serialize into a playbook task mapping (used by the generator)."""
        task: dict = {"name": self.name, self.module: dict(self.params)}
        if self.register:
            task["register"] = self.register
        return task
