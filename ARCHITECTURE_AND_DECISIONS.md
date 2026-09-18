# ARCHITECTURE_AND_DECISIONS.md
## UPI-Inspired Payment Experiment — Architecture and Decision Record

This file records the current architecture and the reasoning behind the main technical decisions.

The roadmap defines sequence and scope.

This file explains the technical structure and why specific choices were made.

---

# 1. Architecture Goal

Build one payment application with two interchangeable ledger implementations.

```text
                    Minimal Demo UI
                           ↓
                        FastAPI
                           ↓
                     PaymentService
                           ↓
                     LedgerInterface
                     /             \
                    /               \
       ConventionalLedger      BlockchainLedger
               ↓                      ↓
          PostgreSQL          Anvil + Solidity
                                      ↓
                                   web3.py
```

The application should not be duplicated for each ledger.

---

# 2. Architectural Principles

## A01 — Shared Payment Logic

Business rules belong in shared application logic wherever possible.

Examples:

```text
payment validation
amount validation
merchant validation
idempotency orchestration
status handling
response formatting
```

Ledger-specific behavior belongs behind `LedgerInterface`.

---

## A02 — Ledger Isolation

The shared domain must not depend directly on:

```text
PostgreSQL-specific types
SQL queries
Solidity types
web3.py objects
transaction receipts
blockchain addresses
```

Adapters translate between the shared domain and each implementation.

---

## A03 — Same Logical Payment

Both implementations execute the same business scenario.

```text
payer
merchant
amount
currency
payment_id
```

This is mandatory for a meaningful comparison.

---

# 3. Decision Record

## D01 — Python

**Decision:** Use Python.

**Status:** ADOPT

**Why:**
- fast prototype iteration
- strong FastAPI ecosystem
- mature testing support
- direct web3.py integration
- simple benchmark scripting

**Trade-off:**
- not the highest-performance runtime for payment infrastructure
- acceptable because this is an experimental prototype

---

## D02 — FastAPI

**Decision:** Use FastAPI as the API layer.

**Status:** ADOPT

**Why:**
- small framework surface
- clear request/response models
- easy local testing
- fits the project scale
- keeps backend development fast

**Alternatives:**
- Flask
- Django
- Node.js frameworks

**Why not selected:**
No alternative currently provides enough extra value to justify changing stack or scope.

---

## D03 — PostgreSQL

**Decision:** Use PostgreSQL for the conventional ledger.

**Status:** ADOPT

**Why:**
- transactional semantics
- atomic debit/credit
- rollback behavior
- concurrency support
- credible relational baseline for payment comparison

**Alternative: SQLite**

**Why not baseline:**
Simpler, but less useful for demonstrating transaction and concurrency behavior.

---

## D04 — Ledger Interface

**Decision:** Both ledger implementations sit behind one interface.

**Status:** ADOPT

Suggested responsibilities:

```text
get_balance(...)
execute_payment(...)
get_transaction(...)
list_transactions(...)
```

Resetting test or benchmark state belongs to test/benchmark infrastructure, not to the core runtime interface.

**Why:**
- prevents duplicate application logic
- supports fair comparison
- improves testability
- makes implementation differences explicit

---

## D05 — PaymentService

**Decision:** Shared application service coordinates payment flow.

**Status:** ADOPT

Responsibilities:

```text
validate request
check business rules
invoke selected ledger
normalize result
record application-level status
return response
```

It must not depend directly on PostgreSQL or Anvil internals.

---

## D06 — Money Representation

**Decision:** Use integer minor units.

**Status:** ADOPT

Example:

```text
100 SEK = 10000 öre
```

**Why:**
Avoid binary floating-point errors in financial values.

---

## D07 — Anvil

**Decision:** Use Anvil as the local Ethereum-compatible test blockchain.

**Status:** ADOPT

**Why:**
- local
- fast
- deterministic
- resettable
- no real money
- transaction receipts available
- gas usage visible
- low setup overhead

**Limitation:**
Anvil does not represent Ethereum mainnet latency, congestion, validator behavior, or real transaction cost.

---

## D08 — Solidity PaymentLedger

**Decision:** Use one minimal custom smart contract.

**Status:** ADOPT

Planned responsibilities:

```text
store simulated balances
execute payment
prevent duplicate payment IDs
emit transaction event
return/revert on invalid state
```

**Not included:**

```text
ERC-20 token product
DeFi logic
wallet product
public deployment
bridges
staking
NFTs
```

---

## D09 — web3.py

**Decision:** Use web3.py for backend-to-blockchain integration.

**Status:** ADOPT

**Why:**
Keeps the integration in Python and allows the same FastAPI application to call both ledger backends.

---

## D10 — Minimal UI

**Decision:** Use a thin web UI.

**Status:** ADOPT

Required functions only:

```text
select ledger
show customer balance
show merchant
show QR
enter payment amount
submit payment
show status
show latency
show transaction history
```

**Why not React by default:**
The frontend is not the research question.

---

## D11 — QR

**Decision:** Generate a real QR payload.

