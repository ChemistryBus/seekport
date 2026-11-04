# Examples

Real transcripts produced on 2026-11-04 with a funded DeepSeek key. They are
recorded, not hand-written, so the output matches what the tool actually prints.

| File | Command |
|---|---|
| [`search.md`](search.md) | `python3 scripts/cli.py search "DeepSeek Search API need_content" --count 5 --md` |
| [`fetch.md`](fetch.md) | `python3 scripts/cli.py fetch "https://api-docs.deepseek.com/zh-cn/guides/search" --md` |
| [`case-study.md`](case-study.md) | before/after: blocked `WebFetch` vs. search + fetch the primary source |

Regenerate them with:

```bash
export DEEPSEEK_API_KEY=sk-...

python3 ../scripts/cli.py search "DeepSeek Search API need_content" \
  --count 5 --md > search.md

python3 ../scripts/cli.py fetch \
  "https://api-docs.deepseek.com/zh-cn/guides/search" --md > fetch.md
```

Each request costs ¥0.005 (≈ $0.0007). The API key is never stored in this
directory or in the transcripts.
