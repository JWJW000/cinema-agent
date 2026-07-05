"""Quark-related tools for the terminal agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from ..agent_config import DEFAULT_CONFIG_PATH, update_quark_cookie
    from ..quark_auth import QuarkAuthManager
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH, update_quark_cookie
    from quark_auth import QuarkAuthManager


def quark_status(arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    config_path = Path((arguments or {}).get("config_path", DEFAULT_CONFIG_PATH))
    return QuarkAuthManager(config_path).status()


def save_quark_cookie(arguments: dict[str, Any]) -> dict[str, Any]:
    cookie = arguments.get("cookie", "")
    if not cookie:
        return {"ok": False, "error": "Missing cookie"}
    config_path = Path(arguments.get("config_path", DEFAULT_CONFIG_PATH))
    update_quark_cookie(config_path, cookie)
    return {"ok": True, "cookie_length": len(cookie), "valid": "unknown"}
