#!/usr/bin/env python3
"""Terminal entry point for JW agent."""

from __future__ import annotations

import argparse
import re
import sys

try:
    from .agent_config import DEFAULT_CONFIG_PATH, load_agent_model_config, load_json_config, safe_config_summary
    from .agent_core import AgentCore, build_default_registry
    from .quark_login import login_quark_with_browser
except ImportError:  # pragma: no cover - script execution fallback
    from agent_config import DEFAULT_CONFIG_PATH, load_agent_model_config, load_json_config, safe_config_summary
    from agent_core import AgentCore, build_default_registry
    from quark_login import login_quark_with_browser


def build_core() -> AgentCore:
    config = load_json_config(DEFAULT_CONFIG_PATH)
    model_config = load_agent_model_config(config)
    return AgentCore(model_config=model_config, registry=build_default_registry(), config=config)


def print_banner(core: AgentCore) -> None:
    summary = safe_config_summary(core.config)
    model = core.model_config.model or "未配置"
    print("JW Agent")
    print(f"模型：{model}")
    print(f"夸克：{'已配置' if summary['quark']['configured'] else '未配置'}")
    print("输入 /help 查看命令，/exit 退出")
    print()


def handle_login_quark() -> str:
    result = login_quark_with_browser(DEFAULT_CONFIG_PATH)
    if not result.get("ok"):
        return f"夸克登录未完成：{result.get('error', '未知错误')}"
    source = "浏览器自动读取" if result.get("source") == "browser" else "手动输入"
    return f"夸克 Cookie 已保存（来源：{source}，长度 {result.get('cookie_length', 0)}），有效性将在下次夸克请求时确认。"


def normalize_command(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().lower())


def is_login_quark_command(text: str) -> bool:
    normalized = normalize_command(text)
    return normalized in {"/login", "/loginquark", "loginquark", "登录夸克"}


def repl() -> int:
    core = build_core()
    print_banner(core)

    while True:
        try:
            user_text = input("你> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return 130

        text = user_text.strip()
        if not text:
            continue
        if text in {"/exit", "exit", "quit", "/quit"}:
            return 0
        if is_login_quark_command(text):
            print(f"agent> {handle_login_quark()}")
            core = build_core()
            continue

        try:
            print("agent> ", end="", flush=True)
            wrote = False
            for chunk in core.handle_input_stream(text):
                print(chunk, end="", flush=True)
                wrote = True
            if wrote:
                print()
            else:
                print()
        except Exception as exc:
            print(f"出错了：{exc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the JW terminal agent.")
    parser.add_argument("--config", action="store_true", help="Print safe config summary and exit")
    args = parser.parse_args(argv)

    if args.config:
        print(core_config_summary())
        return 0
    return repl()


def core_config_summary() -> str:
    import json

    return json.dumps(safe_config_summary(load_json_config(DEFAULT_CONFIG_PATH)), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
