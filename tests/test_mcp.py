"""MCP protocol tests. No network access; tools are mocked."""
from __future__ import annotations

import io
import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))

import seekport_mcp as mcp  # noqa: E402


RESULT = {
    "title": "DeepSeek V4",
    "url": "https://example.com/v4",
    "summary": "A summary.",
    "snippet": "short",
    "content": "",
    "rerank_score": 2.4,
    "authority": 3,
    "site_name": "Example",
    "date": "2026-06-01T00:00:00+00:00",
}


def call(message_id, method, params=None):
    message = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


class ProtocolTests(unittest.TestCase):
    def test_initialize(self):
        reply = mcp.handle(call(1, "initialize", {"protocolVersion": "2025-06-18"}))
        self.assertEqual(reply["result"]["serverInfo"]["name"], "seekport")
        self.assertIn("tools", reply["result"]["capabilities"])

    def test_unsupported_version_falls_back(self):
        reply = mcp.handle(call(1, "initialize", {"protocolVersion": "1999-01-01"}))
        self.assertEqual(reply["result"]["protocolVersion"], mcp.PROTOCOL_VERSION)

    def test_non_string_version_does_not_crash(self):
        reply = mcp.handle(call(1, "initialize", {"protocolVersion": ["2025-06-18"]}))
        self.assertEqual(reply["result"]["protocolVersion"], mcp.PROTOCOL_VERSION)

    def test_notification_has_no_reply(self):
        self.assertIsNone(mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertIsNone(mcp.handle({"jsonrpc": "2.0", "method": "initialize", "params": {}}))

    def test_non_object_messages_are_rejected(self):
        for bad in (None, 5, "hi", [], True):
            with self.subTest(bad=bad):
                reply = mcp.handle(bad)
                self.assertEqual(reply["error"]["code"], -32600)

    def test_bad_params_are_rejected(self):
        reply = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": "not-an-object"})
        self.assertEqual(reply["error"]["code"], -32602)

    def test_wrong_jsonrpc_version(self):
        reply = mcp.handle({"jsonrpc": "1.0", "id": 1, "method": "ping"})
        self.assertEqual(reply["error"]["code"], -32600)

    def test_tools_list(self):
        reply = mcp.handle(call(2, "tools/list"))
        names = {tool["name"] for tool in reply["result"]["tools"]}
        self.assertEqual(names, {"deepseek_search", "deepseek_fetch"})

    def test_unknown_method(self):
        reply = mcp.handle(call(3, "nope"))
        self.assertEqual(reply["error"]["code"], -32601)

    def test_ping(self):
        self.assertEqual(mcp.handle(call(4, "ping"))["result"], {})

    def test_main_survives_malformed_input(self):
        lines = "\n".join([
            "null",
            "not json",
            json.dumps({"jsonrpc": "2.0", "id": 9, "method": "ping"}),
        ]) + "\n"
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(lines)), mock.patch("sys.stdout", out):
            self.assertEqual(mcp.main(), 0)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(replies[0]["error"]["code"], -32600)
        self.assertEqual(replies[1]["error"]["code"], -32700)
        self.assertEqual(replies[2]["result"], {})

    def test_batch_with_a_scalar_does_not_crash(self):
        lines = json.dumps([{"jsonrpc": "2.0", "id": 1, "method": "ping"}, 5]) + "\n"
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(lines)), mock.patch("sys.stdout", out):
            mcp.main()
        replies = json.loads(out.getvalue())
        self.assertEqual(replies[0]["result"], {})
        self.assertEqual(replies[1]["error"]["code"], -32600)

    def test_empty_batch_gets_invalid_request(self):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("[]\n")), mock.patch("sys.stdout", out):
            mcp.main()
        reply = json.loads(out.getvalue())
        self.assertEqual(reply["error"]["code"], -32600)

    def test_main_processes_tool_calls_on_a_worker(self):
        fake = {"query": "x", "total": 0, "returned": 0, "results": []}
        line = json.dumps({"jsonrpc": "2.0", "id": 11, "method": "tools/call",
                           "params": {"name": "deepseek_search",
                                      "arguments": {"query": "x"}}}) + "\n"
        out = io.StringIO()
        with mock.patch.object(mcp.core, "search", return_value=fake), \
                mock.patch("sys.stdin", io.StringIO(line)), mock.patch("sys.stdout", out):
            mcp.main()
        reply = json.loads(out.getvalue())
        self.assertEqual(reply["id"], 11)
        self.assertFalse(reply["result"]["isError"])


