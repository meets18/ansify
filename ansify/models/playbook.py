"""Internal representation of a playbook."""

from __future__ import annotations

from dataclasses import dataclass, field

from ansify.models.task import Task


@dataclass
class Playbook:
    """In-memory playbook object. Converted to YAML only on generation."""

    name: str
    hosts: str = "all"
    become: bool = False
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to the playbook."""
        self.tasks.append(task)

    def remove_task(self, index: int) -> Task:
        """Remove and return the task at ``index``."""
        return self.tasks.pop(index)

    def move_task(self, index: int, direction: int) -> None:
        """Move the task at ``index`` by ``direction`` (-1 or 1)."""
        target = index + direction
        if 0 <= target < len(self.tasks):
            self.tasks[index], self.tasks[target] = self.tasks[target], self.tasks[index]
