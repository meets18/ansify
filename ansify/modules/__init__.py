"""Module registry.

Every supported module is described by a ModuleDef (see base.py). The create
wizard reads these definitions to ask the right questions, so adding a new
module is mostly adding one definition file.
"""

from __future__ import annotations

from typing import Optional

from ansify.modules.base import Field, ModuleDef, VerifyStep  # noqa: F401  (re-exported)
from ansify.modules import (
    authorized_key,
    command,
    copy,
    cron,
    file,
    firewalld,
    group,
    lineinfile,
    lvm,
    mount,
    package,
    reboot,
    replace,
    selinux,
    service,
    template,
    user,
    wait_for,
)

MODULES: list[ModuleDef] = [
    package.MODULE,
    service.MODULE,
    user.MODULE,
    group.MODULE,
    authorized_key.MODULE,
    file.MODULE,
    copy.MODULE,
    template.MODULE,
    lineinfile.MODULE,
    replace.MODULE,
    selinux.MODULE,
    firewalld.MODULE,
    cron.MODULE,
    mount.MODULE,
    lvm.MODULE,
    reboot.MODULE,
    wait_for.MODULE,
    command.MODULE,
]

CATEGORIES: dict[str, list[ModuleDef]] = {}
for _m in MODULES:
    CATEGORIES.setdefault(_m.category, []).append(_m)


def get_module(key: str) -> Optional[ModuleDef]:
    """Return the module definition for ``key`` or None."""
    for _m in MODULES:
        if _m.key == key:
            return _m
    return None
