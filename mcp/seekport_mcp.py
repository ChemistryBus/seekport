#!/usr/bin/env python3
"""seekport MCP server — stdio JSON-RPC 2.0, zero dependencies.

Exposes two tools:
  deepseek_search  ranked web results with relevance/authority filtering
  deepseek_fetch   one page as Markdown

Register with Claude Code:
  claude mcp add seekport -- python3 /absolute/path/to/mcp/seekport_mcp.py

Protocol notes: newline-delimited JSON on stdin/stdout. Logs must never go to
stdout, or they corrupt the transport.
"""
from __future__ import annotations

import json
import os
import sys
import threading

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import ds_core as core  # noqa: E402

SERVER_NAME = "seekport"
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
_WRITE_LOCK = threading.Lock()
_WORKERS = []

TOOLS = [
    {
        "name": "deepseek_search",
        "description": (
            "Search the web through DeepSeek's official Search API. Returns ranked "
            "results with title, URL, summary (600-800 chars) and scores. Supports "
            "site:, -site:, quoted phrases, -term, lang:zh,en, after:, before:. "
            "Use this when WebFetch is blocked by a gateway or when the harness has "
            "no built-in web search."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 128,
                    "description": "Search query; search operators are passed through.",
                },
                "count": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                "min_rerank": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1.5,
                    "description": "Drop results scoring below this. 1.5+ is high quality.",
                },
                "min_authority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 4,
                    "description": "Drop results with lower authority. 3+ is highly authoritative.",
                },
                "need_content": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also return full page text; larger and slower.",
                },
                "ori_question": {
                    "type": "string",
                    "maxLength": 128,
                    "description": "The user's original question, to improve intent matching.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "deepseek_fetch",
        "description": (
            "Fetch one web page through DeepSeek's Fetch API and return its title and "
            "Markdown body. Use after deepseek_search to read a specific result."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Absolute http(s) URL, max 8192 characters.",
                }
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
]


def _ok(message_id, result):
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id, code, message):
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _text(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _call_tool(name, args):
    if not isinstance(args, dict):
        return _text("arguments must be an object", is_error=True)
    if name == "deepseek_search":
        count = args.get("count")
        min_rerank = args.get("min_rerank")
        if min_rerank is None:
            min_rerank = core.DEFAULT_MIN_RERANK
        elif min_rerank == 0:
            min_rerank = None  # 0 means "keep everything", including unscored results
        need_content = args.get("need_content")
        out = core.search(
            args.get("query", ""),
            count=core.DEFAULT_COUNT if count is None else count,
            min_rerank=min_rerank,
            min_authority=args.get("min_authority"),
            need_content=False if need_content is None else need_content,
            ori_question=args.get("ori_question"),
        )
        return _text(core.to_markdown(out["results"]))
    if name == "deepseek_fetch":
        return _text(core.fetch_to_markdown(core.fetch(args.get("url", ""))))
    return _text(f"Unknown tool: {name}", is_error=True)


def handle(message):
    """Return a response dict, or None for notifications."""
    if not isinstance(message, dict):
        return _error(None, -32600, "Invalid Request: expected an object")
    if message.get("jsonrpc") != "2.0":
        return _error(message.get("id"), -32600, "Invalid Request: jsonrpc must be 2.0")
    method = message.get("method")
    message_id = message.get("id")
    if message_id is None:  # notifications/initialized, cancellations, …
        return None
    params = message.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return _error(message_id, -32602, "Invalid params: expected an object")

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = (requested if isinstance(requested, str)
                   and requested in SUPPORTED_VERSIONS else PROTOCOL_VERSION)
        return _ok(message_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": core.__version__},
        })
    if method == "ping":
        return _ok(message_id, {})
    if method == "tools/list":
        return _ok(message_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            return _ok(message_id, _call_tool(params.get("name"), params.get("arguments") or {}))
        except core.SeekportError as exc:
            return _ok(message_id, _text(str(exc), is_error=True))
        except Exception as exc:  # one bad call must not kill the server
            return _ok(message_id, _text(f"seekport internal error: {exc}", is_error=True))
    return _error(message_id, -32601, f"Method not found: {method}")


def _write(payload):
    with _WRITE_LOCK:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def _reply(message):
    try:
        return handle(message)
    except Exception as exc:  # never let one message kill the transport
        return _error(None, -32603, f"Internal error: {exc}")


def _dispatch(message):
    reply = _reply(message)
    if reply:
        _write(reply)


def main():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            _write(_error(None, -32700, "Parse error"))
            continue
        if isinstance(message, list):  # JSON-RPC batch
            if not message:
                _write(_error(None, -32600, "Invalid Request: empty batch"))
                continue
            replies = [reply for reply in map(_reply, message) if reply]
            if replies:
                _write(replies)
            continue
        if (isinstance(message, dict) and message.get("method") == "tools/call"
                and message.get("id") is not None):
            # Tool calls can retry for a while; keep ping and cancellation readable.
            worker = threading.Thread(target=_dispatch, args=(message,))
            _WORKERS[:] = [w for w in _WORKERS if w.is_alive()]
            worker.start()
            _WORKERS.append(worker)
            continue
        _dispatch(message)
    for worker in _WORKERS:
        worker.join()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (BrokenPipeError, KeyboardInterrupt):
        sys.exit(0)
