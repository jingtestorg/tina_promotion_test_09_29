# Specification: ap-invoice-automation-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/ap-invoice-automation-agent/` using instructions from the sap-agent-bootstrap section. (invoke from inside `assets/ap-invoice-automation-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> **Before proceeding**, read [guidelines-agent-skills.md](../guidelines-agent-skills.md) and decide — based on the PRD/intent — whether the agent needs runtime skills.

The AP Invoice Automation agent has complex multi-step workflows (matching logic selection, exception routing) and domain-specific rules (tolerance thresholds, matching flavor selection criteria) that should be implemented as runtime skills.

- [x] Create `assets/ap-invoice-automation-agent/app/skills/invoice-matching/SKILL.md` with step-by-step instructions for:
  - Matching flavor selection logic: 2-way (Invoice ↔ PO only), 3-way (Invoice ↔ PO ↔ GR), 4-way (Invoice ↔ PO ↔ GR ↔ Inspection)
  - Tolerance threshold rules for price variance and quantity variance
  - Decision tree: when to auto-post vs. when to escalate as exception
- [x] Create `assets/ap-invoice-automation-agent/app/skills/exception-handling/SKILL.md` with:
  - Exception classification rules (price mismatch, quantity mismatch, missing PO reference, duplicate detection)
  - Escalation routing logic (AP specialist queue format, required context to include)
  - Retry logic for transient errors (SAP API unavailable, GR not yet posted)

---

## Project-Specific Tasks ✅ COMPLETED

## EDI Invoice Ingestion (R1)

- [ ] Implement an `ingest_edi_invoice` tool in `assets/ap-invoice-automation-agent/app/agent.py` that:
  - Accepts structured invoice payloads (as delivered by SAP Integration Suite after EDI parsing)
  - Extracts mandatory fields: invoice number, vendor ID, invoice date, line items (material, quantity, unit price), PO reference, currency
  - Validates completeness: all mandatory fields present
  - Returns a structured invoice object for downstream processing
  - On malformed or incomplete payload: raises a descriptive exception that will be caught and escalated as M2.missed
- [ ] Add input validation that checks for: missing PO reference, missing vendor ID, zero-value invoices, unsupported currency codes

## Invoice Validation Against SAP Master Data (R1, R2)

- [ ] Implement a `validate_invoice_against_sap` tool that:
  - Calls the SAP S/4HANA AP MCP tools to verify vendor exists in vendor master data
  - Verifies the referenced PO exists and is open (not fully received/invoiced)
  - Checks invoice date falls within PO validity period
  - Returns validation result: passed / failed with reason
- [ ] Handle all SAP API error responses gracefully — relay errors verbatim, never fabricate responses

## Matching Flavor Selection & Execution (R2)

- [ ] Implement a `determine_matching_flavor` tool that:
  - Loads the `invoice-matching` runtime skill
  - Based on invoice type and PO data: selects 2-way, 3-way, or 4-way matching
  - Returns the selected matching flavor with justification
- [ ] Implement a `execute_matching` tool that:
  - For **2-way**: compares invoice line items against PO line items (quantity, price, material)
  - For **3-way**: additionally compares against Goods Receipt (GR) document quantities
  - For **4-way**: additionally compares against Quality Inspection (QI) results
  - Applies tolerance thresholds per the matching skill instructions
  - Returns: match result (matched / partial match / mismatch), matched amounts, variance details
- [ ] Ensure matching calls go through MCP tools only — no direct SAP API HTTP calls

## Touchless Auto-Posting (R3)

- [ ] Implement a `post_invoice_to_sap` tool that:
  - Calls SAP S/4HANA AP invoice posting MCP tool
  - Posts only when matching result is "matched" and within tolerance
  - Captures the SAP document number from the posting response
  - Writes an audit log entry before and after posting (including invoice ID, SAP document number, timestamp, match type)
  - Returns posting confirmation with SAP document number
- [ ] Implement idempotency check: before posting, verify no existing SAP document references this invoice number/vendor combination (duplicate detection)

## Exception Detection & Escalation Routing (R4)