**Status:** ADOPT

Example:

```text
upi-demo://pay?merchant_id=M001
```

For the interview version, scan may be simulated inside the demo.

**Real camera scanning:** WATCH

---

## D12 — NFC

**Decision:** Do not implement real NFC hardware in the interview version.

**Status:** WATCH

**Reason:**
Relevant to the broader project brief, but not required to answer the ledger comparison question.

---

## D13 — Public Blockchain

**Decision:** Do not use public Ethereum/testnet as the primary experiment environment.

**Status:** AVOID for interview version

**Reason:**
Introduces network variance, external dependencies, and non-deterministic conditions.

It may be evaluated later as a secondary extension.

---

# 4. Transaction Semantics

## Conventional Completion

```text
ledger operation starts
→ DB transaction begins
→ payment executes
→ DB COMMIT succeeds
→ ledger execution successfully complete
```

## Blockchain Completion

```text
ledger operation starts
→ transaction submitted
→ included by Anvil
→ successful receipt returned
→ ledger execution successfully complete
```

For blockchain, where practical record:

```text
submission latency
confirmation latency
```

Primary comparison uses ledger-only latency:

```text
ledger operation start → successful completion boundary
```

For the exact PostgreSQL and blockchain timing definitions, and for the secondary full API end-to-end measurement, see `BENCHMARK_AND_EXPERIMENT_PLAN.md`.

Ledger execution completion is distinct from application-observed payment status. A timeout may leave the application in `PENDING` or `UNKNOWN` until reconciliation resolves the receipt to `SUCCESS` or `FAILED`.

---

# 5. Payment Safety

Both implementations must enforce:

```text
amount > 0
valid payer
valid merchant
sufficient balance
unique logical payment
no partial transfer
correct final balance
explicit transaction status
```

Repeated payment IDs must not create repeated debits.

---

# 6. Data Model Boundary

Core concepts:

```text
Customer
Merchant
Account
Payment
Transaction
PaymentStatus
LedgerResult
```

These must remain implementation-neutral.

---

# 7. Security Boundary

Interview prototype assumptions:

```text
synthetic users
synthetic balances
no real money
no bank credentials
no production private keys
Anvil test accounts only
```

No production security claims should be made from this prototype.

---

# 8. Change Rule

Architecture can change if evidence justifies it.

Every meaningful change must record:

```text
previous decision
new decision
reason
evidence
risk
affected Cards
expected benefit
```

Do not change architecture for novelty alone.

# 9. Identifier and Idempotency Semantics

```text
payment_id       = identity of the logical/business payment
transaction_id   = identity of one ledger execution; for blockchain this may map to or include the transaction hash
idempotency_key  = client/request-level duplicate-prevention key
```

Canonical relationship:

```text
idempotency_key → payment request → payment_id → ledger execution → transaction_id
```

One idempotency key identifies one logical request intent. The same key with the same canonical request payload returns the original result without another debit. The same key with a different canonical payload is rejected with HTTP 409 and internal error `IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST`. Payload comparison uses a canonical representation or stable fingerprint/hash.

This rule applies at the application/payment level to both ledger implementations.

# 10. Address and Key Boundary

Each simulated Customer or Merchant may map one-to-one to an Anvil test address. The mapping is application-managed and the backend controls signing. No private keys are exposed to the UI. This is a custodial/testing model, not production wallet architecture or production-safe key management.

# 11. Atomicity and Failure Strategy

The planned PostgreSQL baseline uses `READ COMMITTED`, `SELECT ... FOR UPDATE`, and deterministic locking of relevant account rows:

```text
BEGIN
lock account rows in deterministic order
validate balance and idempotency/payment state
debit payer
credit merchant
persist payment and transaction
COMMIT
```

Failure causes `ROLLBACK`. Controlled failure injection will verify rollback after a simulated debit and before completion; infrastructure will not be intentionally corrupted.

The Solidity ledger will use controlled reverts for invalid conditions and processed `payment_id` values to reject replay. A lost response is reconciled by receipt/status lookup; it is not treated as failure and must not trigger a blind second submission.

# 12. Ambiguous Blockchain Status

If a transaction may have executed but the application times out, retain the transaction hash when available and mark the payment `PENDING` or `UNKNOWN`. Receipt reconciliation resolves it to `SUCCESS`, `FAILED`, or an unresolved state that remains `PENDING`/`UNKNOWN`. Application idempotency and contract-level processed-payment tracking provide separate replay protection.

# 13. Reproducible Local Environment

Docker Compose is the canonical planned local environment:

```text
FastAPI + PostgreSQL + Anvil
```

The benchmark runner should use the same containerized environment and internal network where practical. PostgreSQL data should use a Docker named volume rather than a macOS bind mount. Results represent a local containerized experiment and must not be generalized to production PostgreSQL or Ethereum mainnet performance.

## Runtime / Deployment Structure

This is separate from the logical application architecture above:

```text
Docker Compose
├── FastAPI
├── PostgreSQL
└── Anvil
```
