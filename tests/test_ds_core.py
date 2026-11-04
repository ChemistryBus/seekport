"""Unit tests for seekport's core. All HTTP is mocked; no API credits are spent."""
from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cli  # noqa: E402
import ds_core as core  # noqa: E402
import spend  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class RawResponse(FakeResponse):
    def __init__(self, raw):
        self._raw = raw


class ReadTimeoutResponse:
    def read(self):
        raise TimeoutError("timed out")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code, message="boom", headers=None):
    body = json.dumps({"error": {"message": message, "type": "invalid_request_error",
                                 "param": None, "code": "invalid_request_error"}}).encode()
    return urllib.error.HTTPError("https://api.deepseek.com/x", code, message,
                                  headers or {}, io.BytesIO(body))


RESULT = {
    "rerank_score": 2.4,
    "title": "DeepSeek V4",
    "url": "https://example.com/v4",
    "snippet": "short",
    "summary": "A longer summary for the model.",
    "content": "",
    "site_name": "Example",
    "site_icon": None,
    "date": "2026-06-01T00:00:00+00:00",
    "authority": 3,
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {
            "DEEPSEEK_API_KEY": "test-key",
            "XDG_CACHE_HOME": self.tmp.name,
        })
        self.env.start()
        for name in ("SEEKPORT_BUDGET", "SEEKPORT_BASE_URL", "SEEKPORT_TIMEOUT"):
            os.environ.pop(name, None)
        self.sleep = mock.patch.object(core.time, "sleep")
        self.sleep.start()
        self.open = mock.patch.object(core._OPENER, "open")
        self.opener = self.open.start()

    def tearDown(self):
        self.open.stop()
        self.sleep.stop()
        self.env.stop()
        self.tmp.cleanup()

    def ledger_total(self):
        return spend.spent_today()


