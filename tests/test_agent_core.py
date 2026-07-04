import unittest
import tempfile
from pathlib import Path

from scripts.agent_core import AgentCore, build_default_registry
from scripts.agent_config import AgentModelConfig
from scripts.tools.registry import Tool, ToolRegistry


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def chat(self, messages, tools):
        self.calls.append((messages, tools))
        return self.reply


class FakeStreamingLLM:
    def __init__(self, events):
        self.events = events
        self.calls = []

    def stream_chat(self, messages, tools):
        self.calls.append((messages, tools))
        yield from self.events


class AgentCoreTests(unittest.TestCase):
    def test_slash_help_does_not_require_model(self):
        core = AgentCore(model_config=AgentModelConfig("", "", "", ""), registry=build_default_registry())

        output = core.handle_input("/help")

        self.assertIn("/login quark", output)
        self.assertIn("/tools", output)

    def test_memory_command_shows_memory_summary(self):
        core = AgentCore(model_config=AgentModelConfig("", "", "", ""), registry=build_default_registry())
        core.memory.session.remember_search([{"title": "苹果"}])

        output = core.handle_input("/memory")

        self.assertIn("最近搜索结果：1 个", output)

    def test_forget_command_clears_session_memory(self):
        core = AgentCore(model_config=AgentModelConfig("", "", "", ""), registry=build_default_registry())
        core.memory.session.remember_search([{"title": "苹果"}])

        output = core.handle_input("/forget")

        self.assertIn("已清空会话记忆", output)
        self.assertEqual(core.memory.session.last_search_results, [])

    def test_remember_command_stores_preference(self):
        core = AgentCore(model_config=AgentModelConfig("", "", "", ""), registry=build_default_registry())

        output = core.handle_input("/remember quality=4K")

        self.assertIn("已记住", output)
        self.assertEqual(core.memory.preferences.get("quality"), "4K")

    def test_memory_path_can_be_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            core = AgentCore(
                model_config=AgentModelConfig("", "", "", ""),
                registry=build_default_registry(),
                config={"memory": {"path": str(memory_path)}},
            )

            core.handle_input("/remember quality=4K")

            self.assertTrue(memory_path.exists())

    def test_default_registry_does_not_expose_cookie_write_tool_to_model(self):
        registry = build_default_registry()

        tool_names = {tool.name for tool in registry.list()}

        self.assertIn("quark.status", tool_names)
        self.assertNotIn("quark.save_cookie", tool_names)

    def test_unconfigured_model_returns_local_mode_message_for_natural_language(self):
        core = AgentCore(model_config=AgentModelConfig("", "", "", ""), registry=build_default_registry())

        output = core.handle_input("帮我搜电影")

        self.assertIn("模型未配置", output)

    def test_capability_question_returns_local_help_without_model(self):
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        core = AgentCore(model_config=config, registry=build_default_registry(), llm=FakeLLM({"content": "should not call"}))

        output = core.handle_input("你能做什么")

        self.assertIn("可用命令", output)
        self.assertIn("/login quark", output)

    def test_model_text_reply_is_returned(self):
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        core = AgentCore(model_config=config, registry=build_default_registry(), llm=FakeLLM({"content": "你好"}))

        output = core.handle_input("你好")

        self.assertEqual(output, "你好")

    def test_model_streaming_text_chunks_are_yielded(self):
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        llm = FakeStreamingLLM(
            [
                {"type": "content", "content": "你"},
                {"type": "content", "content": "好"},
                {"type": "done", "message": {"content": "你好", "tool_calls": []}},
            ]
        )
        core = AgentCore(model_config=config, registry=build_default_registry(), llm=llm)

        chunks = list(core.handle_input_stream("hi"))

        self.assertEqual(chunks, ["你", "好"])
        self.assertEqual(core.messages[-1], {"role": "assistant", "content": "你好"})

    def test_streaming_tool_call_runs_after_done_event(self):
        registry = ToolRegistry()
        registry.register(
            Tool(
                name="cinema.search",
                description="Search",
                risk="read",
                handler=lambda args: {"count": 0, "results": []},
            )
        )
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        llm = FakeStreamingLLM(
            [
                {
                    "type": "done",
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "cinema.search",
                                    "arguments": '{"query":"苹果"}',
                                }
                            }
                        ],
                    },
                }
            ]
        )
        core = AgentCore(model_config=config, registry=registry, llm=llm)

        chunks = list(core.handle_input_stream("找苹果"))

        self.assertEqual(chunks, ["没有找到匹配结果。可以换个片名、演员或年份再试。"])

    def test_search_tool_result_is_formatted_and_remembered(self):
        registry = ToolRegistry()
        registry.register(
            Tool(
                name="cinema.search",
                description="Search",
                risk="read",
                handler=lambda args: {
                    "count": 1,
                    "results": [
                        {
                            "title": "苹果 (2007)",
                            "source": "quark",
                            "site": "wp365",
                            "score": 70,
                            "url": "encrypted",
                        }
                    ],
                },
            )
        )
        fake_llm = FakeLLM(
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "cinema.search",
                            "arguments": '{"query": "范冰冰 苹果"}',
                        }
                    }
                ],
            }
        )
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        core = AgentCore(model_config=config, registry=registry, llm=fake_llm)

        output = core.handle_input("帮我找范冰冰主演的苹果")

        self.assertIn("找到 1 个结果", output)
        self.assertIn("苹果 (2007)", output)
        self.assertNotIn("ResourceResult", output)
        self.assertEqual(core.memory.session.last_search_results[0]["title"], "苹果 (2007)")

    def test_saved_location_question_before_save_does_not_call_model_or_auto(self):
        fake_llm = FakeLLM({"content": "should not call"})
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        core = AgentCore(model_config=config, registry=build_default_registry(), llm=fake_llm)

        output = core.handle_input("刚保存到哪里了")

        self.assertIn("还没有保存", output)
        self.assertEqual(fake_llm.calls, [])

    def test_save_first_result_uses_remembered_search_result_without_model(self):
        registry = ToolRegistry()
        registry.register(
            Tool(
                name="cinema.save_result",
                description="Save remembered result",
                risk="write",
                handler=lambda args: {"status": "ok", "path": "夸克影视/苹果 (2007)", "title": args["result"]["title"]},
            )
        )
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        fake_llm = FakeLLM({"content": "should not call"})
        core = AgentCore(model_config=config, registry=registry, llm=fake_llm, confirm=lambda tool, args: True)
        core.memory.session.remember_search([{"title": "苹果 (2007)", "source": "quark", "site": "wp365", "url": "encrypted"}])

        output = core.handle_input("保存第一个结果")

        self.assertIn("夸克影视/苹果 (2007)", output)
        self.assertEqual(fake_llm.calls, [])

    def test_confirm_callback_blocks_write_tool(self):
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        fake_llm = FakeLLM(
            {
                "content": "",
                "tool_calls": [
                    {
                        "id": "1",
                        "function": {
                            "name": "shell.run",
                            "arguments": '{"command": "ls -la"}',
                        },
                    }
                ],
            }
        )
        core = AgentCore(
            model_config=config,
            registry=build_default_registry(),
            llm=fake_llm,
            confirm=lambda tool, args: False,
        )

        output = core.handle_input("执行 ls -la")

        self.assertIn("已取消", output)

    def test_shell_tool_requires_explicit_user_intent_even_if_model_requests_it(self):
        config = AgentModelConfig("openai_compatible", "https://api.example/v1", "demo", "key")
        fake_llm = FakeLLM(
            {
                "content": "",
                "tool_calls": [
                    {
                        "id": "1",
                        "function": {
                            "name": "shell.run",
                            "arguments": '{"command": "ls -la"}',
                        },
                    }
                ],
            }
        )
        core = AgentCore(
            model_config=config,
            registry=build_default_registry(),
            llm=fake_llm,
            confirm=lambda tool, args: True,
        )

        output = core.handle_input("看看当前有哪些文件")

        self.assertIn("需要你明确要求执行 shell 命令", output)


if __name__ == "__main__":
    unittest.main()
