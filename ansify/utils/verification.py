"""Build verification tasks from module definitions.

Every module can carry a built-in verification strategy (collect facts and
show results with debug), so users do not rely on ad-hoc commands.
"""

from __future__ import annotations

from typing import Optional

from ansify.models.task import Task
from ansify.modules import VerifyStep


def apply_verification(task: Task, steps: list[VerifyStep]) -> None:
    """Attach ``steps`` as verification tasks after ``task``.

    - ``{field}`` placeholders in step params are filled from the main task's
      own params (e.g. the chosen package name).
    - A step with ``register`` set causes the main task to store its result
      in that variable — unless the user already registered one, in which
      case the built-in variable name is replaced by the user's everywhere.
    """
    context = {**task.params}
    for step in steps:
        if step.register and not task.register:
            task.register = step.register
        params = {
            k: _format(v, context, step.register, task.register)
            for k, v in step.params.items()
        }
        task.verify.append(Task(module=step.module, params=params, name=step.name))


def _format(value, context: dict, step_register: Optional[str], task_register: Optional[str]):
    if isinstance(value, str):
        if (
            step_register
            and task_register
            and task_register != step_register
        ):
            value = value.replace(f"{step_register}.", f"{task_register}.")
        try:
            return value.format_map(context)
        except (KeyError, IndexError):
            return value
    return value
