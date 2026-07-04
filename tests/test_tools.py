import unittest

from scripts.tools.registry import Tool, ToolRegistry
from scripts.tools.shell_tools import is_dangerous_command, shell_intent_is_explicit


class ToolRegistryTests(unittest.TestCase):
    def test_registry_requires_confirmation_for_write_and_shell_tools(self):
        registry = ToolRegistry()
        registry.register(Tool(name="read.demo", description="Read", risk="read", handler=lambda _: {}))
        registry.register(Tool(name="write.demo", description="Write", risk="write", handler=lambda _: {}))
        registry.register(Tool(name="shell.run", description="Shell", risk="shell", handler=lambda _: {}))

        self.assertFalse(registry.requires_confirmation("read.demo"))
        self.assertTrue(registry.requires_confirmation("write.demo"))
        self.assertTrue(registry.requires_confirmation("shell.run"))

    def test_registry_exports_model_tool_schema(self):
        registry = ToolRegistry()
        registry.register(
            Tool(
                name="cinema.search",
                description="Search content sources",
                risk="read",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                handler=lambda _: {},
            )
        )

        schema = registry.as_openai_tools()
        self.assertEqual(schema[0]["type"], "function")
        self.assertEqual(schema[0]["function"]["name"], "cinema.search")
        self.assertEqual(schema[0]["function"]["parameters"]["required"], ["query"])


class ShellToolTests(unittest.TestCase):
    def test_dangerous_shell_commands_are_blocked(self):
        self.assertTrue(is_dangerous_command("rm -rf /"))
        self.assertTrue(is_dangerous_command("sudo reboot"))
        self.assertTrue(is_dangerous_command("mkfs.ext4 /dev/disk1"))
        self.assertFalse(is_dangerous_command("ls -la"))

    def test_shell_intent_must_be_explicit(self):
        self.assertTrue(shell_intent_is_explicit("帮我执行 ls -la"))
        self.assertTrue(shell_intent_is_explicit("run shell command pwd"))
        self.assertFalse(shell_intent_is_explicit("看看当前有哪些文件"))


if __name__ == "__main__":
    unittest.main()
