#!/usr/bin/env python3
"""seekport — DeepSeek Search / Fetch client, standard library only.

Library: search(), fetch(), to_markdown(), fetch_to_markdown().
CLI:     python3 scripts/cli.py search "query" [--count 10] [--md]

Env: DEEPSEEK_API_KEY (required), SEEKPORT_BUDGET (RMB/day),
     SEEKPORT_BASE_URL, SEEKPORT_TIMEOUT.
Exit: 0 ok, 1 API/network error, 2 bad input or configuration.
"""
from __future__ import annotations

import http.client
import json
import math
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from errors import APIError, ConfigError, SeekportError  # noqa: E402,F401
from spend import PRICE_RMB_PER_CALL, check as budget_check, record as budget_record  # noqa: E402,F401

__version__ = "0.1.0"
DEFAULT_COUNT, DEFAULT_MIN_RERANK = 10, 1.5
MAX_QUERY_CHARS, MAX_URL_CHARS = 128, 8192
MAX_RETRIES, DEFAULT_TIMEOUT = 3, 30
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


# ---------------------------------------------------------------- validation

def _check_query(query):
    if not isinstance(query, str) or not query.strip():
        raise ConfigError("query must be a non-empty string")
    if len(query) > MAX_QUERY_CHARS:
        raise ConfigError(f"query is {len(query)} chars; max {MAX_QUERY_CHARS}")


def _check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 50:
        raise ConfigError("count must be an integer between 1 and 50")


def _check_url(url):
    if not isinstance(url, str) or not url:
        raise ConfigError("url must be a non-empty string")
    if len(url) > MAX_URL_CHARS:
        raise ConfigError(f"url is {len(url)} chars; max {MAX_URL_CHARS}")
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        raise ConfigError("url is malformed (bad IPv6 or host)") from None
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ConfigError("url must be an absolute http(s) URL with a host")
    if parts.username or parts.password:
        raise ConfigError("url must not contain a username or password")


def _check_options(min_rerank, min_authority, need_content, ori_question, localization):
    if min_rerank is not None and (
        isinstance(min_rerank, bool)
        or not isinstance(min_rerank, (int, float))
        or not 0 <= min_rerank <= 3
    ):
        raise ConfigError("min_rerank must be a number between 0 and 3")
    if min_authority is not None and (
        isinstance(min_authority, bool)
        or not isinstance(min_authority, int)
        or not -1 <= min_authority <= 4
    ):
        raise ConfigError("min_authority must be an integer between -1 and 4")
    if not isinstance(need_content, bool):
        raise ConfigError("need_content must be a boolean")
    if ori_question is not None and (
        not isinstance(ori_question, str)
        or not 1 <= len(ori_question) <= MAX_QUERY_CHARS
    ):
        raise ConfigError(f"ori_question must be a string of 1-{MAX_QUERY_CHARS} chars")
    if localization and not isinstance(localization, str):
        raise ConfigError("localization must be an IPv4 or IPv6 address string")


def _env_float(name, default):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number") from None


def _api_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "DEEPSEEK_API_KEY is not set. Create one at "
            "https://platform.deepseek.com/api_keys and export it."
        )
    return key


def _base_url():
    raw = os.environ.get("SEEKPORT_BASE_URL", "https://api.deepseek.com").rstrip("/")
    try:
        parts = urllib.parse.urlsplit(raw)
    except ValueError:
        raise ConfigError("SEEKPORT_BASE_URL is not a valid URL") from None
    if (parts.scheme not in ("http", "https") or not parts.hostname
            or parts.username or parts.password or parts.query or parts.fragment
            or parts.path not in ("", "/")):
        raise ConfigError(
            "SEEKPORT_BASE_URL must be a plain origin such as https://api.deepseek.com"
        )
    if parts.scheme == "http" and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ConfigError("SEEKPORT_BASE_URL must use https (http only for localhost)")
    return raw


# ---------------------------------------------------------------- HTTP

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # never forward the bearer token to another origin


_OPENER = urllib.request.build_opener(_NoRedirect())


def _backoff(attempt, retry_after=None):
    if retry_after:
        try:
            return min(max(float(retry_after), 0.0), 30.0)
        except ValueError:
            pass
    return min(2 ** attempt + random.uniform(0, 0.5), 8.0)


def _api_message(exc):
    try:
        data = json.loads(exc.read().decode("utf-8"))
        return (data.get("error") or {}).get("message") or str(exc)
    except Exception:
        return getattr(exc, "reason", None) or str(exc)


