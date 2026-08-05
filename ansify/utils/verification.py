"""Build verification tasks from module definitions.

Every module can carry a built-in verification strategy (collect facts and
show results with debug), so users do not rely on ad-hoc commands.
"""

from __future__ import annotations

from ansify.models.task import Task
from ansify.modules import VerifyStep


def apply_verification(task: Task, steps: list[VerifyStep]) -> None:
    """Attach ``steps`` as verification tasks after ``task``.

    - ``{field}`` placeholders in step params are filled from the main task's
      own params (e.g. the chosen package name).
    - A step with ``register`` set causes the main task to store its result
      in that variable.
    """
    context = {**task.params}
    for step in steps:
        if step.register:
            task.register = step.register
        params = {k: _format(v, context) for k, v in step.params.items()}
        task.verify.append(Task(module=step.module, params=params, name=step.name))


def _format(value, context: dict):
    if isinstance(value, str):
        try:
            return value.format_map(context)
        except (KeyError, IndexError):
            return value
    return value
