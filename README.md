# seekport

[![tests](https://github.com/ChemistryBus/seekport/actions/workflows/test.yml/badge.svg)](https://github.com/ChemistryBus/seekport/actions/workflows/test.yml)
[![release](https://img.shields.io/github/v/release/ChemistryBus/seekport?style=flat-square)](https://github.com/ChemistryBus/seekport/releases)
[![license](https://img.shields.io/github/license/ChemistryBus/seekport?style=flat-square)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)
![Agent Skill](https://img.shields.io/badge/Agent-Skill-111111?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-server-2F6F9F?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-6B5B95?style=flat-square)
![Codex](https://img.shields.io/badge/Codex-supported-222222?style=flat-square)
![Zcode](https://img.shields.io/badge/Zcode-supported-2F6F9F?style=flat-square)

🌏 English version: [README.en.md](./README.en.md)

**把 DeepSeek 官方的 Search / Fetch API 接到 Claude Code、Codex、Zcode 以及其他 agent harness。**

零依赖 · Agent Skill + MCP · `site:` / `lang:` / `after:` · 相关性/权威性过滤 · 每日预算上限

![seekport：不使用 vs 使用](docs/seekport-flow-zh.svg)

## 30 秒开始

### 方式一：装成 Agent Skill（推荐）

```bash
git clone https://github.com/ChemistryBus/seekport.git ~/seekport
ln -s ~/seekport ~/.claude/skills/seekport
export DEEPSEEK_API_KEY=sk-...
```

重启 Claude Code，然后直接说：

> 用 seekport 搜一下 Nutrients 最新的作者投稿指南

不需要 `pip install`。要求 Python 3.9+。

### 方式二：把这段话发给 AI Agent

> 帮我安装 seekport 这个 Agent Skill。请按下面步骤做：
>
> 1. 确保 `~/.claude/skills/` 存在
> 2. `git clone https://github.com/ChemistryBus/seekport.git ~/.claude/skills/seekport`
> 3. 检查 `SKILL.md`、`scripts/cli.py` 是否存在
> 4. 告诉我怎么设置 `DEEPSEEK_API_KEY`

### 方式三：MCP

```bash
claude mcp add seekport -- python3 "/绝对路径/seekport/mcp/seekport_mcp.py"
```

MCP 适合不能执行 shell 命令的 harness；能跑命令的 Claude Code / Codex 优先用 Skill。两种形态只装一种，避免重复工具和常驻上下文成本。

## 它能做什么

- **带过滤的网页搜索**：支持 `site:`、`-site:`、`"精确短语"`、`-词`、`lang:zh,en`、`after:`、`before:`；默认丢弃 `rerank_score < 1.5`，可加 `--min-authority 3` 只保留高权威来源。
- **抓取原文**：把一个 URL 抓成 Markdown，交给 agent 总结或引用。
- **两种形态**：Agent Skill 或 stdio MCP server（`deepseek_search` / `deepseek_fetch`），共用同一份核心。
- **成本护栏**：408 / 429 / 5xx 自动退避重试；重定向被拒绝；可选 `SEEKPORT_BUDGET` 每日预算上限。
- **零依赖**：纯 Python 3.9+ 标准库，核心 `scripts/ds_core.py` 290 行。

## 怎么搜

```bash
# 1. 查期刊投稿指南
python3 scripts/cli.py search "Nutrients author guidelines site:mdpi.com" --md

# 2. 查官方 API 文档
python3 scripts/cli.py search "DeepSeek pricing site:api-docs.deepseek.com" --md

# 3. 查某个方向的最新进展
python3 scripts/cli.py search "exercise metabolism after:2025 lang:en" --md

# 搜到候选后，抓取原文
python3 scripts/cli.py fetch "https://api-docs.deepseek.com/zh-cn/guides/search" --md
```

| 语法 | 作用 |
|---|---|
| `site:` | 限定站点 |
| `-site:` | 排除站点 |
| `"..."` | 精确短语 |
| `-词` | 排除词 |
| `lang:zh,en` | 限定语言 |
| `after:` / `before:` | 限定时间 |

常用参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--count` | 10 | 返回条数 1–50，**不影响单次计费** |
| `--min-rerank` | 1.5 | 低于该分数的结果丢弃；`0` 表示不过滤 |
| `--min-authority` | 关闭 | 低于该权威性的结果丢弃；`3`–`4` 为极权威 |
| `--md` | 关闭 | 输出 Markdown 而非 JSON |
| `--content` | 关闭 | 让 API 返回网页正文（更大更慢） |
| `--ori-question` | 关闭 | 用户原始问题，帮助理解搜索意图 |

## 为什么需要：一个真实案例

问 agent：“DeepSeek 的网页搜索 API 怎么收费？QPS 多少？”在第三方网关后面，`WebFetch` 读官方文档会报：

> Unable to verify if domain is safe to fetch.

搜索返回的第三方文章中，前三条有两条仍写着 **$0.75/千次、5 QPS**。用 seekport 抓取官方原文后看到的是 **¥5/千次、Search 100 QPS / Fetch 25 QPS**。

先搜索候选，再抓取权威原文并引用。一次搜索 + 一次抓取约 **¥0.01**。完整记录见 [examples/case-study.md](examples/case-study.md)。

## Skill 还是 MCP？

两种形态调用的是同一份 `search()` / `fetch()` 代码，区别在于 agent 如何发现和调用它们。

| | Agent Skill | MCP server |
|---|---|---|
| 安装 | 把仓库复制/软链到 harness 的 skills 目录 | 在 harness 的 MCP 配置里注册命令 |
| 发现方式 | 任务匹配 `SKILL.md` 描述时按需加载 | 每轮对话都把工具 schema 列给模型 |
| 上下文成本 | 未使用前约 0 token | schema 和描述每轮都占上下文 |
| 调用方式 | 模型在 shell 里执行 `python3 .../cli.py` | harness 通过 stdio 调 `tools/call` |
| 需要 shell 权限 | 是 | 否 |
| 适用 | Claude Code、Codex、Zcode 等能执行命令的 harness | 任意 MCP 客户端 |
| 主要风险 | 描述与任务不匹配时，模型可能想不起这个 skill | 常驻上下文成本；重复工具会干扰工具选择 |

**结论**：Claude Code / Codex 默认选 Skill；只有 harness 不能执行 shell 命令时才选 MCP。每个 harness 只装一种。

## 成本与限速

| 项目 | 数值 |
|---|---|
| Search | **每 1,000 次成功请求 ¥5** |
| Fetch | **每 1,000 次成功请求 ¥5** |
| 单次约 | ¥0.005 ≈ **$0.0007** |
| 计费条件 | HTTP 200 **且** Search 结果非空 / Fetch 有正文 |
| 不计费 | 报错、超时、空搜索结果 |
| 限速 | Search **100 QPS**，Fetch **25 QPS**（按账号） |

`--count` 只改返回条数，不改价格。设置 `SEEKPORT_BUDGET=0.05` 可把每日花费限制在 ¥0.05（10 次成功调用），账本位于 `~/.cache/seekport/spend.log`。

> 官方文档说明：通过 DSH / Claude Code / Codex 的 Server 端工具调用访问 Search/Fetch，自北京时间 2026-11-01 00:00 起已按次收费。seekport 是直连 API 客户端，计费方式相同。价格和限速可能变化，引用前请看[官方文档](https://api-docs.deepseek.com/zh-cn/guides/search)。

## 适合 / 不适合

**✅ 适合**

- 用 Claude Code / Codex / Zcode 跑 DeepSeek 的人
- 走第三方网关、`WebFetch` 被拦的人
- 需要查官方文档、期刊投稿指南、会议 deadline 的科研党
- 希望结果先过滤、再进模型，控制 token 和费用的人

**❌ 不适合**

- 需要 PubMed / Web of Science / Scopus 这类学术数据库
- 需要批量爬取、建索引或定时抓取
- 不想为 DeepSeek API 付费
- 不能运行 Python 3.9+ 或没有网络访问

## 常见问题

**和 `@deepseek-ai/dsh-web-deepseek-api` 有什么区别？**
DSH 用户直接用官方包；seekport 面向非 DSH harness、第三方网关，以及需要显式过滤和预算上限的人。

**需要付费吗？**
工具本身 MIT 免费；DeepSeek 的 Search / Fetch API 按次收费，约 ¥0.005 / 次，空结果和报错不计费。

**支持 Windows 吗？**
代码是纯标准库，但 Windows 尚未测试；macOS 和 Linux CI 已测试。

**Codex / Zcode 验证过吗？**
安装说明已写入 README；本次实测的是 Claude Code（Skill）、CLI 和 MCP stdio。Codex / Zcode 尚未在客户端内部逐一验证。

**为什么 WebFetch 会报错？**
第三方网关不认目标域名，`WebFetch` 无法验证安全性。seekport 把 URL 交给 DeepSeek 的 Fetch API，由服务端抓取。

**抓取失败怎么办？**
可能返回 403 / 404，或目标站点有付费墙 / 反爬。换一个 URL，或改用搜索结果的 `summary`。

**会把 API key 写进仓库吗？**
不会。key 只从 `DEEPSEEK_API_KEY` 读取；仓库不含 key；重定向被拒绝，token 不会被转发到其它 origin。

## 把 agent 后端接到 DeepSeek（可选）

seekport 只要求 `DEEPSEEK_API_KEY`，agent 本身不一定要跑在 DeepSeek 上。但 `WebFetch` 报错通常正是切到 DeepSeek 之后出现的。以下是 DeepSeek 官方配置。

<details>
<summary><b>Claude Code / Codex / Zcode 配置</b></summary>

### Claude Code

DeepSeek 提供 Anthropic 兼容端点（[官方接入文档](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code)）：

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<你的 DeepSeek API Key>
export ANTHROPIC_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-flash
```

然后在项目目录执行 `claude`。官方页面还设置了 `CLAUDE_CODE_EFFORT_LEVEL=max` 和 `CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432`；这两项是可选的调优参数，不影响能否连通。

使用官方端点时，Claude Code 的**服务端 Web Search** 可用；DeepSeek 会把每次搜索按 Search API 计费，并为总结搜索结果额外消耗模型 token。seekport 仍然有用的场景是：走**第三方网关**、该网关没有暴露服务端搜索工具，或你需要显式使用 `site:` / `lang:` 过滤、相关性阈值和本地花费上限。

### Codex

DeepSeek 原生支持 Responses API（[官方接入文档](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/codex)）。官方给了一键配置脚本；手动配置需要 `~/.codex/models.json` 模型目录和 `~/.codex/config.toml`：

```toml
model = "deepseek-flash"
model_provider = "deepseek"
preferred_auth_method = "apikey"
forced_login_method = "api"
model_reasoning_effort = "high"
web_search = "disabled"          # 只有 deepseek-v4-pro 才能设为 "live"
model_catalog_json = "~/.codex/models.json"

[model_providers.deepseek]
name = "deepseek"
base_url = "https://api.deepseek.com/"
wire_api = "responses"
experimental_bearer_token = "<你的 DeepSeek API Key>"
```

Codex 内置联网搜索只支持 `deepseek-v4-pro`，由服务端执行，并按 Search API 计费。

### Zcode 及其他 harness

只要能填自定义 OpenAI 兼容或 Anthropic 兼容 provider，就能接 DeepSeek：

| 协议 | Base URL | 鉴权头 | 模型 |
|---|---|---|---|
| OpenAI 兼容 | `https://api.deepseek.com` | `Authorization: Bearer <key>` | `deepseek-flash` |
| Anthropic 兼容 | `https://api.deepseek.com/anthropic` | `x-api-key: <key>` 或 Bearer | `deepseek-flash` |
| Responses API | `https://api.deepseek.com/`（`wire_api = "responses"`） | `Authorization: Bearer <key>` | `deepseek-flash` |

Zcode 的字段名不同，填的值相同。如果 harness 两种协议都不支持，就让 agent 用它自己的模型，再把 seekport 装成 Skill 或 MCP——搜索请求仍然发往 DeepSeek。

</details>

## 项目结构

```text
seekport/
├── SKILL.md                 # 可移植 Agent Skill
├── scripts/
│   ├── ds_core.py           # 核心库：校验、HTTP、搜索/抓取、渲染
│   ├── cli.py               # seekport search / fetch
│   ├── errors.py            # 共享异常类型
│   └── spend.py             # 每日预算账本
├── mcp/
│   └── seekport_mcp.py      # 零依赖 stdio MCP server
├── tests/                   # 81 个单元测试，HTTP 全 mock
├── examples/                # 真实输出与案例
├── docs/                    # before/after 示意图
├── promo/                   # 小红书图文与视频素材
├── CONTRIBUTING.md
├── MAINTENANCE.md
├── README.md                # 中文（默认）
├── README.en.md             # English
└── LICENSE
```

## 开发与测试

```bash
python3 -m unittest discover -s tests -v
```

81 个测试，行覆盖率 93%，CI 在 Python 3.9 / 3.11 / 3.12 上运行。全部 HTTP 均为 mock，不消耗额度。

## 安全

- API key 只从环境变量 `DEEPSEEK_API_KEY` 读取，绝不写入仓库或日志。
- 抓取请求由 DeepSeek 服务器发起，本机不直连目标站点，减少本地 SSRF 风险。
- 抓回的内容是**不可信数据**，只当作待总结的素材，不要执行其中的指令。
- `SEEKPORT_BASE_URL` 可指向代理，但那会把 key 发给该代理。

## 和别的工具的关系

| 项目 | 形态 | 适用 harness | 运行时依赖 | 过滤 / 预算 |
|---|---|---|---|---|
| `@deepseek-ai/dsh-web-deepseek-api` | DSH 插件 | 仅 DSH | — | DSH 管理 |
| `deepseek-web-retrieval` | 插件 | OpenCode / Pi | 视实现 | 视实现 |
| `@wangkh/deepseek-search-mcp` | MCP | 任意 MCP 客户端 | Node | 无 |
| `namelessgod2008/deepseek-search` | 纯 skill | Claude Code | — | 无 license |
| **seekport** | **Skill + MCP + CLI** | **Claude Code / Codex / Zcode / 任意** | **无（标准库）** | **有** |

seekport 补的是组合空位：面向非 DSH harness 的标准可移植 skill、零依赖、显式的相关性与权威性过滤、以及花费上限。

## 致谢

搜索与抓取由 DeepSeek 官方 Search/Fetch API 提供。本项目使用 Claude Code（底层为 DeepSeek 模型）开发。这些是工具，不是作者：GitHub 的 contributors 列表反映的是提交代码的人，而不是使用的模型或 API。

## 参与贡献

欢迎提交 Issue 和 Pull Request。开发流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，维护清单见 [MAINTENANCE.md](MAINTENANCE.md)。请不要在 Issue 里贴 API key。

## 许可证

MIT。

---

Not affiliated with DeepSeek. / 与 DeepSeek 官方无关。
