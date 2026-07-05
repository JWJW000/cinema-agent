import json
import tempfile
import unittest
from pathlib import Path

from scripts.quark_auth.manager import QuarkAuthManager
from scripts.agent_config import update_quark_cookie
from scripts.quark_auth.providers import AuthResult, BrowserCookieFallbackProvider, QuarkpanQrProvider
from scripts.quark_auth.storage import QuarkAuthStorage


class QuarkAuthStorageTests(unittest.TestCase):
    def test_save_cookie_updates_config_and_redacts_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            storage = QuarkAuthStorage(config_path)

            storage.save_cookie("__puus=secret-cookie", source="qr")

            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["quark"]["cookie"], "__puus=secret-cookie")
            status = storage.status()
            self.assertTrue(status["configured"])
            self.assertEqual(status["source"], "qr")
            self.assertEqual(status["cookie_length"], len("__puus=secret-cookie"))
            self.assertNotIn("secret-cookie", json.dumps(status, ensure_ascii=False))


class QuarkpanQrProviderTests(unittest.TestCase):
    def test_login_returns_cookie_from_injected_api_login(self):
        calls = []

        class FakeApiLogin:
            def __init__(self, timeout):
                calls.append(timeout)

            def login(self):
                return "__puus=qr-cookie"

        provider = QuarkpanQrProvider(api_login_cls=FakeApiLogin, timeout=12)

        result = provider.login(output=lambda message: None)

        self.assertTrue(result.ok)
        self.assertEqual(result.source, "qr")
        self.assertEqual(result.cookie, "__puus=qr-cookie")
        self.assertEqual(calls, [12])

    def test_login_reports_unavailable_when_dependency_missing(self):
        provider = QuarkpanQrProvider(api_login_cls=None)

        result = provider.login(output=lambda message: None)

        self.assertFalse(result.ok)
        self.assertEqual(result.source, "qr")
        self.assertIn("quarkpan", result.error)


class BrowserCookieFallbackProviderTests(unittest.TestCase):
    def test_login_returns_cookie_saved_by_legacy_login_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"

            def legacy_login(config_path, output):
                update_quark_cookie(config_path, "__puus=legacy")
                return {"ok": True, "source": "browser", "cookie_length": len("__puus=legacy")}

            provider = BrowserCookieFallbackProvider(config_path=config_path, login_func=legacy_login)

            result = provider.login(output=lambda message: None)

            self.assertTrue(result.ok)
            self.assertEqual(result.source, "browser")
            self.assertEqual(result.cookie, "__puus=legacy")


class QuarkAuthManagerTests(unittest.TestCase):
    def test_login_uses_qr_provider_first_and_saves_cookie(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            manager = QuarkAuthManager(
                config_path=config_path,
                qr_provider=lambda: AuthResult(ok=True, source="qr", cookie="__puus=qr-cookie"),
                fallback_provider=lambda: AuthResult(ok=False, source="fallback", error="should not run"),
            )

            result = manager.login(output=lambda message: None)

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "qr")
            self.assertIn("__puus=qr-cookie", config_path.read_text(encoding="utf-8"))

    def test_login_falls_back_to_cookie_provider_when_qr_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            messages = []
            manager = QuarkAuthManager(
                config_path=config_path,
                qr_provider=lambda: AuthResult(ok=False, source="qr", error="qr unavailable"),
                fallback_provider=lambda: AuthResult(ok=True, source="browser", cookie="__puus=fallback"),
            )

            result = manager.login(output=messages.append)

            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "browser")
            self.assertIn("qr unavailable", "\n".join(messages))
            self.assertIn("__puus=fallback", config_path.read_text(encoding="utf-8"))

    def test_login_fails_when_all_providers_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = QuarkAuthManager(
                config_path=Path(tmp) / "config.json",
                qr_provider=lambda: AuthResult(ok=False, source="qr", error="qr failed"),
                fallback_provider=lambda: AuthResult(ok=False, source="manual", error="manual failed"),
            )

            result = manager.login(output=lambda message: None)

            self.assertFalse(result["ok"])
            self.assertIn("manual failed", result["error"])


if __name__ == "__main__":
    unittest.main()
