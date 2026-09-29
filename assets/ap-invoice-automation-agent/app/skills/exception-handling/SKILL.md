---
name: exception-handling
description: |
  [WHAT] Provides exception classification, escalation routing logic, and retry rules for AP invoice processing failures.
  [WHEN] Use when an invoice cannot be matched, validation fails, a SAP posting error occurs, or any step in the invoice processing pipeline fails.
  [NOT] Do not use for matching tolerance decisions — use the invoice-matching skill instead.
  Key terms: exception, escalation, AP specialist, queue, mismatch, duplicate, retry.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - ap
    - invoice
    - exception
    - escalation
---

# Exception Handling Skill

## Purpose

This skill defines how the agent classifies, records, and routes invoice processing exceptions to ensure no invoice is silently lost and AP specialists receive actionable, complete context for resolution.

## Exception Types and Codes

| Exception Code | Trigger | Priority | Retry Before Escalating? |
|---|---|---|---|
| `MISSING_PO_REFERENCE` | Invoice has no valid PO number | HIGH | No |
| `UNKNOWN_VENDOR` | Vendor ID not found in SAP master data | HIGH | No |
| `PO_CLOSED` | Referenced PO is fully delivered/invoiced or cancelled | HIGH | No |
| `PRICE_MISMATCH` | Price variance exceeds hard block threshold (>5%) | HIGH | No |
| `QUANTITY_OVERBILL` | Invoice quantity exceeds GR quantity | HIGH | No |
| `QI_NOT_ACCEPTED` | QI document exists but is not in ACCEPTED status | MEDIUM | Yes — wait 4h, retry once |
| `PARTIAL_DELIVERY_HOLD` | Invoice qty < 97% of GR quantity | LOW | Yes — wait 24h, retry once |
| `DUPLICATE_INVOICE` | Same invoice number + vendor already posted in SAP | HIGH | No |
| `SAP_API_ERROR` | SAP API returned error or timed out | MEDIUM | Yes — retry once immediately |
| `MALFORMED_EDI` | EDI payload missing mandatory fields or invalid format | HIGH | No |
| `CURRENCY_MISMATCH` | Invoice currency differs from PO currency | HIGH | No |

## Retry Logic

For exception codes marked "Yes" in the retry column:
1. Log the hold with reason and retry timestamp
2. Wait the specified period (do not block — schedule for reprocessing)
3. Retry the failed step exactly once
4. If still failing after retry: escalate as the original exception code

For all other exception codes: escalate immediately without retry.

## Exception Record Format

When escalating, always create an exception record with ALL of the following fields:

```json
{
  "exception_id": "<uuid>",
  "exception_code": "<EXCEPTION_CODE>",
  "priority": "<HIGH|MEDIUM|LOW>",
  "invoice_id": "<invoice_number>",
  "vendor_id": "<vendor_id>",
  "po_reference": "<po_number or null>",
  "gr_reference": "<gr_number or null>",
  "invoice_amount": "<amount + currency>",
  "mismatch_details": {
    "field": "<which field mismatched>",
    "invoice_value": "<value from invoice>",
    "sap_value": "<value from SAP>",
    "variance_pct": "<percentage if applicable>"
  },
  "matching_type_attempted": "<2-way|3-way|4-way|none>",
  "step_failed": "<M1|M2|M3|M4>",
  "recommended_action": "<specific action for AP specialist>",
  "timestamp": "<ISO8601>"
}
```

Never omit fields — use `null` for fields that are not applicable.

## Recommended Actions by Exception Code

| Exception Code | Recommended Action for AP Specialist |
|---|---|
| `MISSING_PO_REFERENCE` | Contact vendor to obtain PO number, or create a blanket PO if applicable |
| `UNKNOWN_VENDOR` | Verify vendor onboarding; create vendor master record if legitimate |
| `PO_CLOSED` | Verify if additional PO needs to be raised; check with procurement |
| `PRICE_MISMATCH` | Review price agreement with vendor; approve manually if within business tolerance |
| `QUANTITY_OVERBILL` | Contact vendor for credit note or revised invoice |
| `QI_NOT_ACCEPTED` | Await QI completion; do not pay until goods are accepted |
| `PARTIAL_DELIVERY_HOLD` | Confirm if partial invoice is acceptable; await remaining delivery |
| `DUPLICATE_INVOICE` | Verify with vendor — reject if truly duplicate, investigate if legitimate re-billing |
| `SAP_API_ERROR` | Check SAP system availability; manually retry posting when system is stable |
| `MALFORMED_EDI` | Contact EDI provider/vendor to resend correct format |
| `CURRENCY_MISMATCH` | Confirm currency with vendor; update PO currency if incorrect |

## Escalation Routing

All exception records are written to the AP Specialist queue. Include the full exception record JSON.

After escalating:
1. Emit M5.achieved log
2. Do NOT attempt further processing of this invoice
3. Return a summary to the caller indicating the invoice has been escalated with exception_id

## Important Rules

- **Never** silently discard an invoice — every failure must produce an exception record
- **Never** invent or estimate mismatch values — all values in exception records come from actual invoice data and SAP API responses
- **Always** include the recommended_action field — it is the most valuable field for the AP specialist
- If the exception record itself cannot be written (e.g., output channel error), log the failure to the system error log and include the raw invoice data
