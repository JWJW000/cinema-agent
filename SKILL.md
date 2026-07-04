---
name: cinema-agent
description: Terminal-first personal media assistant — chat with an OpenAI-compatible model, discover content, save to Quark cloud drive, auto-organize for Infuse/Plex, and remember lightweight preferences. Use when user wants to find/watch movies, save to cloud drive, manage media library, or run the local JW terminal agent.
---

# Cinema Agent

Terminal conversation → Media discovery → Cloud save → Library organization.

## Quick Start

```bash
python3 scripts/setup.py --install-agent-command
jw
```

CLI fallback:

```bash
python3 scripts/cinema.py auto "电影名"     # search + save + organize
python3 scripts/cinema.py search "电影名"   # search only
python3 scripts/cinema.py plugins           # list plugins
```

## Config

`config.json` (not committed, create from `config.example.json`):
- `quark.cookie` — Quark session cookie (login to pan.quark.cn, copy cookie from browser DevTools)
- `plugins` — enable/disable content source plugins
- `save_folder` — Quark folder name (default: "影视资源")
- `agent` — OpenAI-compatible model settings
- `memory` — persistent preference memory path

## Adding Content Sources

1. Copy `scripts/plugins/example.py` to `scripts/plugins/your_site.py`
2. Implement `search()` and `extract_link()`
3. Add `"your_site": {"enabled": true}` to config.json

## Library Management

`cinema.py organize <fid> <title> --type movie|tv`

Organizes files into Infuse/Plex-compatible structure:
- Movies: `影视资源/Movie Name (Year)/Movie Name (Year).ext`
- TV: `影视资源/Show Name/Season XX/Show Name - SXXEXX.ext`

## Workflow

1. User starts `jw`
2. User says "I want to watch X"
3. Agent searches across configured content sources
4. Agent remembers recent search results
5. User confirms save, e.g. "保存第一个结果"
6. Agent saves to Quark and can organize into library structure
7. Infuse/Plex auto-detects and fetches metadata

## Memory

- `/memory` shows session and preference memory
- `/remember key=value` stores a persistent preference
- `/forget` clears session memory only
