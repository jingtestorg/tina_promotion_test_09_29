"""Unit tests for validate_invoice_against_sap tool."""
import json
import pytest
from agent import validate_invoice_against_sap


def test_validate_valid_invoice():
    """Valid invoice passes structural validation."""
    result = json.loads(validate_invoice_against_sap(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        invoice_date="2024-01-15",
    ))
    assert result["status"] == "passed"
    assert result["invoice_id"] == "INV-001"


def test_validate_missing_vendor_id():
    """Missing vendor_id returns UNKNOWN_VENDOR failure."""
    result = json.loads(validate_invoice_against_sap(
        invoice_id="INV-001",
        vendor_id="",
        po_reference="PO-9876",
        invoice_date="2024-01-15",
    ))
    assert result["status"] == "failed"
    assert result["exception_code"] == "UNKNOWN_VENDOR"


def test_validate_missing_po_reference():
    """Missing po_reference returns MISSING_PO_REFERENCE failure."""
    result = json.loads(validate_invoice_against_sap(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="",
        invoice_date="2024-01-15",
    ))
    assert result["status"] == "failed"
    assert result["exception_code"] == "MISSING_PO_REFERENCE"


def test_validate_whitespace_vendor_id():
    """Whitespace-only vendor_id is treated as missing."""
    result = json.loads(validate_invoice_against_sap(
        invoice_id="INV-001",
        vendor_id="   ",
        po_reference="PO-9876",
        invoice_date="2024-01-15",
    ))
    assert result["status"] == "failed"
    assert result["exception_code"] == "UNKNOWN_VENDOR"
