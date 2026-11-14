#!/usr/bin/env python3
"""Render the Xiaohongshu v2 pages to 1080x1440 PNGs with headless Chrome.

Usage:
  python3 render.py            # all pages
  python3 render.py --only 03  # one page

Edit pages/*.html and style.css, then rerun. Output goes to out/.
No third-party Python dependencies.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "pages"
DEFAULT_OUT = ROOT / "out"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if Path(candidate).exists():
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Render promo HTML pages to PNG.")
    parser.add_argument("--only", help="render one page by prefix, e.g. 03")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output directory")
    args = parser.parse_args()

    chrome = find_chrome()
    if not chrome:
        sys.exit(
            "Chrome or Chromium not found. Install Google Chrome, or add its path "
            "to CHROME_CANDIDATES in render.py."
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pages = sorted(PAGES.glob("*.html"))
    if args.only:
        pages = [page for page in pages if page.name.startswith(args.only)]
    if not pages:
        sys.exit("No matching pages in pages/.")

    for page in pages:
        target = out / f"{page.stem}.png"
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--font-render-hinting=none",
            f"--screenshot={target}",
            "--window-size=1080,1440",
            page.resolve().as_uri(),
        ]
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        size_kb = target.stat().st_size // 1024
        print(f"{target.name}  {size_kb} KB")

    print(f"\nDone: {out}")


if __name__ == "__main__":
    main()
