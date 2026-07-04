"""Configuration helpers for the terminal agent."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "config.json"


@dataclass(frozen=True)
class AgentModelConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    history_limit: int = 20
    allow_shell: str = "confirm"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)


def load_json_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json_config(config: dict[str, Any], path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_agent_model_config(config: dict[str, Any]) -> AgentModelConfig:
    agent = config.get("agent", {})
    api_key_env = agent.get("api_key_env", "OPENAI_API_KEY")
    return AgentModelConfig(
        provider=agent.get("provider", "openai_compatible"),
        base_url=os.environ.get("OPENAI_BASE_URL", agent.get("base_url", "https://api.openai.com/v1")),
        model=os.environ.get("OPENAI_MODEL", agent.get("model", "")),
        api_key=os.environ.get(api_key_env, os.environ.get("OPENAI_API_KEY", agent.get("api_key", ""))),
        history_limit=int(agent.get("history_limit", 20)),
        allow_shell=agent.get("allow_shell", "confirm"),
    )


def safe_config_summary(config: dict[str, Any]) -> dict[str, Any]:
    cookie = config.get("quark", {}).get("cookie", "") or ""
    agent = config.get("agent", {})
    return {
        "agent": {
            "provider": agent.get("provider", "openai_compatible"),
            "base_url": agent.get("base_url", "https://api.openai.com/v1"),
            "model": agent.get("model", ""),
            "allow_shell": agent.get("allow_shell", "confirm"),
        },
        "quark": {
            "configured": bool(cookie),
            "cookie_length": len(cookie),
            "valid": "unknown",
        },
        "save_folder": config.get("save_folder", "夸克影视"),
    }


def update_quark_cookie(config_path: Path, cookie: str) -> dict[str, Any]:
    config = load_json_config(config_path)
    config.setdefault("quark", {})["cookie"] = cookie
    save_json_config(config, config_path)
    return config
