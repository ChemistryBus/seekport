# Promo kit

Xiaohongshu (小红书) carousel for seekport: 6 pages, 1080 × 1440 (3:4).

## Files

| Path | What it is |
|---|---|
| `pages/*.html` | Page content; edit these |
| `style.css` | Shared design tokens and layout |
| `render.py` | Renders pages to `out/*.png` with headless Chrome |
| `note.md` | Post copy, titles, hashtags, publishing checklist |
| `out/` | Generated PNGs (gitignored) |

## Render

```bash
python3 render.py            # all six pages
python3 render.py --only 04  # one page
```

Requires Google Chrome or Chromium. No Python packages to install.
The script looks for Chrome in the usual macOS, Linux, and Windows paths; edit
`CHROME_CANDIDATES` in `render.py` if yours is elsewhere.

## Edit

- Text lives in `pages/*.html`. Change it there, not in the PNG.
- Colors, type scale, and spacing live in `style.css` (`:root` at the top).
- After editing, rerun `render.py`.
- The generated `out/*.png` files are ignored by git so the public repo stays
  small; the HTML/CSS source is versioned.

## Page order

1. `01-cover` — hook and a real search command
2. `02-problem` — the WebFetch failure and stale results
3. `03-how` — Agent → Skill/MCP → seekport → DeepSeek API
4. `04-search` — three concrete search examples
5. `05-syntax` — search operator cheat sheet
6. `06-who` — audience and GitHub link
