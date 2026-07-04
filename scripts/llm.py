"""LLM providers for the terminal agent."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Any, Iterator

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - exercised through fallback behavior
    class _HttpxUnavailable:
        Client = None

    httpx = _HttpxUnavailable()

try:
    from .agent_config import AgentModelConfig
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import AgentModelConfig


class OpenAICompatibleClient:
    def __init__(self, config: AgentModelConfig) -> None:
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        }
        self.client = httpx.Client(timeout=60, headers=self.headers) if httpx.Client else None

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        if self.client:
            response = self.client.post(url, json=payload)
            try:
                response.raise_for_status()
            except Exception as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code:
                    raise RuntimeError(
                        f"模型接口请求失败：HTTP {status_code}。请检查 base_url、模型名、API key 或服务权限。"
                    ) from exc
                raise
            data = response.json()
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self.headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                raise RuntimeError(
                    f"模型接口请求失败：HTTP {exc.code} {exc.reason}。请检查 base_url、模型名、API key 或服务权限。"
                ) from exc
            except URLError as exc:
                raise RuntimeError(f"模型接口连接失败：{exc.reason}") from exc
        message = data["choices"][0]["message"]
        return {
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls") or [],
        }

    def stream_chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        content_parts: list[str] = []
        tool_calls: dict[int, dict[str, Any]] = {}

        for data in self._stream_sse(url, payload):
            choice = (data.get("choices") or [{}])[0]
            delta = choice.get("delta", {})
            content = delta.get("content")
            if content:
                content_parts.append(content)
                yield {"type": "content", "content": content}
            for call_delta in delta.get("tool_calls") or []:
                self._merge_tool_call_delta(tool_calls, call_delta)

        yield {
            "type": "done",
            "message": {
                "content": "".join(content_parts),
                "tool_calls": [tool_calls[index] for index in sorted(tool_calls)],
            },
        }

    def _stream_sse(self, url: str, payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
        if self.client:
            try:
                with self.client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        event = self._parse_sse_line(line)
                        if event is not None:
                            yield event
            except Exception as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code:
                    raise RuntimeError(
                        f"模型接口请求失败：HTTP {status_code}。请检查 base_url、模型名、API key 或服务权限。"
                    ) from exc
                raise
            return

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for raw_line in response:
                    event = self._parse_sse_line(raw_line)
                    if event is not None:
                        yield event
        except HTTPError as exc:
            raise RuntimeError(
                f"模型接口请求失败：HTTP {exc.code} {exc.reason}。请检查 base_url、模型名、API key 或服务权限。"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"模型接口连接失败：{exc.reason}") from exc

    def _parse_sse_line(self, raw_line: bytes | str) -> dict[str, Any] | None:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        line = line.strip()
        if not line or not line.startswith("data:"):
            return None
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            return None
        return json.loads(data)

    def _merge_tool_call_delta(self, tool_calls: dict[int, dict[str, Any]], delta: dict[str, Any]) -> None:
        index = int(delta.get("index", 0))
        current = tool_calls.setdefault(index, {"id": "", "function": {"name": "", "arguments": ""}})
        if delta.get("id"):
            current["id"] = delta["id"]
        function_delta = delta.get("function") or {}
        if function_delta.get("name"):
            current["function"]["name"] += function_delta["name"]
        if function_delta.get("arguments"):
            current["function"]["arguments"] += function_delta["arguments"]
