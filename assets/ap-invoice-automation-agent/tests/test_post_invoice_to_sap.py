"""Unit tests for post_invoice_to_sap tool."""
import json
import pytest
from agent import post_invoice_to_sap


MATCHED_RESULT = json.dumps({"match_result": "matched", "variance_pct": 0.5})
MISMATCHED_RESULT = json.dumps({"match_result": "mismatch", "reason": "price_exceeds_threshold"})
PARTIAL_RESULT = json.dumps({"match_result": "partial_match"})


def test_post_matched_invoice():
    """Matched invoice generates posting instruction."""
    result = json.loads(post_invoice_to_sap(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_result=MATCHED_RESULT,
        total_amount=1500.00,
        currency="USD",
    ))
    assert "instruction" in result
    assert "INV-001" in result["instruction"] or result["invoice_id"] == "INV-001"


def test_post_blocked_for_mismatch():
    """Mismatched invoice is blocked from posting."""
    result = json.loads(post_invoice_to_sap(
        invoice_id="INV-002",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_result=MISMATCHED_RESULT,
        total_amount=1500.00,
        currency="USD",
    ))
    assert result["status"] == "blocked"
    assert "mismatch" in result["reason"]


def test_post_blocked_for_partial_match():
    """Partial match invoice is blocked from posting."""
    result = json.loads(post_invoice_to_sap(
        invoice_id="INV-003",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_result=PARTIAL_RESULT,
        total_amount=1500.00,
        currency="USD",
    ))
    assert result["status"] == "blocked"


def test_post_invalid_matching_result_json():
    """Invalid matching_result JSON returns error."""
    result = json.loads(post_invoice_to_sap(
        invoice_id="INV-004",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_result="not-valid-json",
        total_amount=1500.00,
        currency="USD",
    ))
    assert result["status"] == "error"
    assert "JSON" in result["error"]


def test_post_includes_duplicate_check_instruction():
    """Posting instruction includes duplicate detection requirement."""
    result = json.loads(post_invoice_to_sap(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_result=MATCHED_RESULT,
        total_amount=1500.00,
        currency="USD",
    ))
    assert "duplicate" in result["instruction"].lower()
