"""Unit tests for determine_matching_flavor tool."""
import json
import pytest
from unittest.mock import patch
from agent import determine_matching_flavor


def test_determine_matching_flavor_returns_instruction():
    """Returns instruction for agent to check SAP for GR/QI availability."""
    with patch("agent.load_skill", return_value="mock-skill-content"):
        result = json.loads(determine_matching_flavor(
            invoice_id="INV-001",
            po_reference="PO-9876",
        ))
    assert result["invoice_id"] == "INV-001"
    assert result["po_reference"] == "PO-9876"
    assert "instruction" in result
    assert "2-way" in result["instruction"]
    assert "3-way" in result["instruction"]
    assert "4-way" in result["instruction"]


def test_determine_matching_flavor_skill_loaded():
    """Confirms skill is loaded during flavor determination."""
    with patch("agent.load_skill", return_value="skill-content") as mock_load:
        result = json.loads(determine_matching_flavor(
            invoice_id="INV-002",
            po_reference="PO-0001",
        ))
        mock_load.assert_called_once_with("invoice-matching")
    assert result["instruction"] is not None


def test_determine_matching_flavor_fields_present():
    """All expected fields are present in the result."""
    with patch("agent.load_skill", return_value="skill"):
        result = json.loads(determine_matching_flavor("INV-003", "PO-003"))
    assert "invoice_id" in result
    assert "po_reference" in result
    assert "instruction" in result
