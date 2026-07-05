"""Storage for Quark auth credentials."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

try:
    from ..agent_config import DEFAULT_CONFIG_PATH, load_json_config, save_json_config
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH, load_json_config, save_json_config


class QuarkAuthStorage:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)

    def save_cookie(self, cookie: str, source: str) -> dict[str, Any]:
        config = load_json_config(self.config_path)
        config.setdefault("quark", {})["cookie"] = cookie
        config["quark"]["auth_source"] = source
        config["quark"]["auth_updated_at"] = int(time.time())
        save_json_config(config, self.config_path)
        return config

    def status(self) -> dict[str, Any]:
        config = load_json_config(self.config_path)
        quark = config.get("quark", {})
        cookie = quark.get("cookie", "") or ""
        return {
            "configured": bool(cookie),
            "cookie_length": len(cookie),
            "source": quark.get("auth_source", "config" if cookie else ""),
            "updated_at": quark.get("auth_updated_at"),
            "valid": "unknown",
        }
