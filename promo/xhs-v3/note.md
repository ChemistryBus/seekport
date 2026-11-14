# 小红书图文笔记 · seekport v3（少留白版）

9 张图，1080 × 1440（3:4）。**所有内容都在图里；正文只放话题标签。**

## 这条笔记到底在说什么（给你自己看的）

- **场景**：你在用 DeepSeek 模型，但走的是第三方网关（Claude Code / Codex / Zcode 等中转）。
- **为什么自带搜索用不上**：DeepSeek 的联网搜索只在它自己的入口里（App / 网页 / DSH / 官方 endpoint）；走第三方网关时，它不会跟过来。
- **问题**：这个 harness 里 WebFetch 可能报 `Unable to verify if domain is safe to fetch`，内置搜索也不可用。
- **后果**：Agent 只能看搜索摘要，打不开官方原文。
- **例子**：三篇二手文章都说 5 QPS，官方原文写 100 QPS，差 20 倍。
- **seekport 做什么**：补上 search + fetch。先搜候选，再抓官方原文，引用 URL。
- **安装**：不用手动装，直接对 Agent 说“帮我装 seekport”；前提是 `DEEPSEEK_API_KEY` 已配置、账户有余额（Search/Fetch 按次计费）。
- 一句话：不是 DeepSeek 不会搜，是它不替你那个入口搜；seekport 把官方 Search/Fetch API 接过来。

## 标题

**DeepSeek自带搜索，为什么用不上？**

备选：

- DeepSeek模型，搜不了网？
- DeepSeek模型，第三方网关怎么搜？
- DeepSeek自带搜索，为啥用不上

## 正文（直接复制，只有话题）

```
#DeepSeek #DeepSeek模型 #AI搜索 #AI工具 #AI编程 #MCP #开源项目 #效率工具 #程序员 #科研工具
```

## 第一条评论（自己发，可选）

```
GitHub 搜 ChemistryBus/seekport 就能找到。
README 有中英文两版，安装、搜索语法、错误处理都写了。
注意：它是给“用 DeepSeek 模型、但走第三方网关”的人；
用 DeepSeek 官方入口 / DSH 直接用官方搜索，不需要装。
不是 DeepSeek 官方项目，是个人开源；有问题可以直接提 Issue。
```

## 图片顺序

| 顺序 | 文件 | 这一页讲什么 |
|---|---|---|
| 1 | `out/01-cover.png` | 封面：DeepSeek 自带搜索为什么用不上？→ 第三方网关 → seekport 补上 search + fetch |
| 2 | `out/02-problem.png` | WebFetch 报错的那一行 |
| 3 | `out/03-case.png` | 三篇二手文章 vs 官方原文：5 QPS vs 100 QPS |
| 4 | `out/04-how.png` | seekport 补上 search + fetch |
| 5 | `out/05-commands.png` | 两条命令：search + fetch |
| 6 | `out/06-use-cases.png` | 四个真实查询 |
| 7 | `out/07-syntax.png` | 搜索语法小抄 |
| 8 | `out/08-install.png` | 安装：自然语言让 Agent 装；前提 key 已配置 + 账户有余额 |
| 9 | `out/09-who.png` | 适合谁、成本、GitHub |

## 设计说明

- 纸张 + 红线 + 侧边批注 + 剪报/胶带/印章，编辑部手记风。
- 没有 AI 插画、没有 3D 机器人、没有渐变光晕；所有“图”都是排版、终端窗口、文档卡片。
- 正文只放话题，是为了让用户把注意力留在图上；XHS 正文里的外链也容易限流。
- v3 在每页底部加了一条“信息带”（报错翻译 / 时间线 / 验证步骤 / 常见问题），把留白填成有用信息，而不是装饰。
- 代码示例用真实的 `python3 $CLI ...`，不写不存在的 `seekport` 可执行文件。
- 安装页改成 agent-native：先给一句自然语言指令，再写前提（key + 余额）；手动命令只作为小字备选。
- 前提写在封面右上角、第 2 页右上角、第 4 页的“前提”行、第 9 页的 kicker 和“适合”第一条：**用 DeepSeek 模型、但走第三方网关，才需要 seekport**；用 DeepSeek 官方入口 / DSH 直接用官方搜索，不需要装。
- 叙事顺序：封面先回答“DeepSeek 自带搜索为什么用不上”（因为它只在官方入口里，第三方网关不会跟过来）；第 2 页讲 harness 缺 fetch；第 3 页用三篇二手文章做证据；第 4 页展开桥。seekport 不再第 4 页才出现。
- 封面不再用价格对比：改成“没有 seekport：WebFetch ✗ / 搜索 ✗” vs “有 seekport：search + fetch ✓ / 打开原文”。价格从第 3 页也拿掉了，只留 5 QPS vs 100 QPS。

## 发之前检查

- [ ] 9 张图按 `01 → 09` 顺序上传。
- [ ] 标题用“AI 查的资料，可能是二手的”。
- [ ] 正文只放话题标签，不加大段说明。
- [ ] 第一条评论再放 GitHub 关键词，正文不放外链。
- [ ] 价格与 QPS 以官方文档为准（核对日期：2026-11-11）。
- [ ] 不写“最强”“神器”“一键”“永久免费”这类夸张词。
- [ ] 不承诺使用人数；项目刚发布，没有这个数据。
- [ ] 不把测试 key 或任何 key 截图发出去。
- [ ] 发布时间：工作日 20:00–22:00，或周末上午。

## 重新出图

```bash
cd promo/xhs-v3
python3 render.py            # 全部 9 张
python3 render.py --only 03  # 只重出第 3 张
```

改文字：`pages/*.html`。改颜色/字号/间距：`style.css` 顶部的 `:root`。
需要本机有 Google Chrome 或 Chromium。
