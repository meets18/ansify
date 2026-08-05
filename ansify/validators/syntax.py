"""ansible-playbook --syntax-check wrapper with simplified output."""

from __future__ import annotations

import re
import subprocess

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
_ERROR_RE = re.compile(r"^(?:ERROR|\[ERROR\])", re.IGNORECASE)
_WARNING_RE = re.compile(r"\[WARNING\]")


def syntax_check(path: str) -> tuple[bool, list[str]]:
    """Run ``ansible-playbook --syntax-check`` on ``path``.

    Returns (ok, messages) where messages are simplified, ANSI-free lines.
    """
    try:
        proc = subprocess.run(
            ["ansible-playbook", "--syntax-check", str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return False, ["ansible-playbook not found. Install Ansible (Linux/WSL only)."]
    except subprocess.TimeoutExpired:
        return False, ["Syntax check timed out."]

    combined = _strip_ansi(proc.stdout) + "\n" + _strip_ansi(proc.stderr)
    messages: list[str] = []
    for line in combined.splitlines():
        line = line.strip()
        if not line:
            continue
        if _ERROR_RE.match(line) or _WARNING_RE.match(line):
            messages.append(line)
    return proc.returncode == 0, messages


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)
