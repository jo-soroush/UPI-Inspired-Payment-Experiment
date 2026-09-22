# PROJECT_CONTROL.md
## UPI-Inspired Payment Experiment — Live Project Control

This file is the single source of truth for the current execution state of the project.

It should stay short and current.

---

# 1. Project Status

```text
Project: UPI-Inspired Payment Experiment
Overall Status: IN_PROGRESS
Active Card: NONE
Last Completed Card: C07
Next Allowed Card: C08
Execution Authorization: NONE
C02 Authorization: CLOSED/COMPLETED
C03 Authorization: CLOSED/COMPLETED
C04 Authorization: CLOSED/COMPLETED
C05 Authorization: CLOSED/COMPLETED
C06 Authorization: CLOSED/COMPLETED
C07 Authorization: CLOSED/COMPLETED
C08 Authorization: NOT_GRANTED
Current Branch: main
Current Blocker: NONE
Current Work: C07 Blockchain Ledger — delivery COMPLETE; C08 sequence-eligible only
C06 Phase 1 Verification: PASS
C06 Final Independent Re-Audit: PASS
C06 Findings: NONE
C06-A01: RESOLVED
C06-A02: RESOLVED
C06-A03: RESOLVED
C06 Exit Gate: PASS
C06 Ready for Human Delivery Approval: YES
C06 Human Delivery Approval: GRANTED
C06 Git Delivery: COMPLETE
C06 Card Status: COMPLETE
C07 Card Status: COMPLETE
C07 Phase 1 Verification: PASS
C07 Independent Audit: FAIL (historical)
C07 Final Independent Re-Audit: PASS (before C07-A07 discovery)
C07-A01: CLOSED
C07-A02: CLOSED
C07-A03: CLOSED
C07-A04: CLOSED
C07-A05: CLOSED
C07-A06: CLOSED
C07-A07 Independent Re-Audit: PASS
C07-A07: CLOSED
C07-A08 Remediation: PASS
C07-A08: CLOSED
C07-A09 Remediation: PASS
C07-A09: CLOSED
C07 Remediation: PASS
C07 Second Remediation: PASS
C07 Final Independent Re-Audit (Post A08/A09): PASS
C07 New Findings: NONE
C07 Exit Gate: PASS
C07 Ready for Human Delivery Approval: YES
C07 Human Delivery Approval: GRANTED
C07 Git Delivery: COMPLETE
C07 Delivery Commit: d22d48a9253a1cdca86e311620365915d6a04a55
C05 Final Independent Re-Audit: PASS
C05-A01: RESOLVED
C05-A02: RESOLVED
C05-A03: RESOLVED
C05 Findings: NONE
C05 Exit Gate: PASS
C05 Ready for Human Delivery Approval: YES
C05 Human Delivery Approval: GRANTED
C05 Git Delivery: delivery performed by this task
Baseline Readiness: COMPLETE
Interview Demo Ready: NO
Benchmark Complete: NO
```

Next Allowed Card indicates sequence eligibility only. Starting that Card still requires explicit human approval for that specific Card.

---

# 2. Card Status

| Card | Title | Status |
|---|---|---|
| C01 | Project Baseline & Experimental Design | COMPLETE |
| C02 | Domain Models | COMPLETE |
| C03 | Conventional Ledger | COMPLETE |
| C04 | Payment Safety & Failure Handling | COMPLETE |
| C05 | QR Payment Initiation | COMPLETE |
| C06 | Minimal Demo UI | COMPLETE |
| C07 | Blockchain Ledger | COMPLETE |
| C08 | Benchmark & Comparative Experiment | NOT_STARTED |
| C09 | Interview Demo & Engineering Report | NOT_STARTED |

---

# 3. Current Planned Technical Baseline

```text
Backend: FastAPI
Language: Python
Conventional Ledger: PostgreSQL
Blockchain Environment: Anvil
Smart Contract: Minimal Solidity PaymentLedger
Blockchain Integration: web3.py
Money Representation: integer öre
UI: minimal TypeScript web UI
QR: real generated QR, simulated scan acceptable
Benchmark Evidence: JSON + CSV + raw measurements
Execution Environment: Docker Compose (PostgreSQL service implemented; C04 FastAPI payment boundary implemented; containerized FastAPI and Anvil remain planned)
```

---

# 4. Current Architecture

Canonical detailed architecture and technical decisions: `ARCHITECTURE_AND_DECISIONS.md`.
Planned architecture summary: UI → FastAPI → PaymentService → LedgerInterface → ConventionalLedger or BlockchainLedger.

---

# 5. Current Guardrails

```text
One Card at a time
STOP on failure
Correctness before performance
No invented evidence
Same payment flow for both ledgers
Same benchmark workload
No real financial data
No real money
No public blockchain for interview version
Minimal UI only
No scope expansion without documented change
```

---

# 6. Current Research Question

**Does a blockchain-based ledger provide meaningful advantages over a conventional transactional ledger for a small UPI-inspired instant-payment network?**

---

# 7. Primary Demo Scenario

