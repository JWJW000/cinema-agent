"""Conversation core for the terminal agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterator

try:
    from .agent_config import AgentModelConfig, safe_config_summary
    from .llm import OpenAICompatibleClient
    from .memory import MemoryManager
    from .tools.cinema_tools import cinema_auto, cinema_plugins, cinema_save, cinema_save_result, cinema_search
    from .tools.quark_tools import quark_status
    from .tools.registry import Tool, ToolRegistry
    from .tools.shell_tools import run_shell_command, shell_intent_is_explicit
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import AgentModelConfig, safe_config_summary
    from llm import OpenAICompatibleClient
    from memory import MemoryManager
    from tools.cinema_tools import cinema_auto, cinema_plugins, cinema_save, cinema_save_result, cinema_search
    from tools.quark_tools import quark_status
    from tools.registry import Tool, ToolRegistry
    from tools.shell_tools import run_shell_command, shell_intent_is_explicit


SYSTEM_PROMPT = """You are JW, a terminal agent.
Use registered tools for concrete actions. Do not claim a command or tool ran unless a tool result is present.
Never reveal full cookies, API keys, or tokens. Shell commands require explicit user intent and confirmation.
For media-library workflows, use neutral wording like content source.
"""

ConfirmCallback = Callable[[str, dict[str, Any]], bool]


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="cinema.search",
            description="Search enabled content sources for a movie or show.",
            risk="read",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=cinema_search,
        )
    )
    registry.register(Tool(name="cinema.plugins", description="List enabled content source plugins.", risk="read", handler=cinema_plugins))
    registry.register(
        Tool(
            name="cinema.save",
            description="Save a Quark share link to the configured Quark folder.",
            risk="write",
            parameters={
                "type": "object",
                "properties": {
                    "share_url": {"type": "string"},
                    "folder": {"type": "string"},
                },
                "required": ["share_url"],
            },
            handler=cinema_save,
        )
    )
    registry.register(
        Tool(
            name="cinema.save_result",
            description="Save a previously searched result by extracting its share URL first.",
            risk="write",
            parameters={
                "type": "object",
                "properties": {
                    "result": {"type": "object"},
                    "folder": {"type": "string"},
                },
                "required": ["result"],
            },
            handler=cinema_save_result,
        )
    )
    registry.register(
        Tool(
            name="cinema.auto",
            description="Search, choose a good Quark result, save it, and organize it.",
            risk="write",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=cinema_auto,
        )
    )
    registry.register(Tool(name="quark.status", description="Check whether Quark cookie auth is configured.", risk="read", handler=quark_status))
    registry.register(
        Tool(
            name="shell.run",
            description="Run an explicit user-requested shell command after confirmation.",
            risk="shell",
            parameters={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
            handler=run_shell_command,
        )
    )
    return registry


class AgentCore:
    def __init__(
        self,
        model_config: AgentModelConfig,
        registry: ToolRegistry,
        config: dict[str, Any] | None = None,
        llm: Any | None = None,
        confirm: ConfirmCallback | None = None,
        memory: MemoryManager | None = None,
    ) -> None:
        self.model_config = model_config
        self.registry = registry
        self.config = config or {}
        self.llm = llm
        self.confirm = confirm or self._default_confirm
        self.memory = memory or self._build_memory(config or {})
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _build_memory(self, config: dict[str, Any]) -> MemoryManager:
        memory_config = config.get("memory", {})
        path = memory_config.get("path", "~/.cinema-manager/memory.json")
        return MemoryManager(preference_path=Path(path).expanduser())

    def handle_input(self, user_text: str) -> str:
        text = user_text.strip()
        if not text:
            return ""
        if text.startswith("/"):
            return self._handle_slash(text)
        if self._is_capability_question(text):
            return self._handle_slash("/help")
        if self._is_saved_location_question(text):
            return self._saved_location_answer()
        if self._is_save_last_result_request(text):
            return self._save_last_result(text)
        if not self.model_config.is_configured:
            return "模型未配置。请设置 OPENAI_API_KEY、OPENAI_MODEL，必要时设置 OPENAI_BASE_URL；本地命令可先用 /help 查看。"

        if self.llm is None:
            self.llm = OpenAICompatibleClient(self.model_config)
        self.messages.append({"role": "user", "content": text})
        self.messages = self.messages[:1] + self.messages[-self.model_config.history_limit :]
        reply = self.llm.chat(self.messages, self.registry.as_openai_tools())
        tool_output = self._run_tool_calls(reply.get("tool_calls", []), text)
        content = reply.get("content", "")
        if tool_output:
            return tool_output
        self.messages.append({"role": "assistant", "content": content})
        return content

    def handle_input_stream(self, user_text: str) -> Iterator[str]:
        text = user_text.strip()
        local_output = self._handle_local_input(text)
        if local_output is not None:
            if local_output:
                yield local_output
            return
        if not self.model_config.is_configured:
            yield "模型未配置。请设置 OPENAI_API_KEY、OPENAI_MODEL，必要时设置 OPENAI_BASE_URL；本地命令可先用 /help 查看。"
            return

        if self.llm is None:
            self.llm = OpenAICompatibleClient(self.model_config)
        if not hasattr(self.llm, "stream_chat"):
            yield self.handle_input(text)
            return

        self.messages.append({"role": "user", "content": text})
        self.messages = self.messages[:1] + self.messages[-self.model_config.history_limit :]

        final_message: dict[str, Any] = {"content": "", "tool_calls": []}
        for event in self.llm.stream_chat(self.messages, self.registry.as_openai_tools()):
            if event.get("type") == "content":
                yield event.get("content", "")
            elif event.get("type") == "done":
                final_message = event.get("message", final_message)

        tool_output = self._run_tool_calls(final_message.get("tool_calls", []), text)
        if tool_output:
            yield tool_output
            return

        content = final_message.get("content", "")
        self.messages.append({"role": "assistant", "content": content})

    def _handle_local_input(self, text: str) -> str | None:
        if not text:
            return ""
        if text.startswith("/"):
            return self._handle_slash(text)
        if self._is_capability_question(text):
            return self._handle_slash("/help")
        if self._is_saved_location_question(text):
            return self._saved_location_answer()
        if self._is_save_last_result_request(text):
            return self._save_last_result(text)
        return None

    def _handle_slash(self, text: str) -> str:
        if text in {"/help", "/h"}:
            return (
                "可用命令:\n"
                "  /help          显示帮助\n"
                "  /config        查看配置摘要\n"
                "  /tools         列出工具\n"
                "  /memory        查看记忆\n"
                "  /remember k=v  记住偏好\n"
                "  /forget        清空会话记忆\n"
                "  /login quark   浏览器辅助登录夸克\n"
                "  /exit          退出\n"
            )
        if text == "/tools":
            return "\n".join(f"{tool.name} [{tool.risk}] - {tool.description}" for tool in self.registry.list())
        if text == "/config":
            return json.dumps(safe_config_summary(self.config), ensure_ascii=False, indent=2)
        if text == "/memory":
            return self.memory.summary()
        if text == "/forget":
            self.memory.session.forget()
            return "已清空会话记忆。偏好记忆不会被清空。"
        if text.startswith("/remember"):
            return self._handle_remember(text)
        if text == "/login quark":
            return "请在终端入口中使用 /login quark；它会隐藏输入并保存 Cookie。"
        return f"未知命令: {text}"

    def _handle_remember(self, text: str) -> str:
        raw = text[len("/remember"):].strip()
        if "=" not in raw:
            return "用法：/remember key=value，例如 /remember quality=4K"
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            return "用法：/remember key=value，例如 /remember quality=4K"
        self.memory.preferences.set(key, value)
        return f"已记住：{key} = {value}"

    def _is_capability_question(self, text: str) -> bool:
        lowered = text.strip().lower()
        return lowered in {
            "你能做什么",
            "你会什么",
            "help",
            "帮助",
            "功能",
            "what can you do",
        }

    def _is_saved_location_question(self, text: str) -> bool:
        normalized = text.replace(" ", "")
        return "保存" in normalized and any(word in normalized for word in ("哪里", "哪儿", "位置", "路径"))

    def _saved_location_answer(self) -> str:
        if not self.memory.session.last_saved_result:
            if self.memory.session.last_search_results:
                return "还没有保存。上次只是搜索到了结果；如果要保存，可以说“保存第一个结果”。"
            return "还没有保存任何内容。你可以先让我搜索，确认结果后再让我保存。"
        saved = self.memory.session.last_saved_result
        path = saved.get("path") or saved.get("folder") or saved.get("save_folder")
        if path:
            return f"上次保存位置：{path}"
        return "已经执行过保存，但工具没有返回明确路径。可以用 /config 查看默认保存目录。"

    def _is_save_last_result_request(self, text: str) -> bool:
        normalized = text.replace(" ", "")
        return "保存" in normalized and any(marker in normalized for marker in ("第一个", "第1个", "1个", "第一条", "第1条"))

    def _save_last_result(self, text: str) -> str:
        if not self.memory.session.last_search_results:
            return "还没有可保存的搜索结果。你可以先让我搜索电影。"
        result = self.memory.session.last_search_results[0]
        arguments = {"result": result}
        if self.registry.requires_confirmation("cinema.save_result") and not self.confirm("cinema.save_result", arguments):
            return "cinema.save_result: 已取消"
        save_result = self.registry.run("cinema.save_result", arguments)
        self.memory.session.remember_save(save_result if isinstance(save_result, dict) else {"result": save_result})
        return self._format_save_result(save_result)

    def _run_tool_calls(self, tool_calls: list[dict[str, Any]], user_text: str) -> str:
        outputs = []
        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            arguments = self._parse_arguments(function.get("arguments", "{}"))
            if name == "shell.run" and not shell_intent_is_explicit(user_text):
                outputs.append("shell.run: 需要你明确要求执行 shell 命令后才可以运行。")
                continue
            if self.registry.requires_confirmation(name) and not self.confirm(name, arguments):
                outputs.append(f"{name}: 已取消")
                continue
            result = self.registry.run(name, arguments)
            outputs.append(self._format_tool_result(name, result))
        return "\n".join(outputs)

    def _format_tool_result(self, name: str, result: Any) -> str:
        if name == "cinema.search" and isinstance(result, dict):
            results = result.get("results", [])
            self.memory.session.remember_search(results if isinstance(results, list) else [])
            return self._format_search_results(self.memory.session.last_search_results)
        if name in {"cinema.save", "cinema.auto"} and isinstance(result, dict):
            self.memory.session.remember_save(result)
            return self._format_save_result(result)
        return f"{name}: {json.dumps(result, ensure_ascii=False, default=str)}"

    def _format_search_results(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "没有找到匹配结果。可以换个片名、演员或年份再试。"
        lines = [f"找到 {len(results)} 个结果："]
        for index, item in enumerate(results[:5], 1):
            title = item.get("title", "未命名")
            source = item.get("source", "unknown")
            site = item.get("site", "")
            score = item.get("score", 0)
            lines.append(f"{index}. {title} [{source}/{site}] 评分 {score}")
        lines.append("如果要保存，可以说“保存第一个结果”。")
        return "\n".join(lines)

    def _format_save_result(self, result: Any) -> str:
        if not isinstance(result, dict):
            return f"保存结果：{json.dumps(result, ensure_ascii=False, default=str)}"
        if result.get("error"):
            return f"保存失败：{result.get('error')}"
        path = result.get("path") or result.get("folder") or result.get("save_folder")
        if path:
            return f"已保存。位置：{path}"
        return f"保存结果：{json.dumps(result, ensure_ascii=False, default=str)}"

    def _parse_arguments(self, raw: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(raw or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _default_confirm(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        print(f"将执行工具: {tool_name}")
        print(json.dumps(arguments, ensure_ascii=False, indent=2))
        return input("是否继续？[y/N] ").strip().lower() == "y"
