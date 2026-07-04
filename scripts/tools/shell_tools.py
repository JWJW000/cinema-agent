"""Confirmed shell execution helpers."""

from __future__ import annotations

import re
import subprocess
from typing import Any


DANGEROUS_PATTERNS = [
    r"\brm\s+-[^\n]*r[^\n]*f\s+/",
    r"^\s*sudo\b",
    r"\bmkfs(?:\.\w+)?\b",
    r"\bdiskutil\s+erase",
    r"\bdd\s+.*\bof=/dev/",
    r">\s*/(?:etc|bin|sbin|usr|System|Library)\b",
]

EXPLICIT_SHELL_WORDS = ["执行", "运行", "命令", "shell", "terminal", "run command", "运行一下"]


def is_dangerous_command(command: str) -> bool:
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)


def shell_intent_is_explicit(user_text: str) -> bool:
    text = user_text.lower()
    return any(word in text for word in EXPLICIT_SHELL_WORDS)


def run_shell_command(arguments: dict[str, Any]) -> dict[str, Any]:
    command = arguments.get("command", "")
    if not command:
        return {"ok": False, "error": "Missing command"}
    if is_dangerous_command(command):
        return {"ok": False, "error": "Command blocked by safety policy"}

    completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }
