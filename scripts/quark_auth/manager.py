"""Quark authentication orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

try:
    from ..agent_config import DEFAULT_CONFIG_PATH
    from .providers import AuthResult, BrowserCookieFallbackProvider, QuarkpanQrProvider
    from .storage import QuarkAuthStorage
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH
    from quark_auth.providers import AuthResult, BrowserCookieFallbackProvider, QuarkpanQrProvider
    from quark_auth.storage import QuarkAuthStorage


class QuarkAuthManager:
    def __init__(
        self,
        config_path: Path = DEFAULT_CONFIG_PATH,
        qr_provider: Callable[[], AuthResult] | None = None,
        fallback_provider: Callable[[], AuthResult] | None = None,
        storage: QuarkAuthStorage | None = None,
    ):
        self.config_path = Path(config_path)
        self.storage = storage or QuarkAuthStorage(self.config_path)
        self.qr_provider = qr_provider
        self.fallback_provider = fallback_provider

    def login(self, output: Callable[[str], None] = print) -> dict[str, object]:
        output("优先使用夸克 App 扫码登录。")
        qr_result = self._login_qr(output)
        if qr_result.ok:
            self.storage.save_cookie(qr_result.cookie, qr_result.source)
            return {"ok": True, "source": qr_result.source, "cookie_length": len(qr_result.cookie)}

        output(f"扫码登录不可用：{qr_result.error}")
        output("改用浏览器/Cookie 兜底登录。")
        fallback_result = self._login_fallback(output)
        if fallback_result.ok:
            if fallback_result.cookie:
                self.storage.save_cookie(fallback_result.cookie, fallback_result.source)
                cookie_length = len(fallback_result.cookie)
            else:
                cookie_length = self.storage.status()["cookie_length"]
            return {"ok": True, "source": fallback_result.source, "cookie_length": cookie_length}

        return {"ok": False, "source": fallback_result.source, "error": fallback_result.error}

    def status(self) -> dict[str, object]:
        return self.storage.status()

    def _login_qr(self, output: Callable[[str], None]) -> AuthResult:
        if self.qr_provider is not None:
            return self.qr_provider()
        return QuarkpanQrProvider().login(output=output)

    def _login_fallback(self, output: Callable[[str], None]) -> AuthResult:
        if self.fallback_provider is not None:
            return self.fallback_provider()
        return BrowserCookieFallbackProvider(self.config_path).login(output=output)
