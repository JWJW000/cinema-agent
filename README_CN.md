# 🎬 Cinema Agent

面向终端对话的个人影视管理助手：接入 OpenAI 兼容大模型，支持自然语言搜索内容源、保存到夸克网盘、自动整理媒体库，并带有轻量记忆能力。

## 功能特性

- 🔍 **多源搜索** — 插件系统，可添加任意内容源
- 📊 **质量评分** — 按分辨率、片源、HDR、音频、编码、字幕自动排序
- ☁️ **夸克网盘保存** — 一键保存到夸克网盘
- 🎭 **自动分类** — OMDB API 或内容源抓取，本地缓存
- 📁 **媒体库管理** — 自动整理为 Infuse/Plex/Jellyfin 兼容格式
- 🤖 **终端 Agent** — 通过 `jw`/`JW` 启动，支持自然语言对话、流式输出和受控工具调用
- 🧠 **记忆模块** — 记住最近搜索/保存状态，也可以用 `/remember` 保存偏好

## 快速开始

```bash
git clone https://github.com/JWJW000/cinema-agent.git
cd cinema-agent
pip install httpx
python3 scripts/setup.py
python3 scripts/setup.py --install-agent-command
```

设置向导会引导你完成：
1. **夸克网盘登录** — 浏览器辅助 Cookie 登录
2. **内容源选择** — 自动检测已安装插件，逐个启用/禁用
3. **自动分类** — OMDB API（推荐）/ 内容源抓取 / 关闭
4. **保存目录** — 夸克网盘中的文件夹名

## 使用方法

### 终端 Agent

安装终端命令：

```bash
python3 scripts/setup.py --install-agent-command
```

确认 `~/.local/bin` 已在 `PATH` 中，然后可以用任一命令启动：

```bash
JW
jw
```

通过环境变量配置 OpenAI 兼容模型：

```bash
export OPENAI_API_KEY="你的 API Key"
export OPENAI_MODEL="gpt-4.1-mini"
# 可选，用于兼容接口：
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Agent 内置命令：

```text
/help          查看命令
/config        查看安全配置摘要
/tools         查看可用工具
/memory        查看当前记忆
/remember k=v  记住一条偏好
/forget        清空会话记忆
/login quark   打开夸克网页，优先自动读取 Cookie
/exit          退出
```

示例：

```text
你> 帮我找范冰冰主演的苹果
agent> 找到 1 个结果：
1. 名称：《 苹果》 (2007) ... [quark/wp365] 评分 70
如果要保存，可以说“保存第一个结果”。

你> /remember quality=4K
agent> 已记住：quality = 4K
```

### 通过 Hermes Agent

直接告诉你的助手：
- "我要看星际穿越"
- "搜一下流浪地球2"
- "帮我整理一下夸克网盘里的影视资源"

### 命令行

```bash
python3 scripts/cinema.py search "流浪地球"        # 搜索
python3 scripts/cinema.py auto "星际穿越"           # 搜索 + 保存 + 整理
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"  # 保存链接
python3 scripts/cinema.py organize <fid> "电影名" --type movie  # 整理
python3 scripts/cinema.py plugins                    # 查看插件
python3 scripts/setup.py                             # 重新运行设置向导
python3 scripts/agent.py                             # 不安装命令时直接启动 JW agent
```

## 配置说明

编辑 `config.json`（由设置向导创建）：

```json
{
  "quark": {
    "cookie": "从浏览器获取的cookie"
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

### 夸克认证

在终端 agent 中运行 `/login quark`。JW 会打开 [pan.quark.cn](https://pan.quark.cn)，等你在浏览器完成登录后，优先尝试从本机浏览器读取夸克 Cookie。若自动读取不可用，会退回隐藏粘贴 Cookie 的方式。

Cookie 约 7 天过期，过期后重新运行 `/login quark` 即可。

### 记忆模块

终端 agent 有两类记忆：

- 会话记忆：最近搜索结果、最近保存结果，用 `/forget` 清空
- 偏好记忆：持久化的小型键值偏好，存储在 `~/.cinema-manager/memory.json`

命令：

```text
/memory
/remember quality=4K
/forget
```

### 自动分类

| 模式 | 配置 | 准确度 | 费用 |
|------|------|--------|------|
| OMDB API | `"omdb_api_key": "你的key"` | 高 | 免费，1000次/天 |
| 内容源抓取 | `"omdb_api_key": ""` | 中 | 免费 |
| 关闭 | （电影存入扁平结构） | 无 | 免费 |

在 [omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx) 免费获取 OMDB API Key，只需输入邮箱。

分类结果缓存在 `scripts/genre_cache.json`。

## 添加内容源

将 `.py` 插件文件放入 `scripts/plugins/` 目录：

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

实现两个方法：

```python
from plugins import ResourcePlugin, ResourceResult

class Plugin(ResourcePlugin):
    name = "your_site"
    display_name = "你的站点名"
    requires_auth = False
    url = "https://your-site.com"

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        ...
    def extract_link(self, resource: ResourceResult) -> str | None:
        ...
```

然后在 `config.json` 中启用，或重新运行 `setup.py`。详见 `scripts/plugins/example.py` 完整模板。

## 媒体库结构

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

Infuse/Plex 兼容命名：
- 电影：`电影名 (年份).扩展名`
- 电视剧：`剧名/Season XX/剧名 - SXXEXX.扩展名`

## 质量评分

| 因素 | 最佳 | 最差 |
|------|------|------|
| 分辨率 | 2160p/4K (+100) | 480p (+5) |
| 片源 | BluRay/REMUX (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | 无 (0) |
| 音频 | Atmos/TrueHD (+15) | AAC (+2) |
| 编码 | H.265/HEVC (+10) | H.264 (+5) |
| 字幕 | 包含 (+5) | 无 (0) |
| 平台 | 夸克 (+15) | 百度 (0) |

## 许可证

MIT
