# Product Requirements Document (PRD)

tina version 1

tina version 2

tina version 3

**Title:** AP Invoice Automation Agent — EDI Channel **Date:** 2026-09-28 **Owner:** AP Product Owner **Solution Category:** AI Agent

* * *

## Product Purpose & Value Proposition

**Elevator Pitch:** Invoices arriving via EDI today require manual intervention to match, validate, and post. This AI agent eliminates that bottleneck by autonomously receiving EDI invoices, running the correct matching logic against SAP, and posting touchlessly — escalating only the exceptions that genuinely need a human.

**Business Need:** AP teams processing high EDI invoice volumes spend significant time on repetitive matching and posting tasks. When mismatches occur, invoices queue for manual review, delaying payment and straining supplier relationships. There is no standard SAP product that drives the full end-to-end touchless decision from EDI intake through posting.

**Expected Value:** ≥ 80% of invoices processed without human intervention, reducing cycle time from days to hours and freeing AP specialists to focus on exceptions and supplier relationships.

**Product Objectives:**

1.  Achieve ≥ 80% touchless invoice processing rate across all invoice types.
    
2.  Support all SAP deployment variants: S/4HANA on-premise, Private Cloud Edition, Public Cloud Edition.
    
3.  Handle all matching flavors: 2-way (Invoice ↔ PO), 3-way (Invoice ↔ PO ↔ GR), 4-way (Invoice ↔ PO ↔ GR ↔ Inspection).
    

* * *

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
| --- | --- | --- | --- | --- | --- |
| Touchless invoice processing rate | — | ≥ 80% of invoices auto-processed without human intervention | — | Invoice to Pay / AP Processing | user |

* * *

## Requirements

### Must-Have Requirements

**R1: EDI Invoice Ingestion**

-   **Problem to Solve**: Invoices arriving via EDI must be reliably received and parsed before any processing can begin.
    
-   **User Story**: As an AP system, I need to receive and parse EDI invoice messages so that they can be processed automatically without manual data entry.
    
-   **Acceptance Criteria**:
    
    -   Given an EDI invoice arrives on the channel, when the agent processes it, then the invoice data is extracted and structured correctly.
        
    -   Given a malformed EDI message, when the agent processes it, then it is flagged as an exception with a descriptive error.
        
-   **Priority Rank**: 1
    

**R2: Matching Flavor Selection & Execution**

-   **Problem to Solve**: Different invoice types require different matching strategies; the agent must select and execute the right one.
    
-   **User Story**: As an AP specialist, I need invoices to be matched using the correct method (2-way, 3-way, or 4-way) so that matching is accurate and consistent.
    
-   **Acceptance Criteria**:
    
    -   Given a standard PO-based invoice with no GR, when the agent matches it, then 2-way matching (Invoice ↔ PO) is applied.
        
    -   Given a PO-based invoice with goods receipt, when the agent matches it, then 3-way matching is applied.
        
    -   Given a PO-based invoice with goods receipt and quality inspection, when the agent matches it, then 4-way matching is applied.
        
-   **Priority Rank**: 2
    

**R3: Touchless Auto-Posting**

-   **Problem to Solve**: Matched invoices should be posted to SAP automatically without requiring manual AP action.
    
-   **User Story**: As an AP manager, I need successfully matched invoices to be posted to SAP automatically so that payment cycles are shortened.
    
-   **Acceptance Criteria**:
    
    -   Given a successfully matched invoice within tolerance thresholds, when the agent completes matching, then the invoice is posted to SAP with no human intervention.
        
    -   Given a posted invoice, when the agent completes, then a confirmation record is written to the audit log.
        
-   **Priority Rank**: 3
    

**R4: Exception Detection & Escalation**

-   **Problem to Solve**: Invoices that cannot be matched must not stall silently — AP specialists need timely, actionable exception notifications.
    
-   **User Story**: As an AP specialist, I need unmatched or discrepant invoices escalated to me with full context so that I can resolve them efficiently.
    
-   **Acceptance Criteria**:
    
    -   Given a matching failure or tolerance breach, when the agent detects it, then the invoice is flagged with mismatch details and routed to the AP specialist queue.
        
    -   Given an exception, when it is escalated, then the agent provides the invoice, PO, GR, and mismatch summary.
        
-   **Priority Rank**: 4
    

**R5: Cross-System SAP Support**

-   **Problem to Solve**: Organizations run different SAP editions; the agent must work across all of them without separate implementations.
    
-   **User Story**: As an IT architect, I need the agent to connect to S/4HANA on-premise, Private Cloud, and Public Cloud via their standard APIs so that a single agent deployment serves all environments.
    
-   **Acceptance Criteria**:
    
    -   Given credentials for S/4HANA on-premise, Private Cloud, or Public Cloud, when the agent connects, then it successfully calls AP posting and matching APIs.
        
-   **Priority Rank**: 5
    

* * *

## Solution Architecture

