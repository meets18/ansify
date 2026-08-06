"""Shared module definition dataclasses (no imports from ansify.modules)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Field:
    """A single promptable field of a module."""

    key: str
    label: str
    kind: str = "text"  # text | choice | bool | int | multiline | optional
    choices: list[str] = field(default_factory=list)
    default: Optional[str] = None
    required: bool = False
    help: Optional[str] = None
    # Only ask when an earlier field (key) equals value; e.g. state == "present"
    condition: Optional[tuple[str, str]] = None
    # Only ask when the selected module equals value (used by choice modules)
    if_module: Optional[str] = None
    validate: Optional[Callable[[str], bool]] = None


@dataclass
class VerifyStep:
    """A verification task appended after the main task.

    ``register`` names the variable the *main* task must store its result in;
    params may reference that variable (e.g. ``{"var": "svc_result.state"}``).
    """

    module: str
    params: dict = field(default_factory=dict)
    name: str = ""
    register: Optional[str] = None


@dataclass
class ModuleDef:
    """Configuration object that drives the wizard for one module."""

    key: str  # unique registry key, e.g. "package"
    module: str  # FQCN, e.g. ansible.builtin.package
    label: str  # display name in menus
    category: str
    fields: list[Field] = field(default_factory=list)
    verify: list[VerifyStep] = field(default_factory=list)
    verify_prompt: Optional[str] = None  # question shown before adding verification
    needs_become: bool = True
    task_name: str = ""  # template with {field} placeholders for the task name
    task_name_absent: Optional[str] = None  # used instead when state == "absent"