def _post(path, payload, timeout=None):
    if timeout is None:
        timeout = _env_float("SEEKPORT_TIMEOUT", DEFAULT_TIMEOUT)
    if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or not timeout > 0):
        raise ConfigError("timeout must be a positive number of seconds")
    url = _base_url() + path
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"seekport/{__version__}",
    }
    for attempt in range(MAX_RETRIES + 1):
        request = urllib.request.Request(url, data=body, method="POST", headers=headers)
        try:
            with _OPENER.open(request, timeout=timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            message = _api_message(exc)
            if exc.code in RETRY_STATUS and attempt < MAX_RETRIES:
                time.sleep(_backoff(attempt, exc.headers.get("Retry-After")))
                continue
            if exc.code in RETRY_STATUS:
                raise APIError(
                    f"HTTP {exc.code}: {message} "
                    f"(gave up after {MAX_RETRIES + 1} attempts; retry later)"
                ) from None
            raise APIError(f"HTTP {exc.code}: {message}") from None
        except urllib.error.URLError as exc:
            raise APIError(f"network error reaching {url}: {exc.reason}") from None
        except (OSError, http.client.HTTPException) as exc:
            if isinstance(exc, TimeoutError):
                raise APIError(f"request timed out after {timeout}s") from None
            raise APIError(f"connection failed while reading the response: {exc}") from None
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise APIError("server returned a non-JSON response") from None
        if not isinstance(data, dict):
            raise APIError("server returned an unexpected JSON shape")
        return data


# ---------------------------------------------------------------- public API

def _filter(results, min_rerank, min_authority):
    kept = []
    for item in results:
        if not isinstance(item, dict):
            continue
        score = item.get("rerank_score")
        if min_rerank is not None and (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or score < min_rerank
        ):
            continue
        if min_authority is not None:
            authority = item.get("authority")
            if not isinstance(authority, int) or authority < min_authority:
                continue
        kept.append(item)
    return kept


def search(query, *, count=DEFAULT_COUNT, min_rerank=DEFAULT_MIN_RERANK,
           min_authority=None, ori_question=None, localization="",
           need_content=False, timeout=None):
    """Search the web. Returns {query,total,returned,results}."""
    _check_query(query)
    _check_count(count)
    _check_options(min_rerank, min_authority, need_content, ori_question, localization)
    payload = {"query": query, "count": count, "need_content": need_content}
    if ori_question:
        payload["ori_question"] = ori_question
    if localization:
        payload["localization"] = localization
    budget_check()
    data = _post("/v1/tools/search", payload, timeout)
    raw = data.get("results")
    if not isinstance(raw, list):
        raise APIError("unexpected response: missing 'results' array")
    if raw:
        budget_record()  # bill before filtering: a filter bug cannot hide a paid call
    kept = _filter(raw, min_rerank, min_authority)
    return {"query": query, "total": len(raw), "returned": len(kept), "results": kept}


def fetch(url, *, timeout=None):
    """Fetch one page as Markdown. Returns {url,title,content}."""
    _check_url(url)
    budget_check()
    data = _post("/v1/tools/fetch", {"url": url}, timeout)
    title = data.get("title") or ""
    content = data.get("content") or ""
    if not isinstance(title, str) or not isinstance(content, str):
        raise APIError("unexpected response: title/content must be strings")
    if content:
        budget_record()  # the API only bills pages that yielded content
    return {"url": url, "title": title, "content": content}


# ---------------------------------------------------------------- rendering

def to_markdown(results):
    """Render search results compactly: title, URL, meta, summary."""
    if not results:
        return "_No results after filtering. Try a broader query or a lower --min-rerank._"
    blocks = []
    for index, item in enumerate(results, 1):
        site = item.get("site_name")
        title = item.get("title")
        url = item.get("url")
        body = item.get("summary") or item.get("snippet") or ""
        meta = " · ".join(part for part in (
            site if isinstance(site, str) else "",
            str(item.get("date") or "")[:10],
            f"score {item.get('rerank_score', '?')}",
            f"auth {item.get('authority', '?')}",
        ) if part)
        block = (f"## {index}. {title if isinstance(title, str) else '(untitled)'}\n"
                 f"<{url if isinstance(url, str) else ''}>\n\n{meta}\n\n"
                 f"{body if isinstance(body, str) else ''}")
        if item.get("content"):
            block += f"\n\n{item['content']}"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


def fetch_to_markdown(page):
    return f"# {page['title']}\n\n<{page['url']}>\n\n{page['content']}"


if __name__ == "__main__":
    from cli import main
    sys.exit(main())