class ToolTests(unittest.TestCase):
    def test_search_tool_returns_markdown(self):
        fake = {"query": "x", "total": 1, "returned": 1, "results": [RESULT]}
        with mock.patch.object(mcp.core, "search", return_value=fake):
            reply = mcp.handle(call(5, "tools/call", {"name": "deepseek_search",
                                                      "arguments": {"query": "x"}}))
        text = reply["result"]["content"][0]["text"]
        self.assertIn("https://example.com/v4", text)
        self.assertFalse(reply["result"]["isError"])

    def test_null_optionals_use_defaults(self):
        fake = {"query": "x", "total": 0, "returned": 0, "results": []}
        with mock.patch.object(mcp.core, "search", return_value=fake) as search:
            mcp.handle(call(5, "tools/call", {
                "name": "deepseek_search",
                "arguments": {"query": "x", "count": None, "min_rerank": None,
                              "need_content": None, "min_authority": None},
            }))
        kwargs = search.call_args.kwargs
        self.assertEqual(kwargs["count"], mcp.core.DEFAULT_COUNT)
        self.assertEqual(kwargs["min_rerank"], mcp.core.DEFAULT_MIN_RERANK)
        self.assertFalse(kwargs["need_content"])
        self.assertIsNone(kwargs["min_authority"])

    def test_zero_min_rerank_disables_filtering(self):
        fake = {"query": "x", "total": 0, "returned": 0, "results": []}
        with mock.patch.object(mcp.core, "search", return_value=fake) as search:
            mcp.handle(call(5, "tools/call", {
                "name": "deepseek_search",
                "arguments": {"query": "x", "min_rerank": 0},
            }))
        self.assertIsNone(search.call_args.kwargs["min_rerank"])

    def test_wrong_option_type_is_reported_not_coerced(self):
        with mock.patch.object(mcp.core, "search", side_effect=mcp.core.ConfigError("bad type")):
            reply = mcp.handle(call(5, "tools/call", {
                "name": "deepseek_search",
                "arguments": {"query": "x", "need_content": "false"},
            }))
        self.assertTrue(reply["result"]["isError"])
        self.assertIn("bad type", reply["result"]["content"][0]["text"])

    def test_fetch_tool(self):
        fake = {"url": "https://e.com", "title": "T", "content": "Body"}
        with mock.patch.object(mcp.core, "fetch", return_value=fake):
            reply = mcp.handle(call(6, "tools/call", {"name": "deepseek_fetch",
                                                      "arguments": {"url": "https://e.com"}}))
        self.assertEqual(reply["result"]["content"][0]["text"], "# T\n\n<https://e.com>\n\nBody")

    def test_tool_error_is_reported_not_raised(self):
        with mock.patch.object(mcp.core, "search", side_effect=mcp.core.ConfigError("no key")):
            reply = mcp.handle(call(7, "tools/call", {"name": "deepseek_search",
                                                      "arguments": {"query": "x"}}))
        self.assertTrue(reply["result"]["isError"])
        self.assertIn("no key", reply["result"]["content"][0]["text"])

    def test_unknown_tool(self):
        reply = mcp.handle(call(8, "tools/call", {"name": "nope", "arguments": {}}))
        self.assertTrue(reply["result"]["isError"])

    def test_non_object_arguments(self):
        reply = mcp.handle(call(8, "tools/call", {"name": "deepseek_search",
                                                  "arguments": "x"}))
        self.assertTrue(reply["result"]["isError"])

    def test_tools_are_valid_json_schema(self):
        for tool in mcp.TOOLS:
            json.dumps(tool["inputSchema"])
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertIn("required", tool["inputSchema"])


if __name__ == "__main__":
    unittest.main()
