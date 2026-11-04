# 小红书图文笔记（6 张）

图片在 `promo/out/`，按 `01 → 06` 顺序上传。

## 标题（三选一）

1. **我给 Claude Code 加了个搜索**（推荐，口语、有点击欲）
2. Claude Code 联网搜索方案（关键词清楚）
3. 让 AI 查到官方原文（科研党视角）

小红书标题上限约 20 字，以上都在范围内。

## 正文（可直接复制）

```
最近用 Claude Code 跑 DeepSeek，遇到一个很烦的问题：
WebFetch 老是报
“Unable to verify if domain is safe to fetch”

第三方网关下，内置搜索也用不了，
查期刊指南、官方文档只能靠猜，或者引用二手文章。

于是我写了个小工具：seekport
把 DeepSeek 官方的 Search / Fetch API
接到 Claude Code、Codex、Zcode 这些 agent 上。

怎么搜？3 个我常用的例子：

1️⃣ 查期刊投稿指南
seekport search "Nutrients author guidelines site:mdpi.com" --md

2️⃣ 查官方 API 文档
seekport search "DeepSeek pricing site:api-docs.deepseek.com" --md

3️⃣ 查最新进展
seekport search "exercise metabolism after:2025 lang:en" --md

语法和网页搜索一样：
site: / -site: / "精确短语" / -词 / lang:zh,en / after:2025 / before:2026

搜到候选后，想引用原文：
seekport fetch "https://..." --md

安装二选一：
· Skill：放进 ~/.claude/skills
· MCP：deepseek_search / deepseek_fetch

几个特点：
✅ 零依赖，纯 Python 标准库
✅ 按 rerank_score / authority 过滤
✅ 429 / 5xx 自动重试
✅ 每日预算上限
✅ MIT 开源

成本：¥5 / 1000 次成功请求，约 ¥0.005 一次；空结果不计费。

GitHub 搜：ChemistryBus/seekport
（个人项目，不是 DeepSeek 官方，欢迎提 Issue）
```

## 第一条评论（自己发）

```
GitHub 搜 ChemistryBus/seekport 就能找到。
README 有中英文两版，安装、搜索语法、错误处理都写了。
访问 GitHub 需要正常的网络条件；打不开可以留言，我发你 README 截图。
```

## 话题标签

```
#ClaudeCode #DeepSeek #AI工具 #科研工具 #开源 #效率工具 #论文写作 #MCP #独立开发
```

## 图片顺序

| 顺序 | 文件 | 内容 |
|---|---|---|
| 1 | `01-cover.png` | 封面：让 Claude Code 用上 DeepSeek 的联网搜索 |
| 2 | `02-problem.png` | 问题：WebFetch 报错 + 二手文章 vs 官方原文 |
| 3 | `03-how.png` | 原理：Agent → Skill/MCP → seekport → DeepSeek API |
| 4 | `04-search.png` | **怎么搜：3 个具体例子 + fetch** |
| 5 | `05-syntax.png` | **搜索语法小抄** |
| 6 | `06-who.png` | 适合谁 + GitHub 地址 |

## 发布建议

- **封面**用第 1 张，标题用“我给 Claude Code 加了个搜索”。
- **正文里不要放外链**，小红书对外链有限流；用“GitHub 搜 ChemistryBus/seekport”代替。
- 发布时间：工作日 20:00–22:00，或周末上午。
- 有人问“和官方有什么区别”，可以回：
  “官方 DSH 用户不需要它；它主要给走第三方网关、或者用 Codex / Zcode 的人。”
- 有人问“收费吗”，可以回：
  “工具本身 MIT 免费；DeepSeek 的搜索/抓取 API 按次收费，约 ¥0.005 一次，空结果不计费。”

## 发之前检查

- [ ] 价格和 QPS 以官方文档为准：<https://api-docs.deepseek.com/zh-cn/guides/search>
- [ ] 不写“最强”“神器”“一键”“永久免费”这类夸张词。
- [ ] 不承诺“已有多少人使用”（项目刚发布，没有这个数据）。
- [ ] 不把测试 key 或任何 key 截图发出去。
- [ ] 正文约 800 字，低于小红书 1000 字上限。