class SearchTests(Base):
    def test_default_rerank_filter_drops_low_score(self):
        payload = {"results": [RESULT, {**RESULT, "rerank_score": 1.0}]}
        self.opener.return_value = FakeResponse(payload)
        out = core.search("deepseek")
        self.assertEqual(out["total"], 2)
        self.assertEqual(out["returned"], 1)

    def test_filters_low_rerank_and_low_authority(self):
        payload = {"results": [RESULT,
                               {**RESULT, "rerank_score": 1.0},
                               {**RESULT, "authority": 1}]}
        self.opener.return_value = FakeResponse(payload)
        out = core.search("deepseek", min_authority=3)
        self.assertEqual(out["total"], 3)
        self.assertEqual(out["returned"], 1)

    def test_min_authority_filter(self):
        self.opener.return_value = FakeResponse({"results": [{**RESULT, "authority": 2}]})
        out = core.search("x", min_authority=3)
        self.assertEqual(out["returned"], 0)

    def test_malformed_result_items_are_dropped(self):
        self.opener.return_value = FakeResponse({"results": [RESULT, "x", None, 5]})
        out = core.search("x")
        self.assertEqual(out["total"], 4)
        self.assertEqual(out["returned"], 1)

    def test_missing_score_is_dropped_when_filtering(self):
        self.opener.return_value = FakeResponse({"results": [{**RESULT, "rerank_score": None}]})
        self.assertEqual(core.search("x")["returned"], 0)

    def test_min_rerank_none_keeps_unknown_scores(self):
        self.opener.return_value = FakeResponse({"results": [{**RESULT, "rerank_score": None}]})
        self.assertEqual(core.search("x", min_rerank=None)["returned"], 1)

    def test_empty_results_are_not_an_error_and_are_free(self):
        self.opener.return_value = FakeResponse({"results": []})
        out = core.search("nothing matches")
        self.assertEqual(out["results"], [])
        self.assertEqual(self.ledger_total(), 0)

    def test_successful_search_records_spend(self):
        self.opener.return_value = FakeResponse({"results": [RESULT]})
        core.search("x")
        self.assertAlmostEqual(self.ledger_total(), core.PRICE_RMB_PER_CALL)

    def test_filtered_out_search_still_records_spend(self):
        self.opener.return_value = FakeResponse({"results": [{**RESULT, "rerank_score": 0.1}]})
        out = core.search("x")
        self.assertEqual(out["returned"], 0)
        self.assertAlmostEqual(self.ledger_total(), core.PRICE_RMB_PER_CALL)

    def test_missing_key_is_a_config_error(self):
        os.environ.pop("DEEPSEEK_API_KEY")
        with self.assertRaises(core.ConfigError) as ctx:
            core.search("x")
        self.assertIn("DEEPSEEK_API_KEY", str(ctx.exception))

    def test_query_cannot_be_blank(self):
        for bad in ("", "   ", None, 42):
            with self.assertRaises(core.ConfigError):
                core.search(bad)

    def test_query_length_limit(self):
        with self.assertRaises(core.ConfigError) as ctx:
            core.search("x" * 129)
        self.assertIn("128", str(ctx.exception))

    def test_count_bounds(self):
        for bad in (0, 51, True, "10", 1.5):
            with self.assertRaises(core.ConfigError):
                core.search("x", count=bad)

    def test_option_types_are_validated(self):
        cases = [
            {"min_rerank": "1.5"},
            {"min_rerank": 4},
            {"min_authority": "3"},
            {"min_authority": 5},
            {"need_content": "false"},
            {"ori_question": "x" * 129},
            {"ori_question": 7},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(core.ConfigError):
                    core.search("x", **kwargs)
        self.opener.assert_not_called()

    def test_timeout_must_be_positive(self):
        for bad in (0, -1, float("nan"), float("inf"), "30", True):
            with self.subTest(bad=bad):
                with self.assertRaises(core.ConfigError):
                    core.search("x", timeout=bad)

    def test_env_timeout_is_validated(self):
        os.environ["SEEKPORT_TIMEOUT"] = "nan"
        with self.assertRaises(core.ConfigError):
            core.search("x")

    def test_request_shape(self):
        self.opener.return_value = FakeResponse({"results": []})
        core.search("site:github.com deepseek", count=5, need_content=False,
                    ori_question="what is deepseek")
        request = self.opener.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.deepseek.com/v1/tools/search")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        body = json.loads(request.data)
        self.assertEqual(body, {"query": "site:github.com deepseek", "count": 5,
                                "need_content": False, "ori_question": "what is deepseek"})


class RetryTests(Base):
    def test_retries_429_then_succeeds(self):
        self.opener.side_effect = [http_error(429), FakeResponse({"results": [RESULT]})]
        out = core.search("x")
        self.assertEqual(out["returned"], 1)
        self.assertEqual(self.opener.call_count, 2)

    def test_408_is_retried(self):
        self.opener.side_effect = [http_error(408), FakeResponse({"results": []})]
        core.search("x")
        self.assertEqual(self.opener.call_count, 2)

    def test_non_retryable_4xx_are_not_retried(self):
        for code in (400, 401, 402, 403, 404, 413):
            with self.subTest(code=code):
                self.opener.reset_mock()
                self.opener.side_effect = http_error(code, f"error {code}")
                with self.assertRaises(core.APIError) as ctx:
                    core.search("x")
                self.assertEqual(self.opener.call_count, 1)
                self.assertIn(str(code), str(ctx.exception))

    def test_5xx_exhaustion_message(self):
        self.opener.side_effect = [http_error(500, "server down")] * 4
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertEqual(self.opener.call_count, 4)
        self.assertIn("gave up after 4 attempts", str(ctx.exception))

    def test_429_exhaustion_message(self):
        self.opener.side_effect = [http_error(429, "rate limited")] * 4
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("gave up after 4 attempts", str(ctx.exception))
        self.assertIn("retry later", str(ctx.exception))

    def test_400_surfaces_api_message(self):
        self.opener.side_effect = http_error(400, "'count' must be between 1 and 50")
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("'count' must be between 1 and 50", str(ctx.exception))

    def test_network_error_is_an_api_error(self):
        self.opener.side_effect = urllib.error.URLError("Name or service not known")
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("network error", str(ctx.exception))

    def test_read_timeout_is_an_api_error(self):
        self.opener.return_value = ReadTimeoutResponse()
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("timed out", str(ctx.exception))

    def test_read_connection_error_is_an_api_error(self):
        self.opener.return_value = ReadTimeoutResponse()
        self.opener.return_value.read = mock.Mock(side_effect=ConnectionResetError("reset"))
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("connection failed", str(ctx.exception))

    def test_retry_after_header_is_honoured(self):
        self.opener.side_effect = [http_error(429, headers={"Retry-After": "2"}),
                                   FakeResponse({"results": []})]
        core.search("x")
        core.time.sleep.assert_called_once_with(2.0)

    def test_redirects_are_refused(self):
        self.assertIsNone(core._NoRedirect().redirect_request(
            None, None, 302, "Found", {}, "https://evil.example"))
        self.opener.side_effect = http_error(302, "Found")
        with self.assertRaises(core.APIError):
            core.search("x")
        self.assertEqual(self.opener.call_count, 1)

    def test_non_json_response(self):
        self.opener.return_value = RawResponse(b"<html>not json</html>")
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("non-JSON", str(ctx.exception))

    def test_non_object_json_response(self):
        self.opener.return_value = FakeResponse([1, 2, 3])
        with self.assertRaises(core.APIError) as ctx:
            core.search("x")
        self.assertIn("unexpected JSON shape", str(ctx.exception))


class BudgetTests(Base):
    def test_budget_blocks_before_any_http_call(self):
        os.environ["SEEKPORT_BUDGET"] = "0.001"
        with self.assertRaises(core.ConfigError) as ctx:
            core.search("x")
        self.opener.assert_not_called()
        self.assertIn("budget", str(ctx.exception))

    def test_invalid_budget_is_rejected(self):
        os.environ["SEEKPORT_BUDGET"] = "lots"
        with self.assertRaises(core.ConfigError):
            core.search("x")

    def test_non_finite_budget_is_rejected(self):
        for bad in ("nan", "inf", "-1"):
            with self.subTest(bad=bad):
                os.environ["SEEKPORT_BUDGET"] = bad
                with self.assertRaises(core.ConfigError):
                    core.search("x")

    def test_torn_ledger_line_is_ignored(self):
        os.environ["SEEKPORT_BUDGET"] = "1"
        path = spend._file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-a-ledger-line\n")
        self.opener.return_value = FakeResponse({"results": []})
        core.search("x")  # a torn line must not lock the user out
        self.assertEqual(spend.spent_today(), 0)

    def test_record_survives_a_torn_ledger(self):
        path = spend._file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-a-ledger-line\n")
        spend.record()  # must not raise
        self.assertAlmostEqual(spend.spent_today(), spend.PRICE_RMB_PER_CALL)

    def test_concurrent_records_do_not_lose_updates(self):
        threads = [threading.Thread(target=spend.record) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertAlmostEqual(spend.spent_today(), 20 * spend.PRICE_RMB_PER_CALL)


class BaseUrlTests(Base):
    def test_base_url_needs_a_scheme(self):
        os.environ["SEEKPORT_BASE_URL"] = "api.deepseek.com"
        with self.assertRaises(core.ConfigError):
            core.search("x")

    def test_plain_http_is_rejected_off_localhost(self):
        os.environ["SEEKPORT_BASE_URL"] = "http://evil.example"
        with self.assertRaises(core.ConfigError):
            core.search("x")

    def test_http_localhost_is_allowed(self):
        os.environ["SEEKPORT_BASE_URL"] = "http://127.0.0.1:9"
        self.opener.return_value = FakeResponse({"results": []})
        core.search("x")

    def test_base_url_rejects_credentials_and_query(self):
        for bad in ("https://u:p@api.deepseek.com", "https://api.deepseek.com?x=1"):
            with self.subTest(bad=bad):
                os.environ["SEEKPORT_BASE_URL"] = bad
                with self.assertRaises(core.ConfigError):
                    core.search("x")

    def test_base_url_rejects_a_path(self):
        os.environ["SEEKPORT_BASE_URL"] = "https://api.deepseek.com/v1"
        with self.assertRaises(core.ConfigError):
            core.search("x")


class FetchTests(Base):
    def test_fetch_success(self):
        self.opener.return_value = FakeResponse({"title": "T", "content": "# Body"})
        out = core.fetch("https://example.com/a")
        self.assertEqual(out, {"url": "https://example.com/a", "title": "T", "content": "# Body"})

    def test_url_validation(self):
        bad = ["", "example.com", "ftp://example.com", "https://user:pw@example.com",
               "https://" + "a" * 9000, "http://[::1", "http://[zz]"]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(core.ConfigError):
                    core.fetch(url)

    def test_fetch_404_is_a_clear_api_error(self):
        self.opener.side_effect = http_error(404, "no extractable content")
        with self.assertRaises(core.APIError) as ctx:
            core.fetch("https://example.com/gone")
        self.assertIn("404", str(ctx.exception))

    def test_empty_content_is_not_billed(self):
        self.opener.return_value = FakeResponse({"title": "T", "content": ""})
        out = core.fetch("https://example.com/empty")
        self.assertEqual(out["content"], "")
        self.assertEqual(self.ledger_total(), 0)

    def test_non_string_content_is_rejected(self):
        self.opener.return_value = FakeResponse({"title": "T", "content": 123})
        with self.assertRaises(core.APIError):
            core.fetch("https://example.com/bad")


class RenderingTests(Base):
    def test_markdown_contains_link_and_meta(self):
        text = core.to_markdown([RESULT])
        self.assertIn("## 1. DeepSeek V4", text)
        self.assertIn("<https://example.com/v4>", text)
        self.assertIn("score 2.4", text)
        self.assertIn("A longer summary", text)

    def test_markdown_empty(self):
        self.assertIn("No results", core.to_markdown([]))

    def test_markdown_survives_non_string_fields(self):
        text = core.to_markdown([{**RESULT, "site_name": 42, "title": None, "url": None}])
        self.assertIn("(untitled)", text)
        self.assertIn("<>", text)
        self.assertNotIn("None", text)

    def test_fetch_markdown(self):
        text = core.fetch_to_markdown({"url": "https://e.com", "title": "T", "content": "B"})
        self.assertEqual(text, "# T\n\n<https://e.com>\n\nB")


class CliTests(Base):
    def test_search_json_is_default(self):
        fake = {"query": "x", "total": 1, "returned": 1, "results": [RESULT]}
        with mock.patch.object(core, "search", return_value=fake):
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                code = cli.main(["search", "x"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["returned"], 1)

    def test_json_flag_is_accepted(self):
        fake = {"query": "x", "total": 1, "returned": 1, "results": [RESULT]}
        with mock.patch.object(core, "search", return_value=fake):
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                self.assertEqual(cli.main(["search", "x", "--json"]), 0)
        self.assertIn('"results"', out.getvalue())

    def test_search_markdown(self):
        fake = {"query": "x", "total": 1, "returned": 1, "results": [RESULT]}
        with mock.patch.object(core, "search", return_value=fake):
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                cli.main(["search", "x", "--md"])
        self.assertIn("score 2.4", out.getvalue())

    def test_fetch_json_and_markdown(self):
        fake = {"url": "https://e.com", "title": "T", "content": "B"}
        with mock.patch.object(core, "fetch", return_value=fake):
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                self.assertEqual(cli.main(["fetch", "https://e.com"]), 0)
        self.assertEqual(json.loads(out.getvalue())["title"], "T")
        with mock.patch.object(core, "fetch", return_value=fake):
            with mock.patch("sys.stdout", new=io.StringIO()) as out:
                cli.main(["fetch", "https://e.com", "--md"])
        self.assertEqual(out.getvalue().strip(), "# T\n\n<https://e.com>\n\nB")

    def test_json_and_md_are_mutually_exclusive(self):
        for argv in (["search", "x", "--json", "--md"],
                     ["fetch", "https://e.com", "--json", "--md"]):
            with self.subTest(argv=argv):
                with mock.patch("sys.stderr", new=io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        cli.main(argv)
                self.assertEqual(ctx.exception.code, 2)

    def test_min_rerank_zero_disables_filtering(self):
        fake = {"query": "x", "total": 0, "returned": 0, "results": []}
        with mock.patch.object(core, "search", return_value=fake) as search:
            with mock.patch("sys.stdout", new=io.StringIO()):
                cli.main(["search", "x", "--min-rerank", "0"])
        self.assertIsNone(search.call_args.kwargs["min_rerank"])

    def test_config_error_exits_2(self):
        with mock.patch.object(core, "search", side_effect=core.ConfigError("no key")):
            with mock.patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(cli.main(["search", "x"]), 2)

    def test_api_error_exits_1(self):
        with mock.patch.object(core, "fetch", side_effect=core.APIError("HTTP 500")):
            with mock.patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(cli.main(["fetch", "https://e.com"]), 1)


if __name__ == "__main__":
    unittest.main()
