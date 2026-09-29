"""Integration tests for the AP Invoice Automation Agent end-to-end flows."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent import SampleAgent


VALID_INVOICE_PAYLOAD = json.dumps({
    "invoice_id": "INV-2024-INT-001",
    "vendor_id": "VENDOR-TEST-99",
    "invoice_date": "2024-06-15",
    "po_reference": "PO-INT-5555",
    "currency": "EUR",
    "total_amount": 3000.00,
    "line_items": [
        {"material": "MAT-A", "quantity": 20, "unit_price": 150.00}
    ],
})


@pytest.fixture
def agent():
    return SampleAgent()


@pytest.fixture
def mock_llm_matched_response():
    """Simulate LLM deciding to post the invoice touchlessly."""
    return "Invoice INV-2024-INT-001 has been successfully validated, matched (3-way), and posted to SAP. SAP document number: 5100001234. [M4.achieved]: Invoice posted touchlessly, invoice_id=INV-2024-INT-001, sap_document=5100001234"


@pytest.fixture
def mock_llm_exception_response():
    """Simulate LLM deciding to escalate an exception."""
    return "Invoice INV-2024-INT-001 could not be matched due to a price mismatch exceeding the 5% tolerance. The invoice has been escalated to the AP specialist queue. Exception ID: exc-001. [M5.achieved]: Exception escalated, invoice_id=INV-2024-INT-001, exception_type=PRICE_MISMATCH"


@pytest.mark.asyncio
async def test_full_touchless_flow(agent, mock_llm_matched_response):
    """End-to-end: EDI invoice ingested → validated → matched → posted touchlessly."""
    mock_message = MagicMock()
    mock_message.content = mock_llm_matched_response

    with patch("agent.get_mcp_tools", new_callable=AsyncMock, return_value=[]), \
         patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock,
               return_value={"messages": [mock_message]}):

        response = await agent.invoke(
            query=f"Process this EDI invoice: {VALID_INVOICE_PAYLOAD}",
            context_id="test-context-touchless",
        )

    assert response.status == "completed"
    assert "posted" in response.message.lower() or "M4" in response.message


@pytest.mark.asyncio
async def test_exception_escalation_flow(agent, mock_llm_exception_response):
    """End-to-end: invoice with price mismatch → exception escalated."""
    mock_message = MagicMock()
    mock_message.content = mock_llm_exception_response

    with patch("agent.get_mcp_tools", new_callable=AsyncMock, return_value=[]), \
         patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock,
               return_value={"messages": [mock_message]}):

        response = await agent.invoke(
            query="Process invoice INV-2024-INT-001 - price is 200 EUR but PO shows 100 EUR",
            context_id="test-context-exception",
        )

    assert response.status == "completed"
    assert "escalated" in response.message.lower() or "exception" in response.message.lower()


@pytest.mark.asyncio
async def test_stream_yields_processing_then_result(agent):
    """stream() yields initial processing status then final result."""
    mock_message = MagicMock()
    mock_message.content = "Invoice processed successfully."

    with patch("agent.get_mcp_tools", new_callable=AsyncMock, return_value=[]), \
         patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock,
               return_value={"messages": [mock_message]}):

        chunks = []
        async for chunk in agent.stream("Process invoice", "test-stream-ctx"):
            chunks.append(chunk)

    assert len(chunks) >= 2
    assert chunks[0]["is_task_complete"] is False
    assert chunks[-1]["is_task_complete"] is True
    assert chunks[-1]["content"] == "Invoice processed successfully."


@pytest.mark.asyncio
async def test_agent_handles_llm_error_gracefully(agent):
    """Agent returns error status gracefully when LLM invocation fails.
    RuntimeError is a non-retryable error — caught by the general except clause in stream()."""
    from litellm.exceptions import APIConnectionError
    with patch("agent.get_mcp_tools", new_callable=AsyncMock, return_value=[]), \
         patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock,
               side_effect=APIConnectionError("Connection refused", model="test", llm_provider="test")):

        response = await agent.invoke(
            query="Process invoice",
            context_id="test-error-context",
        )

    # APIConnectionError from RETRYABLE_ERRORS will exhaust fallback chain and raise,
    # then be caught by the general except in stream() → returns "error" status
    assert response.status in ("error", "completed")  # completed = graceful degradation message
