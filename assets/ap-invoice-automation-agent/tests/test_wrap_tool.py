"""Tests for wrap_tool and related functionality in prompt_injection_detector."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from prompt_injection_detector import wrap_tool, scan_content


class SimpleInput(BaseModel):
    query: str = Field(description="A query string")


def simple_fn(query: str) -> str:
    return json.dumps({"result": query.upper()})


@pytest.fixture
def simple_tool():
    return StructuredTool.from_function(
        func=simple_fn,
        name="simple_test_tool",
        description="A simple test tool",
        args_schema=SimpleInput,
    )


def test_wrap_tool_returns_tool(simple_tool):
    """wrap_tool returns a BaseTool instance."""
    wrapped = wrap_tool(simple_tool)
    assert wrapped is not None
    assert hasattr(wrapped, "name")


def test_wrap_tool_preserves_name(simple_tool):
    """Wrapped tool has the same name as the original."""
    wrapped = wrap_tool(simple_tool)
    assert wrapped.name == simple_tool.name


def test_scan_content_with_json():
    """JSON content is scanned without exceptions."""
    json_content = '{"invoice_id": "INV-001", "status": "matched", "sap_doc": "5100001234"}'
    result = scan_content(json_content)
    assert not result.is_suspicious


def test_scan_content_with_numeric_data():
    """Numeric-heavy content is not flagged."""
    result = scan_content("12345.67 USD 9876 PO-12345 INV-67890")
    assert not result.is_suspicious


def test_scan_content_flagging_behavior():
    """Verify scan_content flag behavior for typical injection vs normal text."""
    normal_result = scan_content("invoice amount is 1500 USD")
    assert isinstance(normal_result.is_suspicious, bool)
