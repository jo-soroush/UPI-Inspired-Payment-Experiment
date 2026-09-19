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
Last Completed Card: C03
Next Allowed Card: C04
Execution Authorization: NOT_GRANTED
C02 Authorization: NOT_GRANTED
C03 Authorization: NOT_GRANTED
Current Branch: main
Current Blocker: NONE
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
| C04 | Payment Safety & Failure Handling | NOT_STARTED |
| C05 | QR Payment Initiation | NOT_STARTED |
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
UI: minimal web UI
QR: real generated QR, simulated scan acceptable
Benchmark Evidence: JSON + CSV + raw measurements
Execution Environment: Docker Compose (C03 PostgreSQL service implemented; FastAPI and Anvil remain planned)
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
| 2026-09-19 | C03 completed | Human-approved delivery after independent audit PASS and Exit Gate PASS | Delivery commit SHA recorded in the subsequent completion-evidence record |

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
