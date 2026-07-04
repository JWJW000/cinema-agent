"""Session and preference memory stores for JW agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_MEMORY_PATH = Path.home() / ".cinema-manager" / "memory.json"


class SessionMemory:
    """Short-lived memory for the current terminal session."""

    def __init__(self) -> None:
        self.last_search_results: list[dict[str, Any]] = []
        self.last_saved_result: dict[str, Any] | None = None

    def remember_search(self, results: list[dict[str, Any]]) -> None:
        self.last_search_results = results

    def remember_save(self, result: dict[str, Any]) -> None:
        self.last_saved_result = result

    def forget(self) -> None:
        self.last_search_results = []
        self.last_saved_result = None


class PersistentPreferenceMemory:
    """Small JSON-backed store for durable user preferences."""

    def __init__(self, path: Path = DEFAULT_MEMORY_PATH) -> None:
        self.path = Path(path).expanduser()
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"preferences": {}}
        try:
            with self.path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {"preferences": {}}
        if not isinstance(data, dict):
            return {"preferences": {}}
        preferences = data.get("preferences")
        if not isinstance(preferences, dict):
            data["preferences"] = {}
        return data

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def get(self, key: str, default: str | None = None) -> str | None:
        value = self._data.get("preferences", {}).get(key, default)
        return str(value) if value is not None else None

    def set(self, key: str, value: str) -> None:
        key = key.strip()
        if not key:
            raise ValueError("Preference key cannot be empty")
        self._data.setdefault("preferences", {})[key] = value.strip()
        self._save()

    def summary(self) -> dict[str, str]:
        return {str(k): str(v) for k, v in self._data.get("preferences", {}).items()}


class MemoryManager:
    """Facade combining session memory and persistent preferences."""

    def __init__(
        self,
        session: SessionMemory | None = None,
        preferences: PersistentPreferenceMemory | None = None,
        preference_path: Path = DEFAULT_MEMORY_PATH,
    ) -> None:
        self.session = session or SessionMemory()
        self.preferences = preferences or PersistentPreferenceMemory(preference_path)

    def summary(self) -> str:
        lines = []
        search_count = len(self.session.last_search_results)
        lines.append(f"最近搜索结果：{search_count} 个")
        if self.session.last_saved_result:
            path = (
                self.session.last_saved_result.get("path")
                or self.session.last_saved_result.get("folder")
                or self.session.last_saved_result.get("save_folder")
                or "未知位置"
            )
            lines.append(f"最近保存位置：{path}")
        else:
            lines.append("最近保存位置：无")

        preferences = self.preferences.summary()
        if preferences:
            lines.append("偏好记忆：")
            for key, value in sorted(preferences.items()):
                lines.append(f"- {key} = {value}")
        else:
            lines.append("偏好记忆：无")
        return "\n".join(lines)
