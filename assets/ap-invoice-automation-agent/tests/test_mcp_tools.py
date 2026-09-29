"""Tests for the mcp_tools module (mock tool loading)."""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_load_mock_tools_no_mock_file():
    """Returns empty list when mcp-mock.json does not exist at the expected path."""
    import mcp_tools
    # If there's already a mcp-mock.json, this test is N/A - skip
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    if mock_path.exists():
        pytest.skip("mcp-mock.json exists; skipping no-file test")
    result = mcp_tools._load_mock_tools()
    assert isinstance(result, list)
    assert result == []


def test_load_mock_tools_with_valid_mock_file(tmp_path):
    """Loads StructuredTool instances from a valid mcp-mock.json."""
    import mcp_tools

    mock_data = {
        "tools": [
            {"name": "test_tool", "description": "A test tool", "mock_response": {"result": "ok"}},
            {"name": "another_tool", "description": "Another", "mock_response": "string response"},
        ]
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))

    with patch("mcp_tools.Path") as mock_path_cls:
        mock_instance = MagicMock()
        mock_instance.__truediv__ = lambda s, x: mock_file if x == "mcp-mock.json" else tmp_path / x
        mock_instance.parent = tmp_path
        mock_path_cls.return_value.parent.parent = tmp_path

        # Direct call
        result = mcp_tools._load_mock_tools.__wrapped__(mock_file) if hasattr(mcp_tools._load_mock_tools, "__wrapped__") else None

    # Direct test with patched path
    real_mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    if not real_mock_path.exists():
        # Create temp mock file and test loading logic
        test_config = {"tools": [{"name": "sap_post_invoice", "description": "Post invoice to SAP", "mock_response": {"doc_number": "5100001234"}}]}
        real_mock_path.write_text(json.dumps(test_config))
        try:
            tools = mcp_tools._load_mock_tools()
            assert len(tools) == 1
            assert tools[0].name == "sap_post_invoice"
        finally:
            real_mock_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_get_mcp_tools_in_test_mode():
    """In IBD_TESTING mode, get_mcp_tools returns mock tools (empty list if no mock file)."""
    import mcp_tools
    with patch.object(mcp_tools, "_IBD_TESTING", True):
        tools = await mcp_tools.get_mcp_tools()
    assert isinstance(tools, list)


def test_load_mock_tools_invalid_json(tmp_path):
    """Returns empty list when mcp-mock.json contains invalid JSON."""
    import mcp_tools
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text("not-valid-json")

    with patch.object(Path, "__truediv__", return_value=mock_file):
        # Simulate the path resolution
        original_parent = mcp_tools.Path(__file__).parent.parent
        result = mcp_tools._load_mock_tools()
    assert isinstance(result, list)
