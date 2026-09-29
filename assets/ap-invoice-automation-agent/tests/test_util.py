"""Tests for util module."""
import json
import pytest
from util import minify_json, truncate_response, enhance_tool_description, enhance_tool_name


def _make_mock_tool(server_name: str, name: str, description: str = "A tool"):
    """Create a simple mock MCP tool object."""
    from unittest.mock import MagicMock
    tool = MagicMock()
    tool.server_name = server_name
    tool.fragment_name = server_name
    tool.name = name
    tool.description = description
    return tool


# ---- trim_mcp_response / truncate_response ----

def test_trim_short_response():
    """Short responses are returned unchanged."""
    short = '{"result": "ok"}'
    result = truncate_response(short)
    assert result == short


def test_trim_long_response():
    """Very long responses are trimmed to the configured max length."""
    long_response = "x" * 100_000
    result = truncate_response(long_response)
    assert len(result) <= 30_000 + 200  # allow for truncation marker


def test_trim_empty_string():
    """Empty string is returned as-is."""
    result = truncate_response("")
    assert isinstance(result, str)
    assert result == ""


def test_truncate_adds_marker():
    """Truncated response has a truncation marker."""
    long_response = "y" * 50_000
    result = truncate_response(long_response)
    assert "truncated" in result.lower()


# ---- minify_json ----

def test_minify_json_compact():
    """minify_json strips whitespace from pretty-printed JSON."""
    pretty = json.dumps({"key": "value", "num": 42}, indent=4)
    result = minify_json(pretty)
    assert "    " not in result
    parsed = json.loads(result)
    assert parsed["key"] == "value"


def test_minify_non_json():
    """minify_json returns non-JSON text unchanged."""
    text = "plain text response"
    result = minify_json(text)
    assert result == text


def test_minify_empty():
    """minify_json handles empty string."""
    result = minify_json("")
    assert result == ""


# ---- enhance_tool_description ----

def test_enhance_tool_description_basic():
    """enhance_tool_description prefixes with server label."""
    tool = _make_mock_tool("my-server", "my_tool", "Get data")
    result = enhance_tool_description(tool)
    assert "my-server" in result
    assert "Get data" in result


def test_enhance_tool_description_none():
    """enhance_tool_description handles None gracefully."""
    result = enhance_tool_description(None)
    assert result == ""


# ---- enhance_tool_name ----

def test_enhance_tool_name_long_server():
    """enhance_tool_name strips org+type prefix from ORD-style server names."""
    tool = _make_mock_tool("sap.mcpbuilder:apiResource:cost-center:v1", "list_cost_center")
    result = enhance_tool_name(tool)
    assert "list_cost_center" in result
    assert "cost" in result


def test_enhance_tool_name_simple_server():
    """enhance_tool_name handles simple server names without colons."""
    tool = _make_mock_tool("my-server", "my_tool")
    result = enhance_tool_name(tool)
    assert "my_tool" in result
    assert "my" in result


def test_enhance_tool_name_truncates_long():
    """enhance_tool_name truncates very long names to 64 chars."""
    long_server = "sap.org:type:" + "a" * 100 + ":v1"
    tool = _make_mock_tool(long_server, "tool_name")
    result = enhance_tool_name(tool)
    assert len(result) <= 64


def test_enhance_tool_name_none():
    """enhance_tool_name handles None gracefully."""
    result = enhance_tool_name(None)
    assert result == ""


def trim_mcp_response(text: str) -> str:
    """Wrapper for backwards compat in tests."""
    return truncate_response(text)
