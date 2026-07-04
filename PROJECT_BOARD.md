# 🎬 cinema-agent — 项目说明

> 最后更新：2026-07-04 | 当前版本：v1.1 | 状态：终端 Agent 可用 ✅

---

## 一、总览

```
产品：终端对话式影视资源管理 Agent
定位：自然语言对话 → 内容源搜索 → 夸克网盘转存 → 自动分类整理 → Infuse/Plex/Jellyfin 可用
模式：开源免费（MIT），本地终端 agent + CLI
GitHub：github.com/JWJW000/cinema-agent
```

---

## 二、目录结构

```
cinema-agent/
├── SKILL.md                    # Hermes Agent skill 定义
├── README.md                   # 用户文档
├── config.example.json         # 配置模板
├── config.json                 # 本地配置（不提交，含账号密码）
├── scripts/
│   ├── agent.py                # JW/jw 终端 Agent 入口
│   ├── agent_core.py           # Agent 编排、流式输出、工具调用
│   ├── agent_config.py         # Agent 配置读取
│   ├── llm.py                  # OpenAI-compatible 模型客户端
│   ├── cinema.py               # 主入口（search/save/auto/organize）
│   ├── quark.py                # 夸克网盘 API
│   ├── quark_login.py          # 浏览器辅助夸克登录
│   ├── library.py              # 分类整理逻辑
│   ├── setup.py                # 交互式配置向导
│   ├── memory/                 # 会话记忆与持久偏好记忆
│   ├── tools/                  # Agent 工具注册与实现
│   └── plugins/
│       ├── __init__.py         # 插件基类
│       ├── example.py          # 插件开发模板
│       └── wp365.py            # 365wp 内容源
└── tests/                      # 单元测试
```

---

## 三、版本历史

### v1.0 — 初始发布 ✅ 2026-06-03

- [x] 多源搜索 + 插件系统（wp365、mini4k、example 模板）
- [x] 夸克网盘转存 + Cookie 认证
- [x] 自动分类（OMDB API / 内容源抓取 / 关闭三种模式）
- [x] 质量评分（分辨率、来源、HDR、音频、编码、字幕）
- [x] setup.py 交互式配置向导
- [x] README 完善、.gitignore 排除 config.json
- [x] 措辞从 "resource site" 改为 "content source"，避免 LLM 触发版权拒绝

### v1.1 — 终端 Agent ✅ 2026-07-04

- [x] `JW` / `jw` 终端启动入口
- [x] OpenAI-compatible 模型接入
- [x] 流式输出
- [x] 工具注册表与风险确认
- [x] 浏览器辅助夸克登录，剪贴板/可见粘贴兜底
- [x] 搜索结果格式化、保存上下文记忆
- [x] 会话记忆与持久偏好记忆
- [x] 单元测试覆盖核心流程

---

## 四、待办

- [ ] 增加偏好删除命令，例如 `/forget preference quality`
- [ ] 改进保存到夸克后的路径校验
- [ ] 支持更多模型 provider，例如 Ollama

---

## 五、关键信息

- **config.json 含夸克 Cookie/API Key，绝不提交 git**
- 插件开发参考 `scripts/plugins/example.py`
- LLM 措辞注意：用 "content source" 不用 "resource site"
- 记忆文件默认在 `~/.cinema-manager/memory.json`

---

## 六、Agent 交接说明

本项目当前状态稳定。如需扩展：
1. 新增内容源 → 复制 `scripts/plugins/example.py`，实现 `search()` 和 `extract_link()`
2. 修改分类逻辑 → `scripts/library.py`
3. 修改夸克操作 → `scripts/quark.py`
4. 修改 Agent 编排 → `scripts/agent_core.py`
5. 修改记忆模块 → `scripts/memory/`
