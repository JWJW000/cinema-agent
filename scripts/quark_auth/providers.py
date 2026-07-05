"""Authentication providers for Quark login."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

try:
    from ..agent_config import DEFAULT_CONFIG_PATH, load_json_config
    from ..quark_login import login_quark_with_browser
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH, load_json_config
    from quark_login import login_quark_with_browser


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    source: str
    cookie: str = ""
    error: str = ""


class QuarkpanQrProvider:
    """QR login provider backed by the optional quarkpan package."""

    def __init__(self, api_login_cls: Any = ..., timeout: int = 300):
        self.timeout = timeout
        if api_login_cls is ...:
            api_login_cls = self._load_api_login_cls()
        self.api_login_cls = api_login_cls

    def _load_api_login_cls(self) -> Any:
        try:
            from quark_client.auth.api_login import APILogin
        except ModuleNotFoundError:
            return None
        return APILogin

    def login(self, output: Callable[[str], None] = print) -> AuthResult:
        if self.api_login_cls is None:
            return AuthResult(ok=False, source="qr", error="缺少依赖 quarkpan，无法生成扫码登录二维码")

        output("正在生成夸克扫码登录二维码，请稍候...")
        try:
            api_login = self.api_login_cls(timeout=self.timeout)
            cookie = (api_login.login() or "").strip()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            return AuthResult(ok=False, source="qr", error=str(exc))

        if not cookie:
            return AuthResult(ok=False, source="qr", error="扫码登录未返回 Cookie")
        return AuthResult(ok=True, source="qr", cookie=cookie)


class BrowserCookieFallbackProvider:
    """Fallback provider that reuses the existing browser/Cookie flow."""

    def __init__(self, config_path=DEFAULT_CONFIG_PATH, login_func=login_quark_with_browser):
        self.config_path = config_path
        self.login_func = login_func

    def login(self, output: Callable[[str], None] = print) -> AuthResult:
        result = self.login_func(config_path=self.config_path, output=output)
        if result.get("ok"):
            config = load_json_config(self.config_path)
            cookie = config.get("quark", {}).get("cookie", "") or ""
            return AuthResult(ok=True, source=result.get("source", "browser"), cookie=cookie)
        return AuthResult(ok=False, source=result.get("source", "browser"), error=result.get("error", "Cookie 兜底登录失败"))
