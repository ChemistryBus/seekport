# 小红书图文笔记 · seekport v2

9 张图，1080 × 1440（3:4）。**所有内容都在图里；正文只放话题标签。**

## 标题

**AI 查的资料，可能是二手的**

备选：

- 我给 Claude Code 接了个官方搜索
- AI 查资料，别再喂它二手答案
- 一个 WebFetch 报错，逼我写了个小工具

## 正文（直接复制，只有话题）

```
#ClaudeCode #DeepSeek #AI工具 #科研工具 #开源项目 #效率工具 #MCP #论文写作 #AI搜索 #独立开发 #科研日常 #博士生
```

## 第一条评论（自己发，可选）

```
GitHub 搜 ChemistryBus/seekport 就能找到。
README 有中英文两版，安装、搜索语法、错误处理都写了。
不是 DeepSeek 官方项目，是个人开源；有问题可以直接提 Issue。
```

## 图片顺序

| 顺序 | 文件 | 这一页讲什么 |
|---|---|---|
| 1 | `out/01-cover.png` | 封面：AI 查的资料，可能是二手的 |
| 2 | `out/02-problem.png` | WebFetch 报错的那一行 |
| 3 | `out/03-case.png` | 3 篇二手文章 vs 官方原文 |
| 4 | `out/04-how.png` | seekport 是一座小桥 |
| 5 | `out/05-commands.png` | 两条命令：search + fetch |
| 6 | `out/06-use-cases.png` | 四个真实查询 |
| 7 | `out/07-syntax.png` | 搜索语法小抄 |
| 8 | `out/08-install.png` | Skill / MCP 两种装法 |
| 9 | `out/09-who.png` | 适合谁、成本、GitHub |

## 设计说明

- 纸张 + 红线 + 侧边批注 + 剪报/胶带/印章，编辑部手记风。
- 没有 AI 插画、没有 3D 机器人、没有渐变光晕；所有“图”都是排版、终端窗口、文档卡片。
- 正文只放话题，是为了让用户把注意力留在图上；XHS 正文里的外链也容易限流。
- 代码示例用真实的 `python3 $CLI ...`，不写不存在的 `seekport` 可执行文件。

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
cd promo/xhs-v2
python3 render.py            # 全部 9 张
python3 render.py --only 03  # 只重出第 3 张
```

改文字：`pages/*.html`。改颜色/字号/间距：`style.css` 顶部的 `:root`。
需要本机有 Google Chrome 或 Chromium。
