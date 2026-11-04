# Case study: why seekport exists

**Question given to an agent:** “DeepSeek 的网页搜索 API 怎么收费？QPS 多少？”

This is a factual question whose answer changes. It is exactly where a blocked
`WebFetch` plus a stale search index produces a confident wrong answer.

## Before: WebFetch is blocked

```
WebFetch https://api-docs.deepseek.com/zh-cn/guides/search

→ Unable to verify if domain api-docs.deepseek.com is safe to fetch.
  This may be due to network restrictions or enterprise security policies
  blocking claude.ai.
```

The agent cannot open the primary source. Its web search returns secondary
articles. The top three results on 2026-11-04 said:

| # | Source | Claim |
|---|---|---|
| 1 | npmjs.com/package/dsh-web-search-pro | “$0.75 per 1,000 successful requests” |
| 2 | news.qiniu.com (2026-10-18) | “$0.75 / 千次成功请求”, “5 QPS” |
| 3 | github.com/ansellchen-boop/deepseek-search-tools | “每 1,000 次成功请求 5 元”, “QPS 各 5” |

Two of the three are stale. An agent that stops here tells the user
“$0.75 and 5 QPS” — wrong on both counts.

## After: search, then fetch the primary source

```bash
$ python3 scripts/cli.py search "DeepSeek Search API 计费 价格 QPS" --count 3 --md
## 1. dsh-web-search-pro - - Cost: Search and Fetch are each $0.75 ...
<https://www.npmjs.com/package/dsh-web-search-pro?activeTab=dependents#8>
NPM · 2026-10-26 · score 2.3335 · auth 3
...

## 2. DeepSeek 搜索 API 正式开放：每千次请求 $0.75，开发者如何接入？
<https://news.qiniu.com/archives/1792373734665#1>
七牛云 · 2026-10-18 · score 2.2985 · auth 3
...
```

The search gives candidates with dates and authority scores. It does not settle
the question.

```bash
$ python3 scripts/cli.py fetch "https://api-docs.deepseek.com/zh-cn/guides/search" --md
# 网页搜索与抓取
<https://api-docs.deepseek.com/zh-cn/guides/search>
...
## 计费
API | 计费单位 | 价格
Search | 每 1,000 次成功请求 | 5元
Fetch | 每 1,000 次成功请求 | 5元
...
API | QPS 限制
Search | 100
Fetch | 25
```

**Answer:** ¥5 per 1,000 successful requests, Search and Fetch billed
separately; Search 100 QPS, Fetch 25 QPS per account (official docs,
2026-11-04).

## Why this matters

- Search alone produced a confident, stale answer. Fetching the primary source
  corrected it.
- The agent can cite the URL, so the user can verify the claim.
- One search + one fetch costs **¥0.01** (2 × ¥0.005); empty results are free.
- `site:`, `lang:`, `after:` and the `rerank_score` / `authority` filters keep
  the candidate list small before the model reads it.

This is the workflow seekport is built for: **search for candidates, filter,
fetch the authoritative page, cite it** — in a harness where `WebFetch` cannot
do the last step.
