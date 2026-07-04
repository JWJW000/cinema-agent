# 🎬 Cinema Agent

A terminal-first media assistant for personal media library management — chat with an OpenAI-compatible model, discover content, save to Quark cloud drive, and keep lightweight session/preferences memory.

## Features

- 🔍 **Multi-source search** — plugin system, add any content source
- 📊 **Quality scoring** — auto-ranks by resolution, source, HDR, audio, codec, subtitles
- ☁️ **Quark save** — one-click save to your Quark cloud drive
- 🎭 **Genre auto-classification** — OMDB API or content source scraping, with local cache
- 📁 **Library management** — auto-organize files for Infuse/Plex/Jellyfin
- 🤖 **Terminal agent** — start with `jw`/`JW`, chat naturally, stream model replies, and call approved tools
- 🧠 **Memory** — session memory for recent search/save state, plus persistent preferences via `/remember`

## Quick Start

```bash
git clone https://github.com/JWJW000/cinema-agent.git
cd cinema-agent
pip install httpx
python3 scripts/setup.py
python3 scripts/setup.py --install-agent-command
```

Setup wizard walks you through:
1. **夸克网盘登录** — browser-assisted Cookie login
2. **内容源选择** — 自动检测已安装插件，逐个启用/禁用
3. **自动分类** — OMDB API（推荐）/ 内容源抓取 / 关闭
4. **保存目录** — 夸克网盘中的文件夹名

## Usage

### Terminal Agent

Install the terminal entry commands:

```bash
python3 scripts/setup.py --install-agent-command
```

Make sure `~/.local/bin` is in your `PATH`, then start the agent with either command:

```bash
JW
jw
```

Configure an OpenAI-compatible model with environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4.1-mini"
# optional, for compatible providers:
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Inside the agent:

```text
/help          Show commands
/config        Show safe config summary
/tools         List available tools
/memory        Show current memory
/remember k=v  Remember a preference
/forget        Clear session memory
/login quark   Open Quark in your browser, auto-detect Cookie when possible
/exit          Exit
```


### Via Hermes Agent

Just tell your agent:
- "我要看星际穿越"
- "搜一下流浪地球2"
- "帮我整理一下夸克网盘里的影视资源"

### CLI

```bash
python3 scripts/cinema.py search "流浪地球"        # Search
python3 scripts/cinema.py auto "星际穿越"           # Search + save + organize
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"  # Save a link
python3 scripts/cinema.py organize <fid> "电影名" --type movie  # Organize
python3 scripts/cinema.py plugins                    # List plugins
python3 scripts/setup.py                             # Re-run setup wizard
python3 scripts/agent.py                             # Start JW agent without installing commands
```

## Configuration

Edit `config.json` (created by setup wizard):

```json
{
  "quark": {
    "cookie": "your_cookie_from_browser"
  },
  "plugins": {
    "wp365": { "enabled": true }
  },
  "save_folder": "夸克影视",
  "omdb_api_key": "",
  "agent": {
    "provider": "openai_compatible",
    "base_url": "https://api.openai.com/v1",
    "model": "",
    "api_key_env": "OPENAI_API_KEY",
    "allow_shell": "confirm",
    "history_limit": 20
  },
  "memory": {
    "enabled": true,
    "path": "~/.cinema-manager/memory.json"
  }
}
```

### Quark Auth

In the terminal agent, run `/login quark`. JW opens [pan.quark.cn](https://pan.quark.cn), waits for you to finish browser login, then tries to read the Quark Cookie from your local browser. If automatic detection is unavailable, it falls back to hidden Cookie paste.

Cookies expire after ~7 days. When expired, run `/login quark` again.

### Memory

The terminal agent keeps two kinds of memory:

- Session memory: recent search results and last save result, cleared by `/forget`
- Preference memory: small persistent key-value preferences stored in `~/.cinema-manager/memory.json`

Commands:

```text
/memory
/remember quality=4K
/forget
```

### Genre Classification

| Mode | Config | Accuracy | Cost |
|------|--------|----------|------|
| OMDB API | `"omdb_api_key": "your_key"` | High | Free, 1000 req/day |
| Content scrape | `"omdb_api_key": ""` | Medium | Free |
| Disabled | (movies go to flat structure) | N/A | Free |

Get a free OMDB key at [omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx) — just enter your email.

Genre results cached in `scripts/genre_cache.json`.

## Adding Content Sources

Drop a `.py` plugin file into `scripts/plugins/`:

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

Implement two methods:

```python
from plugins import ResourcePlugin, ResourceResult

class Plugin(ResourcePlugin):
    name = "your_site"
    display_name = "Your Site Name"
    requires_auth = False
    url = "https://your-site.com"

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        ...
    def extract_link(self, resource: ResourceResult) -> str | None:
        ...
```

Then enable in `config.json` or re-run `setup.py`. See `scripts/plugins/example.py` for a full template.

## Library Structure

```
夸克影视/
├── 动作/
│   └── 金谍行动 (2026)/
│       └── In.the.Grey.2026.2160p.WEB-DL.mkv
├── 剧情/
│   └── 大濛 (2025)/
│       └── A.Foggy.Tale.2025.1080p.NF.WEB-DL.mkv
├── 科幻/
│   └── 流浪地球2 (2023)/
│       └── 流浪地球2 (2023).mkv
└── 其他/
    └── 未识别类型的电影 (2024)/
```

Infuse/Plex compatible naming:
- Movie: `Movie Name (Year).ext`
- TV: `Show Name/Season XX/Show Name - SXXEXX.ext`

## Quality Scoring

| Factor | Best | Worst |
|--------|------|-------|
| Resolution | 2160p/4K (+100) | 480p (+5) |
| Source | BluRay/REMUX (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | None (0) |
| Audio | Atmos/TrueHD (+15) | AAC (+2) |
| Codec | H.265/HEVC (+10) | H.264 (+5) |
| Subtitles | Included (+5) | None (0) |
| Platform | Quark (+15) | Baidu (0) |

## License

MIT
