"""Unit tests for ingest_edi_invoice tool."""
import json
import pytest
from agent import ingest_edi_invoice


VALID_PAYLOAD = {
    "invoice_id": "INV-2024-001",
    "vendor_id": "VENDOR-42",
    "invoice_date": "2024-01-15",
    "po_reference": "PO-9876",
    "currency": "USD",
    "total_amount": 1500.00,
    "line_items": [
        {"material": "MAT-001", "quantity": 10, "unit_price": 150.00}
    ],
}


def test_ingest_valid_invoice():
    """Valid EDI invoice payload is parsed successfully."""
    result = json.loads(ingest_edi_invoice(json.dumps(VALID_PAYLOAD)))
    assert result["status"] == "success"
    assert result["invoice_id"] == "INV-2024-001"
    assert result["vendor_id"] == "VENDOR-42"
    assert result["po_reference"] == "PO-9876"


def test_ingest_missing_mandatory_field():
    """Invoice missing po_reference returns error with MALFORMED_EDI."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "po_reference"}
    result = json.loads(ingest_edi_invoice(json.dumps(payload)))
    assert result["status"] == "error"
    assert result["exception_code"] == "MALFORMED_EDI"
    assert "po_reference" in result["error"]


def test_ingest_missing_vendor_id():
    """Invoice missing vendor_id returns MALFORMED_EDI error."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "vendor_id"}
    result = json.loads(ingest_edi_invoice(json.dumps(payload)))
    assert result["status"] == "error"
    assert result["exception_code"] == "MALFORMED_EDI"


def test_ingest_empty_line_items():
    """Invoice with empty line items returns MALFORMED_EDI error."""
    payload = {**VALID_PAYLOAD, "line_items": []}
    result = json.loads(ingest_edi_invoice(json.dumps(payload)))
    assert result["status"] == "error"
    assert result["exception_code"] == "MALFORMED_EDI"


def test_ingest_invalid_json():
    """Invalid JSON payload returns MALFORMED_EDI error."""
    result = json.loads(ingest_edi_invoice("not-valid-json"))
    assert result["status"] == "error"
    assert result["exception_code"] == "MALFORMED_EDI"


def test_ingest_preserves_line_items():
    """Line items are preserved in the parsed output."""
    result = json.loads(ingest_edi_invoice(json.dumps(VALID_PAYLOAD)))
    assert len(result["line_items"]) == 1
    assert result["line_items"][0]["material"] == "MAT-001"
