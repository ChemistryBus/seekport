# seekport

**Bridge DeepSeek's official Search/Fetch API to Claude Code, Codex, Zcode, and any other agent harness.**

`seekport` is a thin, zero-dependency bridge to DeepSeek's official
[Search and Fetch APIs](https://api-docs.deepseek.com/zh-cn/guides/search). It
gives an agent real web search and page fetch even when the harness's built-in
`WebFetch` or search is blocked. It exists for one concrete failure:

> Unable to verify if domain is safe to fetch.

That is what Claude Code's `WebFetch` says when it runs through a third-party
gateway it cannot validate. On the same setup, the harness usually has no usable
built-in web search either. `seekport` gives the agent two plain commands that
work anywhere Python 3 runs:

```bash
python3 scripts/cli.py search "DeepSeek V4 release" --md
python3 scripts/cli.py fetch  "https://api-docs.deepseek.com/zh-cn/guides/search" --md
```

## Why you need this: a real case

Ask an agent: *“How much does DeepSeek's Search API cost, and what are its QPS
limits?”* Behind a gateway, `WebFetch` on the official docs fails
(`Unable to verify if domain is safe to fetch`). Search returns secondary
articles — two of the top three still claimed **$0.75 / 1,000 and 5 QPS**.
Fetching the primary source showed **¥5 / 1,000, Search 100 QPS / Fetch 25 QPS**.

seekport closes that loop: search for candidates, fetch the authoritative page,
cite it. One search + one fetch costs **¥0.01**. Full transcript:
[examples/case-study.md](examples/case-study.md).

## What you get

- **Zero runtime dependencies** — Python 3.9+ standard library only.
- **One core, two shapes** — a portable Agent Skill (`SKILL.md`) and a stdio
  MCP server (`deepseek_search`, `deepseek_fetch`).
- **Filtering before the model sees results** — `rerank_score` and `authority`
  thresholds cut noise and token cost.
- **A cost guardrail** — optional daily spend cap (`SEEKPORT_BUDGET`), and retry
  behaviour that never duplicates a successful paid call.
- **Readable core** — `scripts/ds_core.py` is 290 lines you can read in five
  minutes.

## What it is not

- Not a general-purpose search engine.
- Not a replacement for DeepSeek Harness's official
  [`@deepseek-ai/dsh-web-deepseek-api`](https://www.npmjs.com/package/@deepseek-ai/dsh-web-deepseek-api).
  If you use DSH, use the official package.
- Not a third-party SDK wrapper. There is no SDK; it speaks the documented JSON
  API directly.

## Quick start

```bash
git clone https://github.com/<you>/seekport.git
cd seekport
export DEEPSEEK_API_KEY=sk-...        # your existing DeepSeek key

python3 scripts/cli.py search "DeepSeek V4 release" --count 5 --md
python3 scripts/cli.py fetch "https://api-docs.deepseek.com/zh-cn/api/search/" --md
```

Requirements: Python 3.9+. No `pip install` step.

## Step 0: point the agent at DeepSeek (optional)

seekport only needs `DEEPSEEK_API_KEY`; the agent itself does not have to run on
DeepSeek. But the failure seekport solves usually appears when it does. These
are the official DeepSeek settings.

### Claude Code

DeepSeek exposes an Anthropic-compatible endpoint
([official guide](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code)):

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<your DeepSeek API key>
export ANTHROPIC_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-flash
```

Then run `claude` in your project. The official page also sets
`CLAUDE_CODE_EFFORT_LEVEL=max` and `CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432`;
both are optional tuning, not required to connect.

With the official endpoint, Claude Code's server-side **Web Search** is
available; DeepSeek bills each search as a Search API request plus the extra
model tokens used to summarise the results. seekport remains useful when you go
through a **third-party gateway** that does not expose that server-side tool, or
when you want explicit `site:` / `lang:` filters, relevance thresholds, and a
local spend cap.

### Codex

DeepSeek natively supports the Responses API
([official guide](https://api-docs.deepseek.com/quick_start/agent_integrations/codex)).
The guide provides a one-command setup script; the manual equivalent is a
`~/.codex/models.json` model catalog plus `~/.codex/config.toml`:

```toml
model = "deepseek-flash"
model_provider = "deepseek"
preferred_auth_method = "apikey"
forced_login_method = "api"
model_reasoning_effort = "high"
web_search = "disabled"          # "live" only with deepseek-v4-pro
model_catalog_json = "~/.codex/models.json"

[model_providers.deepseek]
name = "deepseek"
base_url = "https://api.deepseek.com/"
wire_api = "responses"
experimental_bearer_token = "<your DeepSeek API key>"
```

Codex's built-in web search only works with `deepseek-v4-pro`, is executed
server-side, and is billed as Search API requests.

### Zcode and other harnesses

Any harness that accepts a custom OpenAI- or Anthropic-compatible provider works:

| Protocol | Base URL | Auth header | Model |
|---|---|---|---|
| OpenAI-compatible | `https://api.deepseek.com` | `Authorization: Bearer <key>` | `deepseek-flash` |
| Anthropic-compatible | `https://api.deepseek.com/anthropic` | `x-api-key: <key>` or Bearer | `deepseek-flash` |
| Responses API | `https://api.deepseek.com/` with `wire_api = "responses"` | `Authorization: Bearer <key>` | `deepseek-flash` |

Zcode's field names differ, but the values are the same. If the harness supports
neither protocol, keep the agent on its own model and install seekport as a
Skill or MCP server — the search calls still go to DeepSeek.

## Install as an Agent Skill

The repository root **is** the skill directory: `SKILL.md` plus `scripts/`.

**Claude Code**

```bash
git clone https://github.com/<you>/seekport.git ~/seekport
ln -s ~/seekport ~/.claude/skills/seekport
```

Restart the session, then the skill is available as `seekport`.

**Codex, Zcode, and other harnesses**

There is no harness-specific packaging: the skill is Markdown plus a Python
script. Either point the harness at `SKILL.md`, or add three lines to your
`AGENTS.md` / project instructions:

```markdown
## Web search
When WebFetch is blocked or no web search exists, use seekport:
`python3 /path/to/seekport/scripts/cli.py search "<query>" --md`
Read /path/to/seekport/SKILL.md for flags and error handling.
```

## Install as an MCP server

```bash
claude mcp add seekport -- python3 /absolute/path/to/seekport/mcp/seekport_mcp.py
```

Or add it to an MCP config file:

```json
{
  "mcpServers": {
    "seekport": {
      "command": "python3",
      "args": ["/absolute/path/to/seekport/mcp/seekport_mcp.py"],
      "env": { "DEEPSEEK_API_KEY": "sk-..." }
    }
  }
}
```

**Trade-off:** MCP tools are always resident in the model's context, so their
schemas cost tokens on every turn. The Skill shape loads only when used. Prefer
the Skill unless the harness has no skill loader or you need always-on tools.
The MCP server is hand-written JSON-RPC over stdio — no `mcp` SDK, no
dependencies.

## Skill or MCP: which should I install?

Both shapes call the same `search()` / `fetch()` code. The difference is how the
agent discovers and invokes them.

| | Agent Skill | MCP server |
|---|---|---|
| Install | copy/symlink the repo into the harness's skills directory | register a command in the harness's MCP config |
| Discovery | loaded on demand when the task matches `SKILL.md` | every tool schema is listed to the model on every turn |
| Context cost | ~0 tokens until used | schemas + descriptions occupy context every turn |
| Invocation | the model runs `python3 .../cli.py` in a shell | the harness calls `tools/call` over stdio |
| Needs shell access | yes | no |
| Permissions | the shell's permission rules | the harness's MCP tool permissions |
| Works on | Claude Code, Codex, Zcode, any harness that can run a command | any MCP client |
| Main risk | the model may not notice the skill if its description doesn't match the task | permanent context cost, and duplicate tools can confuse selection |

**Choose Skill** when the harness can run shell commands and you want the lowest
context cost. This is the default choice for Claude Code and Codex.

**Choose MCP** when the harness cannot run arbitrary shell commands, or when you
want the model to always see a typed tool interface.

**Pick one per harness.** Installing both duplicates tools and pays the MCP
context cost for no benefit. They do not conflict technically, but they do
compete during tool selection.

## Usage

### Search

```bash
# JSON (stable contract, good for scripts and agents)
python3 scripts/cli.py search "deepseek v4"

# Markdown (fewer tokens, good for reading)
python3 scripts/cli.py search "deepseek v4" --count 5 --md

# Only highly authoritative results
python3 scripts/cli.py search "clinical trial endpoints" --min-authority 3 --md

# Full page text included (larger; usually unnecessary)
python3 scripts/cli.py search "transformer scaling laws" --content --count 3
```

JSON output:

```json
{
  "query": "deepseek v4",
  "total": 10,
  "returned": 6,
  "results": [
    {
      "rerank_score": 2.4,
      "title": "DeepSeek V4 model released",
      "url": "https://example.com/deepseek-v4",
      "snippet": "Short excerpt, 100-200 chars.",
      "summary": "Longer summary, 600-800 chars, intended for the model.",
      "content": "",
      "site_name": "Example News",
      "site_icon": "https://example.com/favicon.ico",
      "date": "2026-06-01T00:00:00+00:00",
      "authority": 3
    }
  ]
}
```

`total` is the API's count; `returned` is what survived filtering.

### Fetch

```bash
python3 scripts/cli.py fetch "https://example.com/article" --md
# -> { "url": ..., "title": ..., "content": "<Markdown>" }
```

### Search operators

Passed through to DeepSeek unchanged; combine them in one query.

| Operator | Example | Meaning |
|---|---|---|
| `site:` | `deepseek site:github.com` | Restrict to a site; chain with `OR` |
| `-site:` | `deepseek -site:example.com` | Exclude a site |
| `"..."` | `"exact phrase"` | Exact phrase |
| `-` | `deepseek -广告` | Exclude a term |
| `-"..."` | `deepseek -"release notes"` | Exclude a phrase |
| `lang:` | `lang:zh,en` | Restrict language |
| `after:` | `after:2025` or `after:2025-01-01` | Published after |
| `before:` | `before:2026` or `before:2026-06-01` | Published before |

### Result fields

| Field | Meaning |
|---|---|
| `rerank_score` | 0–3, relevance + authority + freshness. **≥ 1.5 is good.** |
| `authority` | −1 unknown, 0–4. **≥ 3 is highly authoritative.** |
| `summary` | Usually 600–800 chars, sometimes longer (a real result was 2.3k); read this instead of fetching. |
| `snippet` | 100–200 chars; for display only. |
| `date` | RFC 3339 UTC, or `null` when unknown. |
| `content` | Full text, empty unless `need_content=true`. |

## Cost and limits

These numbers are from the official docs as of 2026-11-04. **Check the docs
before quoting them.**

| Item | Value |
|---|---|
| Search | **¥5 per 1,000 successful requests** |
| Fetch | **¥5 per 1,000 successful requests** |
| Approx. per call | ¥0.005 ≈ **$0.0007** |
| Billed when | HTTP 200 **and** non-empty results (Search) / content (Fetch) |
| Not billed | errors, timeouts, empty searches |
| `count` | Does not affect price, only result count |
| Rate limit | Search **100 QPS**, Fetch **25 QPS** per account |
| Fetch extra | Per-domain QPS limit, also returns 429 |

Notes:

- Search and Fetch are billed independently.
- DeepSeek's docs state that Search/Fetch calls made through server-side tool
  calls in DSH / Claude Code / Codex have been billed since
  2026-11-01 00:00 Beijing time. seekport is a direct API client, so it is
  billed the same way.
- Set `SEEKPORT_BUDGET=0.05` to cap daily spend at ¥0.05 (10 successful calls).
  The ledger is local, best-effort, and stored at
  `~/.cache/seekport/spend.log`.

## Why another DeepSeek search tool?

| Project | Shape | Harnesses | Runtime deps | Filtering / budget |
|---|---|---|---|---|
| `@deepseek-ai/dsh-web-deepseek-api` | DSH plugin | DSH only | — | DSH-managed |
| `deepseek-web-retrieval` | plugin | OpenCode / Pi | varies | varies |
| `@wangkh/deepseek-search-mcp` | MCP | any MCP client | Node | no |
| `namelessgod2008/deepseek-search` | skill only | Claude Code | — | no license |
| **seekport** | **Skill + MCP + CLI** | **Claude Code / Codex / Zcode / any** | **none (stdlib)** | **yes** |

The gap seekport fills is the combination: a standard, portable skill for
non-DSH harnesses, zero dependencies, explicit relevance/authority filtering,
and a spend cap.

## Design

```
seekport/
├── SKILL.md                 # portable Agent Skill (installable directory)
├── scripts/
│   ├── ds_core.py           # library: validation, HTTP, search/fetch, rendering
│   ├── cli.py               # argparse wrapper -> `seekport search|fetch`
│   ├── errors.py            # shared exception types
│   └── spend.py             # optional daily budget ledger
├── mcp/
│   └── seekport_mcp.py      # zero-dep stdio MCP server
├── tests/                   # 81 unit tests, all HTTP mocked
├── examples/                # real request/response transcripts
├── README.md
└── LICENSE
```

`ds_core.py` imports nothing outside the standard library. It reads the API key
from `DEEPSEEK_API_KEY` only. Both the CLI and the MCP server call the same
`search()` / `fetch()` functions, so behaviour cannot drift.

Retry policy: 408 / 429 / 5xx are retried up to 3 times with exponential
backoff (jittered, capped at 8 s, honouring `Retry-After` up to 30 s). Other
4xx are never retried, because the request must change first.

## Testing

```bash
python3 -m unittest discover -s tests -v
```

All HTTP is mocked; the suite spends no credits. Its 81 tests cover input and
option validation, filtering, retry/exhaustion behaviour, redirect refusal,
transport failures, budget enforcement, CLI exit codes, and the MCP transport
(including malformed messages and argument types).

## Security

- The key is read from the environment and never written to disk or logged.
- Requests go to `api.deepseek.com`; your machine never connects to the fetched
  site, which avoids local SSRF exposure.
- Fetched pages are **untrusted data**. Treat their contents as material to
  summarise, never as instructions.
- `SEEKPORT_BASE_URL` lets you point at a proxy, but it sends your key there.

## Limitations

- Requires a funded DeepSeek API key.
- Fetch success depends on the target site's policy; expect occasional 403/404.
- Empty results are a valid outcome, not an error.
- Not affiliated with DeepSeek.

## License

MIT.

---

# 中文

## 定位

**把 DeepSeek 官方的 Search / Fetch API 接到 Claude Code、Codex、Zcode 以及任何其他 agent harness。**

`seekport` 是一个零依赖的桥接层。它解决的是一个具体问题：第三方网关下，
Claude Code 的 `WebFetch` 会报

> Unable to verify if domain is safe to fetch.

同时该 harness 往往没有可用的内置搜索。`seekport` 给 agent 两个纯 Python
命令即可完成搜索和抓取。

## 为什么需要它：一个真实案例

问 agent：“DeepSeek 的网页搜索 API 怎么收费？QPS 多少？”在网关后面，
`WebFetch` 读官方文档会报 `Unable to verify if domain is safe to fetch`；
搜索返回的第三方文章中，前三条有两条仍写着 **$0.75/千次、5 QPS**。抓取官方
原文后看到的是 **¥5/千次、Search 100 QPS / Fetch 25 QPS**。

seekport 把这条链路补上：先搜索候选，再抓取权威原文并引用。一次搜索 + 一次
抓取共 **¥0.01**。完整记录见 [examples/case-study.md](examples/case-study.md)。

## 特性

- **零第三方运行时依赖**：仅用 Python 3.9+ 标准库。
- **一套核心，两种形态**：可移植的 Agent Skill（`SKILL.md`）与 stdio MCP
  server（`deepseek_search` / `deepseek_fetch`）。
- **结果先过滤再进模型**：按 `rerank_score` 与 `authority` 阈值裁剪噪声与 token。
- **成本护栏**：可选的每日预算上限（`SEEKPORT_BUDGET`）。
- **核心可读**：`scripts/ds_core.py` 290 行，5 分钟能读完。

## 不做什么

- 不做通用搜索引擎。
- 不替代 DSH 官方包 `@deepseek-ai/dsh-web-deepseek-api`；用 DSH 就用官方实现。
- 不封装第三方 SDK，直接调用文档化 JSON API。

## 快速开始

```bash
git clone https://github.com/<you>/seekport.git
cd seekport
export DEEPSEEK_API_KEY=sk-...          # 复用现有 DeepSeek key

python3 scripts/cli.py search "DeepSeek V4 模型发布" --count 5 --md
python3 scripts/cli.py fetch "https://api-docs.deepseek.com/zh-cn/api/search/" --md
```

不需要 `pip install`。

## 第 0 步：把 agent 后端接到 DeepSeek（可选）

seekport 只要求 `DEEPSEEK_API_KEY`，agent 本身不一定要跑在 DeepSeek 上。但
seekport 要解决的那个报错，通常正是切到 DeepSeek 之后出现的。以下是 DeepSeek
官方配置。

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

然后在项目目录执行 `claude`。官方页面还设置了
`CLAUDE_CODE_EFFORT_LEVEL=max` 和 `CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432`；
这两项是可选的调优参数，不影响能否连通。

使用官方端点时，Claude Code 的**服务端 Web Search** 可用；DeepSeek 会把每次
搜索按 Search API 计费，并为总结搜索结果额外消耗模型 token。seekport 仍然有用的
场景是：走**第三方网关**、该网关没有暴露服务端搜索工具，或你需要显式使用
`site:` / `lang:` 过滤、相关性阈值和本地花费上限。

### Codex

DeepSeek 原生支持 Responses API（[官方接入文档](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/codex)）。
官方给了一键配置脚本；手动配置需要 `~/.codex/models.json` 模型目录和
`~/.codex/config.toml`：

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

Zcode 的字段名不同，填的值相同。如果 harness 两种协议都不支持，就让 agent 用它
自己的模型，再把 seekport 装成 Skill 或 MCP——搜索请求仍然发往 DeepSeek。

## 安装为 Skill

仓库根目录就是 skill 目录（`SKILL.md` + `scripts/`）。

**Claude Code**

```bash
ln -s ~/seekport ~/.claude/skills/seekport
```

**Codex / Zcode / 其他 harness**

没有 harness 专用打包：它只是 Markdown 加一个 Python 脚本。让 harness 读取
`SKILL.md`，或在 `AGENTS.md` 里加三行指向它即可。示例见英文部分的
"Install as an Agent Skill"。

## 安装为 MCP

```bash
claude mcp add seekport -- python3 /绝对路径/seekport/mcp/seekport_mcp.py
```

**取舍**：MCP 工具会常驻模型上下文，schema 每轮都消耗 token；Skill 只在被调用时
加载。除非 harness 没有 skill 加载器，否则优先用 Skill。MCP server 是手写的
stdio JSON-RPC，不依赖 `mcp` SDK。

## Skill 还是 MCP？该装哪个

两种形态调用的是同一份 `search()` / `fetch()` 代码，区别在于 agent 如何发现和
调用它们。

| | Agent Skill | MCP server |
|---|---|---|
| 安装 | 把仓库复制/软链到 harness 的 skills 目录 | 在 harness 的 MCP 配置里注册命令 |
| 发现方式 | 任务匹配 `SKILL.md` 描述时按需加载 | 每轮对话都把工具 schema 列给模型 |
| 上下文成本 | 未使用前约 0 token | schema 和描述每轮都占上下文 |
| 调用方式 | 模型在 shell 里执行 `python3 .../cli.py` | harness 通过 stdio 调 `tools/call` |
| 需要 shell 权限 | 是 | 否 |
| 权限体系 | shell 命令权限 | harness 的 MCP 工具权限 |
| 适用 | Claude Code、Codex、Zcode 等能执行命令的 harness | 任意 MCP 客户端 |
| 主要风险 | 描述与任务不匹配时，模型可能想不起这个 skill | 常驻上下文成本；重复工具会干扰工具选择 |

**选 Skill**：harness 能跑 shell 命令，且你希望上下文成本最低。Claude Code 和
Codex 默认选这个。

**选 MCP**：harness 不能执行任意 shell 命令，或你希望模型始终看到一个带类型定义的
工具接口。

**每个 harness 只装一种。** 两种都装会产生重复工具，并白白支付 MCP 的上下文成本；
技术上不冲突，但会在工具选择时互相竞争。

## 用法

```bash
# 默认 10 条，自动丢弃 rerank_score < 1.5，输出 JSON
python3 scripts/cli.py search "deepseek v4"

# Markdown 输出，token 更省
python3 scripts/cli.py search "deepseek v4" --count 5 --md

# 只要高权威结果
python3 scripts/cli.py search "临床 试验 终点" --min-authority 3 --md

# 组合搜索语法
python3 scripts/cli.py search 'deepseek site:github.com OR site:huggingface.co lang:zh after:2025'
```

参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--count` | 10 | 返回条数 1–50，**不影响单次计费** |
| `--min-rerank` | 1.5 | 低于该相关性分数的结果丢弃；`0` 表示不过滤 |
| `--min-authority` | 关闭 | 低于该权威性的结果丢弃；`3`–`4` 为极权威 |
| `--ori-question` | 关闭 | 用户原始问题，帮助理解搜索意图 |
| `--content` | 关闭 | 让 API 返回网页正文（更大更慢） |
| `--md` | 关闭 | 输出 Markdown 而非 JSON |

## 成本与限速（官方文档，2026-11-04）

| 项目 | 数值 |
|---|---|
| Search | **每 1,000 次成功请求 ¥5** |
| Fetch | **每 1,000 次成功请求 ¥5** |
| 单次约 | ¥0.005 ≈ **$0.0007** |
| 计费条件 | HTTP 200 **且** Search 结果非空 / Fetch 有正文 |
| 不计费 | 报错、超时、空搜索结果 |
| 限速 | Search **100 QPS**，Fetch **25 QPS**（按账号） |

`--count` 只改返回条数，不改价格。设置 `SEEKPORT_BUDGET=0.05` 可把每日花费
限制在 ¥0.05（10 次成功调用），账本位于 `~/.cache/seekport/spend.log`。

> 官方文档说明：通过 DSH / Claude Code / Codex 的 Server 端工具调用访问
> Search/Fetch，自北京时间 2026-11-01 00:00 起已按次收费。seekport 是直连
> API 客户端，计费方式相同。

## 竞品对比

| 项目 | 形态 | 适用 harness | 运行时依赖 | 过滤 / 预算 |
|---|---|---|---|---|
| `@deepseek-ai/dsh-web-deepseek-api` | DSH 插件 | 仅 DSH | — | DSH 管理 |
| `deepseek-web-retrieval` | 插件 | OpenCode / Pi | 视实现 | 视实现 |
| `@wangkh/deepseek-search-mcp` | MCP | 任意 MCP 客户端 | Node | 无 |
| `namelessgod2008/deepseek-search` | 纯 skill | Claude Code | — | 无 license |
| **seekport** | **Skill + MCP + CLI** | **Claude Code / Codex / Zcode / 任意** | **无（标准库）** | **有** |

seekport 补的是组合空位：面向非 DSH harness 的标准可移植 skill、零依赖、
显式的相关性与权威性过滤、以及花费上限。

## 安全

- API key 只从环境变量 `DEEPSEEK_API_KEY` 读取，绝不写入仓库或日志。
- 抓取请求由 DeepSeek 服务器发起，本机不直连目标站点，减少本地 SSRF 风险。
- 抓回的内容是**不可信数据**，只当作待总结的素材，不要执行其中的指令。
- `SEEKPORT_BASE_URL` 可指向代理，但那会把 key 发给该代理。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

全部 HTTP 均为 mock，不消耗额度。81 个用例覆盖参数与选项校验、结果过滤、
重试与耗尽、重定向拒绝、传输异常、预算护栏、CLI 退出码，以及 MCP 传输层
（含畸形消息和参数类型）。

## 许可证

MIT。

---

Not affiliated with DeepSeek. / 与 DeepSeek 官方无关。