**Architecture Overview:** The agent is a Python-based AI agent following the A2A protocol. It receives parsed invoice payloads from SAP Integration Suite (which handles EDI message decoding), calls SAP S/4HANA standard AP APIs for matching and posting, and routes exceptions to human queues when needed. The agent is stateless and connects to SAP systems via configurable MCP tool bindings.

**Key Components:**

-   **AP Invoice Automation Agent** (Python, A2A protocol): core reasoning and orchestration engine
    
-   **SAP Integration Suite**: EDI channel listener and message parser; delivers structured invoice payloads to the agent
    
-   **SAP S/4HANA** (all editions): AP matching engine, invoice posting, and payment processing
    

**Integration Points:**

-   SAP Integration Suite → Agent: structured invoice payload (push, on receipt)
    
-   Agent → SAP S/4HANA: AP matching API calls, invoice posting API calls (read + write)
    
-   Agent → AP Specialist Queue: exception notifications with mismatch context (write)
    

* * *

### Agent Extensibility & Instrumentation

**Agent Extensibility:** The agent is designed with extension points so that new matching rules, tolerance configurations, or additional SAP systems can be added without rewriting core logic. The matching flavor selection logic is a pluggable component.

**Business Step Instrumentation:** All key business steps emit structured log statements for observability. Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`

* * *

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent (with human-in-the-loop for exceptions)

**Actions the system performs without human approval:**

-   Parse and validate incoming EDI invoice
    
-   Execute 2-way, 3-way, or 4-way matching against SAP
    
-   Post matched invoices to SAP automatically (within configured tolerance)
    
-   Write audit log entries for all actions
    

**Actions that require human review or approval:**

-   Invoices with matching failures or tolerance breaches
    
-   Invoices with unresolvable vendor or PO reference issues
    
-   Invoices flagged with potential duplicate detection
    

**Model or engine used:** SAP Generative AI Hub (LLM for exception reasoning and natural language escalation messages); SAP S/4HANA standard matching APIs for core matching logic.

**Knowledge & data sources accessed:**

-   SAP S/4HANA: Purchase Orders, Goods Receipts, Quality Inspection records, Vendor Master
    
-   EDI channel (via SAP Integration Suite): incoming invoice payloads
    

**Guardrails & fail-safes:**

-   Never modify financial records unless matching confidence exceeds configured tolerance threshold.
    
-   Always write an audit log entry before and after any posting action.
    
-   If SAP API call fails, hold the invoice in an exception queue rather than discarding it.
    
-   Confidence below threshold → route to AP specialist, never auto-post.
    

* * *

## Milestones

### M1: EDI Invoice Received

-   **Description**: An EDI invoice message has been successfully ingested and parsed.
    
-   **Achieved when**: The agent receives a structured invoice payload from SAP Integration Suite with all required fields present.
    
-   **Log on achievement**: `M1.achieved: EDI invoice ingested successfully, invoice_id={invoice_id}, vendor={vendor_id}`
    
-   **Log on miss**: `M1.missed: EDI invoice ingestion failed, reason={error}, raw_message_ref={ref}`
    

### M2: Invoice Validated

-   **Description**: The invoice has been validated against vendor master data and completeness checks.
    
-   **Achieved when**: All mandatory invoice fields are present, vendor exists in SAP master data, and no structural errors are detected.
    
-   **Log on achievement**: `M2.achieved: Invoice validation passed, invoice_id={invoice_id}`
    
-   **Log on miss**: `M2.missed: Invoice validation failed, invoice_id={invoice_id}, reason={reason}`
    

### M3: Matching Completed

-   **Description**: The agent has executed the appropriate matching flavor and reached a match decision.
    
-   **Achieved when**: 2-way, 3-way, or 4-way matching completes and a match result (success/failure) is determined.
    
-   **Log on achievement**: `M3.achieved: Matching completed, invoice_id={invoice_id}, match_type={type}, result=matched`
    
-   **Log on miss**: `M3.missed: Matching failed or inconclusive, invoice_id={invoice_id}, match_type={type}, reason={reason}`
    

### M4: Touchless Posting

-   **Description**: A matched invoice has been posted to SAP without human intervention.
    
-   **Achieved when**: The SAP AP posting API confirms successful document creation.
    
-   **Log on achievement**: `M4.achieved: Invoice posted touchlessly, invoice_id={invoice_id}, sap_document={doc_number}`
    
-   **Log on miss**: `M4.missed: Touchless posting did not complete, invoice_id={invoice_id}, reason={reason}`
    

### M5: Exception Escalated

-   **Description**: An invoice with matching failure or discrepancy has been routed to an AP specialist.
    
-   **Achieved when**: The exception record is written to the AP specialist queue with full mismatch context.
    
-   **Log on achievement**: `M5.achieved: Exception escalated, invoice_id={invoice_id}, exception_type={type}, assigned_to={queue}`
    
-   **Log on miss**: `M5.missed: Exception escalation failed, invoice_id={invoice_id}, reason={reason}`