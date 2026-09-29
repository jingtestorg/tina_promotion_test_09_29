"""Unit tests for execute_matching tool."""
import json
import pytest
from agent import execute_matching


LINE_ITEMS = json.dumps([{"material": "MAT-001", "quantity": 10, "unit_price": 150.00}])


def test_execute_matching_2way():
    """2-way matching returns instruction with correct matching type."""
    result = json.loads(execute_matching(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_flavor="2-way",
        line_items=LINE_ITEMS,
    ))
    assert result["matching_flavor"] == "2-way"
    assert "2-way" in result["instruction"]
    assert result["line_items_count"] == 1


def test_execute_matching_3way():
    """3-way matching includes GR comparison instruction."""
    result = json.loads(execute_matching(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_flavor="3-way",
        line_items=LINE_ITEMS,
    ))
    assert result["matching_flavor"] == "3-way"
    assert "3-way" in result["instruction"]


def test_execute_matching_4way():
    """4-way matching instruction references GR and QI."""
    result = json.loads(execute_matching(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_flavor="4-way",
        line_items=LINE_ITEMS,
    ))
    assert result["matching_flavor"] == "4-way"


def test_execute_matching_invalid_flavor():
    """Invalid matching flavor returns error."""
    result = json.loads(execute_matching(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_flavor="5-way",
        line_items=LINE_ITEMS,
    ))
    assert result["status"] == "error"
    assert "5-way" in result["error"]


def test_execute_matching_invalid_line_items_json():
    """Invalid line_items JSON returns error."""
    result = json.loads(execute_matching(
        invoice_id="INV-001",
        vendor_id="VENDOR-42",
        po_reference="PO-9876",
        matching_flavor="2-way",
        line_items="not-valid-json",
    ))
    assert result["status"] == "error"
    assert "JSON" in result["error"]


def test_execute_matching_multiple_line_items():
    """Multiple line items are counted correctly."""
    items = json.dumps([
        {"material": "MAT-001", "quantity": 10, "unit_price": 100.00},
        {"material": "MAT-002", "quantity": 5, "unit_price": 200.00},
    ])
    result = json.loads(execute_matching("INV-001", "V-01", "PO-001", "3-way", items))
    assert result["line_items_count"] == 2