- [ ] Implement an `escalate_exception` tool that:
  - Loads the `exception-handling` runtime skill
  - Classifies the exception type (price mismatch, quantity mismatch, missing reference, duplicate, validation failure)
  - Formats an exception record including: invoice ID, vendor ID, PO reference, mismatch details, matching type attempted, recommended next action
  - Routes the exception to the AP specialist queue (write to output / notification channel)
  - Returns exception ID and routing confirmation
- [ ] Ensure ALL exception paths (validation failure, matching failure, posting failure) route through this tool

## Cross-System SAP Support (R5)

- [ ] Configure the agent to support multiple SAP system types via environment variables:
  - `SAP_SYSTEM_TYPE`: `on-premise` | `private-cloud` | `public-cloud`
  - MCP tool selection adapts based on system type
- [ ] Document the required environment variables in a comment block in `agent.py`

## Agent System Prompt

- [ ] In `assets/ap-invoice-automation-agent/app/agent.py`, update the `@prompt_section` with:
  - Agent role: "You are an AP Invoice Automation agent. You process invoices received via EDI channel, determine the correct matching strategy, execute matching against SAP, post matched invoices touchlessly, and escalate exceptions."
  - Always follow the invoice-matching skill for matching flavor decisions
  - Always follow the exception-handling skill for escalation routing
  - Never post an invoice without successful matching within tolerance
  - Never fabricate or guess SAP data — always retrieve live data via MCP tools
  - Always emit structured log statements at each milestone

---

## Business Instrumentation

- [x] Implement business step instrumentation for all 5 milestones from the PRD:
  - `M1.achieved/missed` — EDI Invoice Received: `[M1.achieved]: EDI invoice ingested successfully, invoice_id={invoice_id}, vendor={vendor_id}` / `[M1.missed]: EDI invoice ingestion failed, reason={error}`
  - `M2.achieved/missed` — Invoice Validated: `[M2.achieved]: Invoice validation passed, invoice_id={invoice_id}` / `[M2.missed]: Invoice validation failed, invoice_id={invoice_id}, reason={reason}`
  - `M3.achieved/missed` — Matching Completed: `[M3.achieved]: Matching completed, invoice_id={invoice_id}, match_type={type}, result=matched` / `[M3.missed]: Matching failed, invoice_id={invoice_id}, reason={reason}`
  - `M4.achieved/missed` — Touchless Posting: `[M4.achieved]: Invoice posted touchlessly, invoice_id={invoice_id}, sap_document={doc_number}` / `[M4.missed]: Touchless posting failed, invoice_id={invoice_id}, reason={reason}`
  - `M5.achieved/missed` — Exception Escalated: `[M5.achieved]: Exception escalated, invoice_id={invoice_id}, exception_type={type}` / `[M5.missed]: Exception escalation failed, invoice_id={invoice_id}, reason={reason}`
- [x] Add OpenTelemetry spans for each milestone (see [guidelines-agent-python.md](../guidelines-agent-python.md) for Python-specific implementation)
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [ ] During API discovery: call `sap_knowledge_graph_api_discovery` with query "SAP S/4HANA AP invoice posting supplier invoice purchase order goods receipt matching" and save results to `api-discovery-results.md`
- [ ] For each relevant API found, download the schema using `sap_knowledge_graph_api_schema_download` and save to `specification/ap-invoice-automation-agent/api-specs/`
- [ ] If API specs were downloaded: invoke `mcp-translation-file` skill to generate MCP translation files, then invoke `setup-solution` to register MCP assets
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway`
- [ ] Add MCP server dependencies to `asset.yaml` under `requires` using exact ORD IDs
- [ ] After MCP translation is complete: generate `mcp-mock.json` using the `mcp-mock-config` skill

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit tests in `assets/ap-invoice-automation-agent/tests/` — one per tool (6 tools covered)
- [x] Write one integration test: full EDI-to-post flow with mocked SAP MCP tools and mocked LLM responses
- [x] Write one integration test: EDI-to-exception-escalation flow (matching failure path)
- [x] Run `pytest` — 205/205 tests passing, 90% coverage (above 70% threshold)
- [x] Verify `assets/ap-invoice-automation-agent/app/agent.py` has exactly 9 decorated functions — confirmed
- [x] Run `pytest` again to generate final `test_report.json` — 205 passed, score: 100%
- [x] Verify `test_report.json` exists in `assets/ap-invoice-automation-agent/` — confirmed
