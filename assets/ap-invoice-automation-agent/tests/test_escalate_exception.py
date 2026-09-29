"""Unit tests for escalate_exception tool."""
import json
import pytest
from unittest.mock import patch
from agent import escalate_exception


def _escalate(exception_code: str, mismatch_details: dict | None = None) -> dict:
    with patch("agent.load_skill", return_value="exception-skill-content"):
        return json.loads(escalate_exception(
            invoice_id="INV-001",
            vendor_id="VENDOR-42",
            po_reference="PO-9876",
            exception_code=exception_code,
            mismatch_details=json.dumps(mismatch_details or {}),
            matching_type_attempted="3-way",
            step_failed="M3",
        ))


def test_escalate_price_mismatch():
    """PRICE_MISMATCH exception is escalated with HIGH priority."""
    result = _escalate("PRICE_MISMATCH", {"field": "unit_price", "invoice_value": 200, "sap_value": 150, "variance_pct": 33})
    assert result["status"] == "escalated"
    assert result["exception_record"]["priority"] == "HIGH"
    assert result["exception_record"]["exception_code"] == "PRICE_MISMATCH"
    assert "vendor" in result["exception_record"]["recommended_action"].lower() or "price" in result["exception_record"]["recommended_action"].lower()


def test_escalate_missing_po_reference():
    """MISSING_PO_REFERENCE exception is HIGH priority."""
    result = _escalate("MISSING_PO_REFERENCE")
    assert result["exception_record"]["priority"] == "HIGH"
    assert result["exception_record"]["exception_code"] == "MISSING_PO_REFERENCE"


def test_escalate_quantity_overbill():
    """QUANTITY_OVERBILL exception is escalated with HIGH priority."""
    result = _escalate("QUANTITY_OVERBILL", {"invoice_value": 15, "sap_value": 10})
    assert result["exception_record"]["priority"] == "HIGH"
    assert result["exception_record"]["exception_code"] == "QUANTITY_OVERBILL"


def test_escalate_qi_not_accepted():
    """QI_NOT_ACCEPTED exception is MEDIUM priority with retry guidance."""
    result = _escalate("QI_NOT_ACCEPTED")
    assert result["exception_record"]["priority"] == "MEDIUM"
    assert result["exception_record"]["exception_code"] == "QI_NOT_ACCEPTED"


def test_escalate_duplicate_invoice():
    """DUPLICATE_INVOICE exception is HIGH priority."""
    result = _escalate("DUPLICATE_INVOICE")
    assert result["exception_record"]["priority"] == "HIGH"


def test_escalate_exception_record_completeness():
    """Exception record contains all required fields."""
    result = _escalate("SAP_API_ERROR")
    record = result["exception_record"]
    required_fields = ["exception_id", "exception_code", "priority", "invoice_id",
                       "vendor_id", "po_reference", "mismatch_details",
                       "matching_type_attempted", "step_failed", "recommended_action", "timestamp"]
    for field in required_fields:
        assert field in record, f"Missing field: {field}"


def test_escalate_exception_id_is_uuid():
    """Exception ID is a valid UUID."""
    import uuid
    result = _escalate("PRICE_MISMATCH")
    exception_id = result["exception_record"]["exception_id"]
    uuid.UUID(exception_id)  # Raises ValueError if not valid UUID


def test_escalate_loads_exception_skill():
    """Exception handling skill is loaded during escalation."""
    with patch("agent.load_skill", return_value="skill") as mock_load:
        escalate_exception(
            invoice_id="INV-001", vendor_id="V-01", po_reference="PO-01",
            exception_code="PRICE_MISMATCH", mismatch_details="{}",
            matching_type_attempted="3-way", step_failed="M3"
        )
        mock_load.assert_called_with("exception-handling")
