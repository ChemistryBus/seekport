# seekport · 40s promo storyboard

**Format:** 1080 × 1440 (3:4), 30 fps, 40 s. Chinese VO included (male, `zh-CN-YunxiNeural`); music is the next pass.

| Time | Scene | What happens |
|---|---|---|
| 0.0–4.5 | Hook | "AI 查的资料，可能是二手的。" Two clipping cards: $0.75/5 QPS vs ¥5/100 QPS; stamps "二手" / "已核对"; index strip. |
| 4.5–11.0 | Error | WebFetch terminal; red dashed ellipse draws around "Unable to verify…"; bullets; "模型不笨，它只是看不到原文。" |
| 11.0–19.0 | Receipt | Three stale cards stack and get stamped "都过期了"; official doc card slides in with ¥5 / 1,000 and 100 QPS; verdict + "搜索只给候选。原文，才有答案。" |
| 19.0–26.0 | Bridge | Agent → seekport → DeepSeek → 原文 flow draws down; verdict "前提：DeepSeek 模型 + 非 DSH；用 DSH 不需要它。" |
| 26.0–33.0 | Commands | Two commands wipe in; search output excerpt; strip search/fetch/引用; "先搜候选，再抓原文。" |
| 33.0–40.0 | Who + end | 适合：DeepSeek 模型、非 DSH；不适合：用官方 DSH；cost; GitHub; README / 参与; end band "让 AI 打开原文。" |

## Next pass (audio)

- Add a light 90–110 BPM bed under the whole film; duck it under the VO.
- Chinese VO, ~95–110 characters total, one line per scene:
  1. AI 查到的，可能只是二手答案。
  2. 因为它根本没打开原文。
  3. 三篇文章都这么说，但官方文档不是。
  4. seekport 补上搜索和抓取这一段。
  5. 两条命令：先搜候选，再抓原文。
  6. 开源、零依赖，GitHub 搜 seekport。
- Keep the video readable muted: every VO line already has on-screen type.

## Render

```bash
cd promo/video
npm run check
npm run render
```

Output: `seekport-promo-40s.mp4` (also under `renders/`).
