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
Last Completed Card: C05
Next Allowed Card: C06
Execution Authorization: NONE
C02 Authorization: NOT_GRANTED
C03 Authorization: NOT_GRANTED
C04 Authorization: NOT_GRANTED
C05 Authorization: CLOSED/COMPLETED
C06 Authorization: NOT_GRANTED
Current Branch: main
Current Blocker: NONE
Current Work: NONE — C05 completed; C06 sequence-eligible only
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
| C06 | Minimal Demo UI | NOT_STARTED |
| C07 | Blockchain Ledger | NOT_STARTED |
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
