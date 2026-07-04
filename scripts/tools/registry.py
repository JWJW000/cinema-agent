"""Small tool registry used by the terminal agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass
class Tool:
    name: str
    description: str
    risk: str
    handler: ToolHandler
    parameters: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def requires_confirmation(self, name: str) -> bool:
        return self.get(name).risk in {"write", "shell"}

    def run(self, name: str, arguments: dict[str, Any]) -> Any:
        return self.get(name).handler(arguments)

    def as_openai_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.list()
        ]