```text
Customer C001 = 1000 SEK
Merchant M001 = 0 SEK

Customer scans merchant QR
→ pays 100 SEK

Expected:

Customer C001 = 900 SEK
Merchant M001 = 100 SEK
Transaction = SUCCESS
```

This same logical payment must work with:

```text
ConventionalLedger
BlockchainLedger
```

---

# 8. Current Benchmark Baseline

```text
Primary metric: ledger-only latency
Secondary metric: full API end-to-end latency
Workloads: 10 / 100 / 500 / 1000
Measured runs: 5
Mode: sequential
Canonical methodology: BENCHMARK_AND_EXPERIMENT_PLAN.md
```

---

# 9. Change Log

Record only meaningful baseline changes.

| Date | Change | Reason | Evidence |
|---|---|---|---|
| Initial | Project control created | Establish execution baseline | Roadmap + evidence map + AGENTS.md |
| 2026-09-18 | C01 started | Explicit human authorization for C01 Phase 1 | C01 pre-implementation check |
| 2026-09-18 | C01 completed | Controlled initial baseline delivery | `f4fafcf77f43fe137a9b12398f1995f60dacea19` |
| 2026-09-18 | C02 started | Explicit human authorization for C02 Phase 1 | C02 pre-implementation check |
| 2026-09-18 | C02 completed | Independent re-audit, Exit Gate, delivery, and push passed | Implementation delivery: `20098e9c4782d38137fb047711314c2b738de373`; completion evidence/state: `cf4977b9e4364bd5dfef7b788fba7cd363b3affa` |
| 2026-09-19 | C03 started | Explicit human authorization for C03 Phase 1 | C03 start-and-implement instruction after read-only preflight PASS |
| 2026-09-19 | C03 completed | Human-approved delivery after independent audit PASS and Exit Gate PASS | Implementation delivery: `e626bc10eab7a33c5a03042e41a706d989168548`; completion evidence/state: subsequent documentation record |
| 2026-09-20 | C04 started | Explicit human authorization for C04 Phase 1 after the read-only preflight decisions were resolved | C04 implementation instruction; authorization is limited to C04 |
| 2026-09-20 | C04 completed | Human delivery approval granted after final validation, final independent documentation confirmation PASS, and Exit Gate PASS; controlled delivery completed on `main` | C04 delivery status: COMPLETE; immutable delivery SHA is determined by Git and reported in the final delivery output; no C05 authorization or advancement |
| 2026-09-20 | C05 started | Explicit human authorization for C05 Phase 1 after canonical QR contract lock and independent confirmation | C05 implementation instruction; authorization is limited to C05 and does not authorize C06 |
| 2026-09-20 | C05 Phase 1 implemented | QR implementation, deterministic contract tests, C03/C04 regressions, full suite, evidence update, and self-audit passed | C05 remains IN_PROGRESS; independent audit, human delivery approval, and Git delivery are pending |
| 2026-09-20 | C05-A01 remediated | Formal independent audit found raw URI control-character normalization; bounded parser guard and regression evidence completed | C05 remains IN_PROGRESS; independent re-audit, human delivery approval, and Git delivery are pending |
| 2026-09-21 | C05-A02 remediated | Independent re-audit found malformed UTF-8 percent decoding and decoded control-character acceptance; bounded strict-decoding and regression evidence completed | C05 remains IN_PROGRESS; independent re-audit, human delivery approval, and Git delivery are pending |
| 2026-09-21 | C05-A03 remediated | Independent re-audit found empty-fragment-delimiter acceptance; bounded raw-fragment guard and regression evidence completed | C05 remains IN_PROGRESS; independent re-audit, human delivery approval, and Git delivery are pending |
| 2026-09-21 | C05 final independent re-audit passed | C05-A01, C05-A02, and C05-A03 independently verified resolved; no findings remained | C05 remains IN_PROGRESS pending explicit human delivery approval and controlled Git delivery |
| 2026-09-21 | C05 completed | Human delivery approval granted after final validation and independent re-audit PASS; controlled Git delivery performed by this task | C05 delivery status: COMPLETE; final immutable SHA reported in delivery output |
| 2026-09-21 | C06 authorized recovery and verification started | Explicit human authorization adopts the pre-existing uncommitted C06 candidate for formal inspection and verification; it does not retroactively authorize its earlier creation | Committed baseline `267ef0644b692e3322cacf93cb282d9b409b1e46` had C06 `NOT_STARTED` / `NOT_GRANTED`; no prior C06 delivery or approval existed |
| 2026-09-21 | C06 independent audit failed | Independent spec-based audit found C06-A01 (bootstrap `hostaddr` remote-target bypass) and C06-A02 (confirmed payment success overwritten by refresh failure) | C06 remains IN_PROGRESS; Exit Gate and delivery approval remain pending |
| 2026-09-21 | C06-A01/A02 remediated | Bounded fixes and deterministic regressions completed for both findings | Independent re-audit is required; C06 remains IN_PROGRESS |
| 2026-09-21 | C06 independent re-audit failed | The re-audit confirmed C06-A01/A02 resolved but found C06-A03: libpq `service=`/environment target resolution could bypass the destructive bootstrap target guard | C06 remains IN_PROGRESS; Exit Gate and delivery approval remain pending |
| 2026-09-21 | C06-A03 remediated | Bootstrap now uses an explicit validated local target and suppresses implicit libpq target environment during destructive operations | Independent re-audit is required; C06 remains IN_PROGRESS |
| 2026-09-21 | C06 final independent re-audit passed | C06-A01, C06-A02, and C06-A03 independently verified resolved; no findings remained; Exit Gate passed | C06 remains IN_PROGRESS pending explicit human delivery approval and controlled Git delivery |
| 2026-09-21 | C06 completed | Human delivery approval granted after final independent re-audit PASS and Exit Gate PASS; controlled delivery completed on `main` | C06 status: COMPLETE; C07 remains NOT_STARTED/NOT_GRANTED; immutable delivery SHA is reported by Git after commit |
| 2026-09-21 | C07 Phase 1 authorized | Explicit human authorization granted for C07 implementation and deterministic verification only | C07 is IN_PROGRESS; C08 and Git delivery remain unauthorized |
| 2026-09-21 | C07 Phase 1 implemented | Blockchain contract, adapter, durable recovery journal, transport selector, deterministic verification, real-Anvil/browser smoke, and self-audit passed | C07 remains IN_PROGRESS pending independent audit; C08, approval, and Git delivery remain unauthorized |
| 2026-09-21 | C07 independent audit failed | Independent spec-based audit found C07-A01 terminal replay downgrade, C07-A02 unrestricted bootstrap targets, C07-A03 unsafe receipt classification, C07-A04 duplicate participant addresses, and C07-A05 stale ledger-switch presentation | C07 remains IN_PROGRESS; Exit Gate, human approval, and Git delivery remain pending |
| 2026-09-21 | C07-A01-A05 remediated | Bounded fixes and deterministic regressions passed for all five findings, including fresh real-Anvil and browser-switch verification | Independent re-audit is required; C07 remains IN_PROGRESS and C08 remains unauthorized |
| 2026-09-22 | C07 independent re-audit failed | A01/A03 remained open because stale resolver snapshots could overwrite terminal journal state; A06 found unrestricted runtime RPC composition. A02/A04/A05 closed. | C07 remains IN_PROGRESS; second bounded remediation required; C08, approval, and Git delivery remain unauthorized. |
| 2026-09-22 | C07-A01/A03/A06 second remediation | PostgreSQL terminal-state compare-and-set, stale resolver races, and runtime local-Anvil identity/chain validation passed deterministic verification. | Independent re-audit is required; C07 remains IN_PROGRESS and C08 remains unauthorized. |
| 2026-09-22 | C07-A07 remediated | Manual post-final-audit file review found that the C07 test harness used an unvalidated environment DSN for destructive PostgreSQL fixtures. Module-level fail-closed validation now permits only the explicit loopback `upi_payment_test` URI before any test database activity. | Historical remediation record; the subsequent independent A07 re-audit passed. C07 remained IN_PROGRESS; C08 remained NOT_STARTED/NOT_GRANTED. |
| 2026-09-22 | C07-A07 independent re-audit passed | Independent controlled module-load probes confirmed unsafe C07 test DSNs reject before any PostgreSQL connection; no A07 technical finding remained. | C07 remained IN_PROGRESS; later manual review found A08/A09. |
| 2026-09-22 | C07-A08/A09 remediated | Payment-intent ledger capture/control lock prevents mixed UI context; C06 test-module DSN validation now fails closed before fixture database activity. | Final independent re-audit is required; C07 remains IN_PROGRESS, human delivery approval/Git delivery are pending, and C08 remains NOT_STARTED/NOT_GRANTED. |
| 2026-09-22 | C07 Final Independent Re-Audit (Post A08/A09) passed | Independent re-execution of full validation confirmed C07-A01 through C07-A09 CLOSED, new findings NONE, and Exit Gate PASS | C07 remains IN_PROGRESS; Human Delivery Approval remains NOT_GRANTED; Git Delivery remains NOT_PERFORMED; C08 remains NOT_STARTED/NOT_GRANTED; Ready for Human Delivery Approval: YES. |
| 2026-09-22 | C07 Human Delivery Approval granted | Explicit human authorization for controlled C07 Git delivery only | C07 Git delivery is being performed by this task; C08 remains NOT_STARTED/NOT_GRANTED; CLAUDE.md excluded from delivery scope. |

| 2026-09-22 | C07 completed | Controlled delivery completed on `main` after final independent re-audit PASS and human approval | C07 status: COMPLETE; delivery commit: `d22d48a9253a1cdca86e311620365915d6a04a55`; C08 remains NOT_STARTED/NOT_GRANTED; no automatic advancement occurred |

---

# 10. Update Rule

Update this file whenever:

```text
a Card starts
a Card completes
a blocker appears
a baseline technology changes
a benchmark rule changes
a delivery occurs
```

Do not turn this file into a long history log.

Detailed Card history belongs in:

```text
PAYMENT_CARD_EVIDENCE_MAP.md
```
