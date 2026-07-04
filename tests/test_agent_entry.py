import unittest

from scripts.agent import is_login_quark_command, normalize_command


class AgentEntryTests(unittest.TestCase):
    def test_normalize_command_removes_spaces_and_lowercases(self):
        self.assertEqual(normalize_command(" /LOGIN   Quark "), "/loginquark")

    def test_login_quark_command_accepts_common_variants(self):
        for text in ["/login quark", "/loginquark", "/login", "login quark", "登录夸克"]:
            with self.subTest(text=text):
                self.assertTrue(is_login_quark_command(text))

    def test_login_quark_command_rejects_unrelated_text(self):
        self.assertFalse(is_login_quark_command("你能做什么"))


if __name__ == "__main__":
    unittest.main()
