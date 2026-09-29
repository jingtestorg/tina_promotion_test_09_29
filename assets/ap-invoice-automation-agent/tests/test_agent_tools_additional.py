"""Additional tests for higher coverage of agent.py tool functions."""
import json
import pytest
from unittest.mock import patch
from agent import (
    ingest_edi_invoice,
    validate_invoice_against_sap,
    determine_matching_flavor,
    execute_matching,
    post_invoice_to_sap,
    escalate_exception,
    AP_TOOLS,
    _log_milestone,
)


# ---- ingest_edi_invoice additional coverage ----

def test_ingest_missing_invoice_id():
    """Missing invoice_id returns MALFORMED_EDI."""
    payload = {
        "vendor_id": "V-01", "invoice_date": "2024-01-01",
        "po_reference": "PO-01", "currency": "USD",
        "total_amount": 100.0, "line_items": [{"qty": 1}]
    }
    result = json.loads(ingest_edi_invoice(json.dumps(payload)))
    assert result["status"] == "error"
    assert "invoice_id" in result["error"]


def test_ingest_multiple_line_items():
    """Invoice with multiple line items is ingested correctly."""
    payload = {
        "invoice_id": "INV-X", "vendor_id": "V-01", "invoice_date": "2024-01-01",
        "po_reference": "PO-01", "currency": "EUR", "total_amount": 500.0,
        "line_items": [
            {"material": "A", "quantity": 2, "unit_price": 100.0},
            {"material": "B", "quantity": 3, "unit_price": 100.0},
        ]
    }
    result = json.loads(ingest_edi_invoice(json.dumps(payload)))
    assert result["status"] == "success"
    assert len(result["line_items"]) == 2


# ---- validate_invoice_against_sap additional coverage ----

def test_validate_returns_sap_tool_instruction():
    """Validation result includes instruction to call SAP MCP tools."""
    result = json.loads(validate_invoice_against_sap("INV-001", "V-42", "PO-9876", "2024-01-15"))
    assert "SAP MCP" in result["message"] or "MCP" in result["message"]


# ---- post_invoice_to_sap additional coverage ----

def test_post_returns_invoice_fields():
    """Post instruction includes key invoice fields."""
    matched = json.dumps({"match_result": "matched"})
    result = json.loads(post_invoice_to_sap("INV-001", "V-01", "PO-01", matched, 1000.0, "USD"))
    assert result["invoice_id"] == "INV-001"
    assert result["total_amount"] == 1000.0
    assert result["currency"] == "USD"


# ---- execute_matching additional coverage ----

def test_execute_matching_returns_all_fields():
    """Execute matching result includes all expected metadata fields."""
    items = json.dumps([{"material": "M", "quantity": 5, "unit_price": 100.0}])
    result = json.loads(execute_matching("INV-001", "V-01", "PO-01", "2-way", items))
    assert result["invoice_id"] == "INV-001"
    assert result["vendor_id"] == "V-01"
    assert result["po_reference"] == "PO-01"


# ---- escalate_exception additional coverage ----

def test_escalate_partial_delivery_hold():
    """PARTIAL_DELIVERY_HOLD exception is LOW priority."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(escalate_exception(
            "INV-001", "V-01", "PO-01", "PARTIAL_DELIVERY_HOLD",
            json.dumps({}), "3-way", "M3"
        ))
    assert result["exception_record"]["priority"] == "LOW"


def test_escalate_sap_api_error():
    """SAP_API_ERROR exception is MEDIUM priority."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(escalate_exception(
            "INV-001", "V-01", "PO-01", "SAP_API_ERROR",
            json.dumps({}), "none", "M4"
        ))
    assert result["exception_record"]["priority"] == "MEDIUM"


def test_escalate_unknown_exception_code():
    """Unknown exception codes default to MEDIUM priority."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(escalate_exception(
            "INV-001", "V-01", "PO-01", "CUSTOM_ERROR",
            json.dumps({}), "2-way", "M2"
        ))
    assert result["exception_record"]["priority"] == "MEDIUM"
    assert result["exception_record"]["recommended_action"] == "Review invoice manually"


def test_escalate_null_po_reference():
    """Empty po_reference is stored as None in exception record."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(escalate_exception(
            "INV-001", "V-01", "", "PRICE_MISMATCH",
            json.dumps({}), "2-way", "M3"
        ))
    assert result["exception_record"]["po_reference"] is None


def test_escalate_invalid_mismatch_details_json():
    """Invalid mismatch_details JSON is handled gracefully."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(escalate_exception(
            "INV-001", "V-01", "PO-01", "PRICE_MISMATCH",
            "not-valid-json", "3-way", "M3"
        ))
    assert result["status"] == "escalated"
    assert result["exception_record"]["mismatch_details"] == {"raw": "not-valid-json"}


# ---- AP_TOOLS registry ----

def test_ap_tools_registry_has_all_tools():
    """AP_TOOLS contains all 6 expected tool names."""
    tool_names = {t.name for t in AP_TOOLS}
    expected = {
        "ingest_edi_invoice", "validate_invoice_against_sap",
        "determine_matching_flavor", "execute_matching",
        "post_invoice_to_sap", "escalate_exception"
    }
    assert expected == tool_names


# ---- _log_milestone ----

def test_log_milestone_achieved(caplog):
    """Milestone achieved log is emitted at INFO level."""
    import logging
    with caplog.at_level(logging.INFO):
        _log_milestone("M1", True, invoice_id="INV-001", vendor_id="V-01")
    assert "M1.achieved" in caplog.text


def test_log_milestone_missed(caplog):
    """Milestone missed log is emitted at INFO level."""
    import logging
    with caplog.at_level(logging.INFO):
        _log_milestone("M3", False, invoice_id="INV-001", reason="mismatch")
    assert "M3.missed" in caplog.text
