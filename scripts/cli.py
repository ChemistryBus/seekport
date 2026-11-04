#!/usr/bin/env python3
"""seekport command line interface. Thin wrapper around ds_core."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ds_core as core


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="seekport",
        description="Web search and page fetch through DeepSeek's Search/Fetch API.",
    )
    parser.add_argument("--version", action="version", version=f"seekport {core.__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="search the web")
    search.add_argument("query")
    search.add_argument("--count", type=int, default=core.DEFAULT_COUNT,
                        help="1-50, default 10")
    search.add_argument("--min-rerank", type=float, default=core.DEFAULT_MIN_RERANK,
                        help="drop results below this score; 0 keeps everything")
    search.add_argument("--min-authority", type=int, default=None,
                        help="drop results below this authority; 3+ is authoritative")
    search.add_argument("--ori-question", default=None, help="the user's original question")
    search.add_argument("--content", action="store_true", help="also return full page text")
    search_format = search.add_mutually_exclusive_group()
    search_format.add_argument("--md", action="store_true", help="print Markdown instead of JSON")
    search_format.add_argument("--json", action="store_true", help="print JSON (the default)")

    fetch = sub.add_parser("fetch", help="fetch one page as Markdown")
    fetch.add_argument("url")
    fetch_format = fetch.add_mutually_exclusive_group()
    fetch_format.add_argument("--md", action="store_true", help="print Markdown instead of JSON")
    fetch_format.add_argument("--json", action="store_true", help="print JSON (the default)")
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "search":
            out = core.search(
                args.query,
                count=args.count,
                min_rerank=None if args.min_rerank == 0 else args.min_rerank,
                min_authority=args.min_authority,
                ori_question=args.ori_question,
                need_content=args.content,
            )
            text = core.to_markdown(out["results"]) if args.md else json.dumps(
                out, ensure_ascii=False, indent=2
            )
        else:
            out = core.fetch(args.url)
            text = core.fetch_to_markdown(out) if args.md else json.dumps(
                out, ensure_ascii=False, indent=2
            )
        print(text)
        return 0
    except core.ConfigError as exc:
        print(f"seekport: {exc}", file=sys.stderr)
        return 2
    except core.APIError as exc:
        print(f"seekport: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
