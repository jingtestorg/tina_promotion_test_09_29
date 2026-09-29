"""Tests for mcp_providers/agw.py context management utilities."""
import json
import pytest
from unittest.mock import patch, MagicMock
from mcp_providers.agw import set_user_token, reset_user_token, get_user_sub, get_user_token, _build_mock_tools


def test_set_and_reset_user_token():
    """set_user_token returns a token context that can be reset."""
    ctx = set_user_token("test-jwt-token")
    assert ctx is not None
    reset_user_token(ctx)


def test_set_user_token_none():
    """set_user_token accepts None without error."""
    ctx = set_user_token(None)
    assert ctx is not None
    reset_user_token(ctx)


def test_get_user_sub_without_token():
    """get_user_sub returns a non-empty string even without a token."""
    result = get_user_sub()
    assert isinstance(result, str)
    assert len(result) > 0


def test_set_token_multiple_times():
    """Multiple token sets and resets work correctly."""
    ctx1 = set_user_token("token-1")
    ctx2 = set_user_token("token-2")
    reset_user_token(ctx2)
    reset_user_token(ctx1)


def test_get_user_token_after_set():
    """get_user_token returns the set token."""
    ctx = set_user_token("my-jwt")
    try:
        token = get_user_token()
        assert token == "my-jwt"
    finally:
        reset_user_token(ctx)


def test_get_user_token_returns_none_when_not_set():
    """get_user_token returns None when no token is set."""
    ctx = set_user_token(None)
    try:
        token = get_user_token()
        assert token is None
    finally:
        reset_user_token(ctx)


def test_build_mock_tools_in_test_mode():
    """_build_mock_tools returns a list of tools in IBD_TESTING mode."""
    tools = _build_mock_tools()
    assert isinstance(tools, list)


def test_build_mock_tools_with_mock_file(tmp_path):
    """_build_mock_tools loads tools from a valid mcp-mock.json with servers format."""
    import json as _json
    from pathlib import Path
    import mcp_providers.agw as agw_module

    mock_data = {
        "servers": {
            "sap-ap": {
                "tools": {
                    "post_invoice": {
                        "description": "Post an AP invoice to SAP",
                        "mock_response": {"doc_number": "5100001234", "status": "posted"},
                        "input_schema": {
                            "properties": {
                                "invoice_id": {"type": "string", "description": "Invoice ID"},
                                "amount": {"type": "number", "description": "Invoice amount"},
                            },
                            "required": ["invoice_id"]
                        }
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(_json.dumps(mock_data))

    original_mock_file = agw_module._MOCK_FILE
    agw_module._MOCK_FILE = mock_file
    try:
        tools = agw_module._build_mock_tools()
        assert len(tools) == 1
        assert tools[0].name == "post_invoice"
    finally:
        agw_module._MOCK_FILE = original_mock_file


@pytest.mark.asyncio
async def test_agw_get_mcp_tools_ibd_testing():
    """In IBD_TESTING mode, get_mcp_tools from agw returns mock tools (or empty list)."""
    import mcp_providers.agw as agw_module
    tools = await agw_module.get_mcp_tools()
    assert isinstance(tools, list)


def test_get_user_sub_with_valid_b64_jwt():
    """get_user_sub handles a JWT with valid base64 segments gracefully."""
    import base64, json as _json
    # Craft a minimal JWT-like token with a valid base64 payload containing 'sub'
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(_json.dumps({"sub": "test-user-123"}).encode()).rstrip(b"=").decode()
    fake_jwt = f"{header}.{payload}.fakesig"
    ctx = set_user_token(fake_jwt)
    try:
        result = get_user_sub()
        assert isinstance(result, str)
        assert len(result) > 0
    finally:
        reset_user_token(ctx)
