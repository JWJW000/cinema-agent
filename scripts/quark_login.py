"""Browser-assisted Quark login flow for the terminal agent."""

from __future__ import annotations

import getpass
import subprocess
import webbrowser
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable

try:
    from .agent_config import DEFAULT_CONFIG_PATH, update_quark_cookie
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH, update_quark_cookie


QUARK_URL = "https://pan.quark.cn"
QUARK_COOKIE_NAMES = {"__puus", "kps", "sign", "vcode", "tfstk"}


def cookie_looks_like_quark(cookie: str) -> bool:
    names = {part.split("=", 1)[0].strip() for part in cookie.split(";") if "=" in part}
    return bool(names & QUARK_COOKIE_NAMES)


def browser_cookie_string(cookies: Iterable[Any]) -> str:
    parts = []
    for cookie in cookies:
        domain = getattr(cookie, "domain", "") or ""
        name = getattr(cookie, "name", "") or ""
        value = getattr(cookie, "value", "") or ""
        if "quark.cn" in domain and name and value:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


def load_browser_cookies() -> list[Any]:
    try:
        import browser_cookie3
    except ModuleNotFoundError:
        return []

    loaders = [
        getattr(browser_cookie3, name, None)
        for name in ("chrome", "edge", "safari", "firefox", "opera", "brave")
    ]
    for loader in loaders:
        if loader is None:
            continue
        try:
            cookies = list(loader(domain_name="quark.cn"))
        except Exception:
            continue
        if cookies:
            return cookies
    return []


def load_clipboard_text() -> str:
    try:
        completed = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
    except (FileNotFoundError, subprocess.SubprocessError):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def login_quark_with_browser(
    config_path: Path = DEFAULT_CONFIG_PATH,
    open_url: Callable[[str], Any] = webbrowser.open,
    input_fn: Callable[[str], str] = input,
    hidden_input: Callable[[str], str] = getpass.getpass,
    visible_input: Callable[[str], str] = input,
    clipboard_loader: Callable[[], str] = load_clipboard_text,
    cookie_loader: Callable[[], Iterable[Any]] = load_browser_cookies,
    output: Callable[[str], None] = print,
) -> dict[str, Any]:
    open_url(QUARK_URL)
    output("已打开夸克网盘。如果浏览器没有自动跳出，请手动打开 https://pan.quark.cn")
    output("请在浏览器完成登录，然后回到这里。")
    input_fn("登录完成后按 Enter 继续...")

    browser_cookie = browser_cookie_string(cookie_loader())
    if browser_cookie and cookie_looks_like_quark(browser_cookie):
        update_quark_cookie(config_path, browser_cookie)
        return {"ok": True, "source": "browser", "cookie_length": len(browser_cookie)}

    output("没有自动读取到夸克 Cookie，改用手动兜底。")
    output("如果你已经复制了 Cookie，我会先尝试直接读取剪贴板。")
    clipboard_cookie = clipboard_loader().strip()
    if clipboard_cookie and cookie_looks_like_quark(clipboard_cookie):
        update_quark_cookie(config_path, clipboard_cookie)
        return {"ok": True, "source": "clipboard", "cookie_length": len(clipboard_cookie)}

    output("剪贴板里没有可用的夸克 Cookie。")
    output("浏览器开发者工具 Network 中任选 pan.quark.cn 请求，复制 Cookie 请求头。")
    output("先尝试隐藏输入；如果粘贴后看不到字符，直接按 Enter。")
    manual_cookie = hidden_input("Cookie: ").strip()
    source = "manual"
    if not manual_cookie:
        output("隐藏输入为空，改用可见粘贴。粘贴后按 Enter：")
        manual_cookie = visible_input("Cookie: ").strip()
        source = "visible"
    if not manual_cookie:
        return {"ok": False, "source": "manual", "error": "未输入 Cookie"}
    if not cookie_looks_like_quark(manual_cookie):
        return {"ok": False, "source": "manual", "error": "不像夸克 Cookie，未保存"}

    update_quark_cookie(config_path, manual_cookie)
    return {"ok": True, "source": source, "cookie_length": len(manual_cookie)}
