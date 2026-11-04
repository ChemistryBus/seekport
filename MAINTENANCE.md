# 维护清单

这份清单写给项目维护者，不需要编程背景。所有命令都在项目目录执行：

```bash
cd "/Users/wubolong/Documents/Claude/Github Seekport"
```

## 每周 5 分钟

- [ ] 打开 [Issues](https://github.com/ChemistryBus/seekport/issues)，回复或关闭。
- [ ] 打开 [Actions](https://github.com/ChemistryBus/seekport/actions)，确认最近一次 `tests` 是绿色。
- [ ] 如果有 Pull Request，先让 Claude 看一遍，再决定是否 Merge。

## 每月 10 分钟

- [ ] 看一眼 DeepSeek 的[计费与限速文档](https://api-docs.deepseek.com/zh-cn/guides/search)有没有变。
- [ ] 执行 `git pull`，把远端更新拉到本地。
- [ ] 执行 `python3 -m unittest discover -s tests`，确认 81 个测试通过。
- [ ] 检查 README 里的价格、QPS、模型名是否仍然准确。

## 修改内容

- **改文字**：在 GitHub 打开 `README.md` 或 `README.zh-CN.md`，点右上角铅笔，改完点 **Commit changes**。
- **改代码 / 加功能**：直接告诉 Claude 要改什么。改完测试后会提交并推送。
- **不要在网页上直接改** `scripts/` 或 `mcp/` 下的代码，除非你确定自己在做什么。

## 安全

- 不要把 API key 贴进 Issue、README、代码或截图。
- 怀疑 key 泄露：在 [DeepSeek 控制台](https://platform.deepseek.com/api_keys)删除它，生成新 key，然后更新：

  ```bash
  printf "export DEEPSEEK_API_KEY='%s'\n" 'sk-你的新key' > ~/.config/seekport/env
  chmod 600 ~/.config/seekport/env
  ```

- 不要碰 **Settings → Danger Zone → Delete this repository**。

## 发布新版本

```bash
git tag -a v0.1.1 -m "seekport v0.1.1"
git push origin v0.1.1
gh release create v0.1.1 --title "v0.1.1" --notes "这一版改了什么"
```

## 出问题时

- **测试红了**：把 Actions 里的报错复制给 Claude。
- **改坏了想回退**：告诉 Claude“回退到上一个版本”，不要自己执行 `git reset --hard`。
- **本地 Skill 不更新**：在项目目录 `git pull`，然后重启 Claude Code。
- **Skill 报 401**：key 失效了，按上面的步骤换 key。

## 文件在哪里

| 文件 | 作用 |
|---|---|
| `README.md` / `README.zh-CN.md` | 项目主页（英 / 中） |
| `SKILL.md` | Agent Skill 说明 |
| `scripts/ds_core.py` | 核心库 |
| `scripts/cli.py` | 命令行 |
| `mcp/seekport_mcp.py` | MCP server |
| `tests/` | 自动测试 |
| `examples/` | 真实输入输出与案例 |
| `docs/seekport-flow.svg` | README 里的示意图 |
| `.github/workflows/test.yml` | 每次 push 自动跑测试 |
