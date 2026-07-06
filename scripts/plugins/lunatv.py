"""
LunaTV-config plugin.

Searches MacCMS-compatible API sources listed in LunaTV-config.json.
These are online playback sources, not Quark share links.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Optional

from . import ResourcePlugin, ResourceResult


DEFAULT_CONFIG_URL = "https://raw.githubusercontent.com/hafrey1/LunaTV-config/main/LunaTV-config.json"


class Plugin(ResourcePlugin):
    name = "lunatv"
    display_name = "LunaTV 多源"
    requires_auth = False
    url = "https://github.com/hafrey1/LunaTV-config"

    def __init__(self, config: dict | None = None):
        super().__init__(config=config)
        self.config_url = self.config.get("config_url", DEFAULT_CONFIG_URL)
        self.max_sources = int(self.config.get("max_sources", 10))
        self.timeout = int(self.config.get("timeout", 10))

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        results: list[ResourceResult] = []
        for key, site in self._enabled_sites()[: self.max_sources]:
            api = (site.get("api") or "").strip()
            if not api:
                continue
            try:
                data = self.request_json(self._search_url(api, query, page))
            except Exception as exc:
                print(f"[lunatv] {key} search error: {exc}")
                continue
            results.extend(self._map_results(site_key=key, site=site, data=data))
        return results

    def extract_link(self, resource: ResourceResult) -> Optional[str]:
        return None

    def request_json(self, url: str) -> dict[str, Any]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
        return json.loads(raw)

    def _enabled_sites(self) -> list[tuple[str, dict[str, Any]]]:
        sites = self.config.get("sites")
        if not sites:
            try:
                sites = self.request_json(self.config_url).get("api_site", {})
            except Exception as exc:
                print(f"[lunatv] config load error: {exc}")
                return []
        disabled = set(self.config.get("disabled_sites", []))
        include = set(self.config.get("include_sites", []))
        items = []
        for key, site in sites.items():
            if include and key not in include:
                continue
            if key in disabled:
                continue
            if isinstance(site, dict):
                items.append((key, site))
        return items

    def _search_url(self, api: str, query: str, page: int) -> str:
        separator = "&" if "?" in api else "?"
        params = urllib.parse.urlencode({"ac": "detail", "wd": query, "pg": str(page)})
        return f"{api}{separator}{params}"

    def _map_results(self, site_key: str, site: dict[str, Any], data: dict[str, Any]) -> list[ResourceResult]:
        source_name = self._clean_source_name(site.get("name") or site_key)
        mapped = []
        for item in data.get("list", []) or []:
            title = self._title(item, source_name)
            play_url = self._first_play_url(item.get("vod_play_url", ""))
            mapped.append(
                ResourceResult(
                    title=title,
                    source="online",
                    url=play_url,
                    site=self.name,
                    quality=item.get("vod_remarks", "") or "",
                    extra={
                        "source_name": source_name,
                        "source_key": site_key,
                        "api": site.get("api", ""),
                        "year": item.get("vod_year", "") or "",
                        "actor": item.get("vod_actor", "") or "",
                        "remarks": item.get("vod_remarks", "") or "",
                        "play_from": item.get("vod_play_from", "") or "",
                    },
                )
            )
        return mapped

    def _title(self, item: dict[str, Any], source_name: str) -> str:
        parts = [str(item.get("vod_name", "")).strip()]
        year = str(item.get("vod_year", "") or "").strip()
        remarks = str(item.get("vod_remarks", "") or "").strip()
        if year:
            parts[0] = f"{parts[0]} ({year})"
        parts.append(source_name)
        if remarks:
            parts.append(remarks)
        return " - ".join(part for part in parts if part)

    def _first_play_url(self, raw: str) -> str:
        if not raw:
            return ""
        first_group = raw.split("$$$", 1)[0]
        first_item = first_group.split("#", 1)[0]
        if "$" in first_item:
            return first_item.split("$", 1)[1].strip()
        return first_item.strip()

    def _clean_source_name(self, name: str) -> str:
        return name.replace("🎬", "").strip()
