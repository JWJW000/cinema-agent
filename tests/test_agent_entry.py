import unittest

from scripts.agent import is_login_quark_command, normalize_command, render_chunk


class AgentEntryTests(unittest.TestCase):
    def test_normalize_command_removes_spaces_and_lowercases(self):
        self.assertEqual(normalize_command(" /LOGIN   Quark "), "/loginquark")

    def test_login_quark_command_accepts_common_variants(self):
        for text in ["/login quark", "/loginquark", "/login", "login quark", "登录夸克"]:
            with self.subTest(text=text):
                self.assertTrue(is_login_quark_command(text))

    def test_login_quark_command_rejects_unrelated_text(self):
        self.assertFalse(is_login_quark_command("你能做什么"))

    def test_render_chunk_smooths_short_model_text(self):
        written = []
        render_chunk("你好", write=written.append, sleep=lambda _: None)

        self.assertEqual(written, ["你", "好"])

    def test_render_chunk_keeps_multiline_tool_output_together(self):
        written = []
        render_chunk("找到 1 个结果：\n1. 苹果", write=written.append, sleep=lambda _: None)

        self.assertEqual(written, ["找到 1 个结果：\n1. 苹果"])


if __name__ == "__main__":
    unittest.main()
