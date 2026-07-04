"""Tool wrappers around the existing cinema CLI functions."""

from __future__ import annotations

from typing import Any


def _cinema_module():
    try:
        from .. import cinema
    except ImportError:  # pragma: no cover - script execution fallback
        import cinema
    return cinema


def cinema_search(arguments: dict[str, Any]) -> Any:
    cinema = _cinema_module()
    query = arguments.get("query", "")
    config = cinema.load_config()
    plugins = cinema.load_plugins(config)
    all_results = []
    for plugin in plugins:
        try:
            results = plugin.search(query)
        except Exception:
            continue
        for result in results:
            result.site = plugin.name
            result.extra["score"] = cinema.score_resource(result)
            all_results.append(result)

    all_results.sort(key=lambda item: item.extra.get("score", 0), reverse=True)
    return {
        "query": query,
        "count": len(all_results),
        "results": [
            {
                "title": item.title,
                "source": item.source,
                "site": item.site,
                "score": item.extra.get("score", 0),
                "url": item.url,
            }
            for item in all_results[:20]
        ],
    }


def cinema_plugins(arguments: dict[str, Any] | None = None) -> Any:
    cinema = _cinema_module()
    plugins = cinema.load_plugins(cinema.load_config())
    return {
        "plugins": [
            {
                "name": plugin.name,
                "display_name": plugin.display_name,
                "requires_auth": plugin.requires_auth,
                "url": plugin.url,
            }
            for plugin in plugins
        ]
    }


def cinema_save(arguments: dict[str, Any]) -> Any:
    cinema = _cinema_module()
    try:
        return cinema.cmd_save(arguments.get("share_url", ""), cinema.load_config(), arguments.get("folder", ""))
    except ModuleNotFoundError as exc:
        return {"error": f"缺少依赖：{exc.name}。请先安装后再保存。"}


def cinema_save_result(arguments: dict[str, Any]) -> Any:
    cinema = _cinema_module()
    result = arguments.get("result", {})
    if not isinstance(result, dict):
        return {"error": "保存失败：结果格式不正确"}

    config = cinema.load_config()
    plugins = cinema.load_plugins(config)
    plugin = next((item for item in plugins if item.name == result.get("site")), None)
    if not plugin:
        return {"error": f"找不到内容源插件：{result.get('site', '')}"}

    try:
        resource = cinema.ResourceResult(
            title=result.get("title", ""),
            source=result.get("source", ""),
            url=result.get("url", ""),
            site=result.get("site", ""),
            extra={"score": result.get("score", 0)},
        )
        share_url = plugin.extract_link(resource)
    except Exception as exc:
        return {"error": f"提取分享链接失败：{exc}"}

    if not share_url:
        return {"error": "提取分享链接失败"}

    saved = cinema_save({"share_url": share_url, "folder": arguments.get("folder", "")})
    if isinstance(saved, dict) and saved.get("error"):
        return saved
    folder = arguments.get("folder") or config.get("save_folder", "夸克影视")
    return {
        "status": "ok",
        "title": result.get("title", ""),
        "share_url": share_url,
        "save_folder": folder,
        "result": saved,
    }


def cinema_auto(arguments: dict[str, Any]) -> Any:
    cinema = _cinema_module()
    return cinema.cmd_auto(arguments.get("query", ""), cinema.load_config())
