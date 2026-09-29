---
name: invoice-matching
description: |
  [WHAT] Provides matching flavor selection logic and tolerance rules for AP invoice processing.
  [WHEN] Use when determining which matching type to apply (2-way, 3-way, 4-way) and when evaluating whether an invoice matches within tolerance.
  [NOT] Do not use for exception escalation routing — use the exception-handling skill instead.
  Key terms: 2-way matching, 3-way matching, 4-way matching, tolerance, PO, GR, quality inspection.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - ap
    - invoice
    - matching
---

# Invoice Matching Skill

## Purpose

This skill encodes the matching flavor selection logic and tolerance threshold rules for AP invoice processing. It ensures the agent consistently selects the correct matching strategy and correctly evaluates whether an invoice is within acceptable variance.

## Matching Flavor Selection Rules

### 2-Way Matching (Invoice ↔ Purchase Order)
**Apply when:**
- The invoice references a PO number
- No Goods Receipt (GR) document exists for the PO line items
- Invoice type is for services or non-stock items where GR is not required

**What to compare:**
- Invoice line item price vs. PO line item price
- Invoice quantity vs. PO quantity ordered
- Vendor on invoice vs. vendor on PO
- Currency on invoice vs. PO currency

### 3-Way Matching (Invoice ↔ PO ↔ Goods Receipt)
**Apply when:**
- The invoice references a PO number
- A Goods Receipt (GR) document exists for the PO line items
- Invoice type is for physical goods/materials

**What to compare:**
- Invoice line item price vs. PO line item price
- Invoice quantity vs. GR quantity received (NOT PO quantity ordered)
- Vendor on invoice vs. vendor on PO
- Delivery date on invoice vs. GR posting date (informational only, not a hard block)

### 4-Way Matching (Invoice ↔ PO ↔ GR ↔ Quality Inspection)
**Apply when:**
- The invoice references a PO number
- A Goods Receipt exists
- A Quality Inspection (QI) document exists and is in ACCEPTED status for the PO line items
- Typically applies to regulated industries (pharma, aerospace) or high-value materials

**What to compare:**
- All 3-way matching comparisons PLUS:
- Invoice quantity vs. QI accepted quantity (not total GR quantity)
- QI result must be ACCEPTED — if QI is still in process, hold the invoice (do not escalate yet, retry after configured wait period)

## Tolerance Thresholds

### Price Variance Tolerance
- **Hard block (escalate immediately):** Price variance > 5% of PO line item price
- **Soft tolerance (auto-post with audit flag):** Price variance ≤ 2% of PO line item price
- **Review zone (escalate with LOW priority):** Price variance between 2% and 5%

### Quantity Variance Tolerance
- **Hard block (escalate immediately):** Invoice quantity > GR quantity (overbilling)
- **Auto-post:** Invoice quantity ≤ GR quantity AND within 3% under-delivery tolerance
- **Partial delivery hold:** Invoice quantity < 97% of GR quantity — hold for remaining delivery

### Amount Tolerance (absolute)
- **Minor discrepancy (auto-post):** Total invoice amount differs by ≤ 10 currency units from expected
- This covers rounding differences across line items

## Matching Decision Logic

Follow this decision tree for every invoice:

```
1. Does invoice have a valid PO reference?
   → NO: Escalate as "MISSING_PO_REFERENCE"
   → YES: Continue

2. Does a GR document exist for this PO?
   → NO: Apply 2-way matching
   → YES: Does a QI document exist and is it ACCEPTED?
       → YES: Apply 4-way matching
       → NO (QI exists but not ACCEPTED): Hold invoice, do not process yet
       → NO (no QI): Apply 3-way matching

3. After matching: Are all variances within tolerance?
   → YES (all within soft tolerance): Auto-post touchlessly → M4
   → YES (within 2-5% zone): Auto-post with audit flag → M4 (flagged)
   → NO (any hard block): Escalate as exception → M5
```

## Important Rules

- **Never** guess or infer PO/GR data — always retrieve live data via MCP tools
- **Never** post an invoice if any line item exceeds the hard block threshold
- **Always** log the matching type selected and the variance amounts in the M3 milestone log
- If SAP returns an error when fetching GR/QI data, treat it as a transient error and retry once. If still failing, escalate as "SAP_API_ERROR" exception type.
