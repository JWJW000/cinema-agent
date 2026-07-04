import tempfile
import unittest
from http.cookiejar import Cookie
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.quark_login import (
    browser_cookie_string,
    cookie_looks_like_quark,
    login_quark_with_browser,
)


def make_cookie(name, value, domain=".pan.quark.cn"):
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=domain.startswith("."),
        path="/",
        path_specified=True,
        secure=True,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


class QuarkLoginTests(unittest.TestCase):
    def test_browser_cookie_string_collects_quark_cookies(self):
        cookies = [make_cookie("__puus", "abc"), make_cookie("other", "def", ".example.com")]

        result = browser_cookie_string(cookies)

        self.assertEqual(result, "__puus=abc")

    def test_cookie_looks_like_quark_requires_known_cookie_name(self):
        self.assertTrue(cookie_looks_like_quark("__puus=abc; kps=def"))
        self.assertFalse(cookie_looks_like_quark("session=abc"))

    def test_login_quark_with_browser_saves_cookie_from_browser_without_prompting_manual(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            input_fn = Mock()
            hidden_input = Mock()

            result = login_quark_with_browser(
                config_path=config_path,
                open_url=lambda url: True,
                input_fn=input_fn,
                hidden_input=hidden_input,
                cookie_loader=lambda: [make_cookie("__puus", "abc")],
                output=lambda message: None,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "browser")
            self.assertIn("__puus=abc", config_path.read_text(encoding="utf-8"))
            hidden_input.assert_not_called()

    def test_login_quark_with_browser_falls_back_to_hidden_manual_cookie(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"

            result = login_quark_with_browser(
                config_path=config_path,
                open_url=lambda url: True,
                input_fn=lambda prompt="": "",
                hidden_input=lambda prompt="": "__puus=manual",
                clipboard_loader=lambda: "",
                cookie_loader=lambda: [],
                output=lambda message: None,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "manual")
            self.assertIn("__puus=manual", config_path.read_text(encoding="utf-8"))

    def test_login_quark_with_browser_uses_clipboard_before_manual_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            hidden_input = Mock()

            result = login_quark_with_browser(
                config_path=config_path,
                open_url=lambda url: True,
                input_fn=lambda prompt="": "",
                hidden_input=hidden_input,
                visible_input=lambda prompt="": "",
                clipboard_loader=lambda: "__puus=clipboard",
                cookie_loader=lambda: [],
                output=lambda message: None,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "clipboard")
            self.assertIn("__puus=clipboard", config_path.read_text(encoding="utf-8"))
            hidden_input.assert_not_called()

    def test_login_quark_with_browser_falls_back_to_visible_paste_when_hidden_input_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"

            result = login_quark_with_browser(
                config_path=config_path,
                open_url=lambda url: True,
                input_fn=lambda prompt="": "",
                hidden_input=lambda prompt="": "",
                visible_input=lambda prompt="": "__puus=visible",
                clipboard_loader=lambda: "",
                cookie_loader=lambda: [],
                output=lambda message: None,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "visible")
            self.assertIn("__puus=visible", config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
