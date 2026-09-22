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

Implemented C07 responsibilities:

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

**Decision:** Use a minimal TypeScript web UI as the C06 presentation and payment-initiation layer.

**Status:** ADOPT

The TypeScript UI calls the existing FastAPI boundary:

```text
TypeScript UI
→ FastAPI
→ PaymentService
→ LedgerInterface
→ ConventionalLedger or BlockchainLedger
```

The UI remains outside the core research question and must not duplicate payment correctness, balance rules, merchant validation, idempotency, payment fingerprinting, persistence, ledger execution, rollback, or blockchain semantics. Those remain backend responsibilities.

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

**Framework boundary:**
React is not required by default. C06 should choose the smallest frontend structure that satisfies the demo; any framework selection must be justified by C06 evidence and explicitly approved.

The frontend is not the research question.

### Historical C06 Contract Lock (Pre-Implementation)

The following contract was locked before C06 implementation. It remains the design basis for the delivered C06 UI; it is retained here as historical decision evidence and does not describe current authorization.

**Frontend baseline:** Plain TypeScript plus HTML and CSS, compiled with `tsc`, with no framework selected by default. FastAPI serves the compiled UI and static assets on the same origin as the API. A separate frontend runtime server and CORS middleware are not required for the primary interview-demo path.

**Fixed demo context:** The UI presents `C001` and `M001` as fixture identities only, not as a customer or merchant directory. It begins from `C001 = 100000` öre and `M001 = 0` öre, submits `10000` öre, and demonstrates `90000` / `10000` öre with `SUCCESS`.

**SEK presentation transport:** The UI accepts a non-negative decimal string matching exactly:

```text
^(0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$
```

The sole decimal separator is `.`. Whitespace, signs, commas, grouping separators, scientific notation, and more than two fractional digits are rejected as malformed presentation input. The UI pads a missing fractional component to `00` and a one-digit component to two digits, concatenates the normalized decimal text into öre, and converts only that integer string to the JSON integer sent to FastAPI. It must not use binary floating-point multiplication. The UI rejects values above the JavaScript safe-integer range before transport; C04/backend validation of amount and all payment rules remains authoritative.

Examples:

```text
100    → 10000 öre
100.0  → 10000 öre
100.00 → 10000 öre
```

**Request identities:** The existing `POST /payments` request requires distinct `payment_id` and `idempotency_key` fields. The UI may create opaque values with `crypto.randomUUID()` for one new user payment intent, but must not compute the canonical fingerprint or decide replay/conflict outcomes. It must not automatically retry an ambiguous request. If a later C06 retry affordance is added, it must reuse the exact original request payload and identifiers so C04 remains authoritative.

**Implemented thin FastAPI UI surface:**

```text
POST /payments
  existing C04 request/response contract; unchanged

GET /accounts/{owner_id}/balance
  → { "owner_id": "C001", "currency": "SEK", "balance_ore": 100000 }

GET /transactions
  → { "transactions": [
        {
          "transaction_id": "...",
          "payment_id": "...",
          "ledger_type": "ConventionalLedger",
          "status": "SUCCESS",
          "timestamp": "ISO-8601 timestamp"
        }
      ] }

GET /merchants/{merchant_id}/qr
  → image/png generated by the existing C05 QR adapter

GET / and static assets
  → compiled TypeScript UI served by FastAPI
```

Balance and history reads must pass through `PaymentService` to the existing `LedgerInterface.get_balance()` and `LedgerInterface.list_transactions()` operations. The API/UI layer must not query PostgreSQL directly. The history route is deliberately unfiltered, unpaginated, and limited to the deterministic demo history; it does not create a second transaction model or reporting system.

The QR route invokes the existing C05 generator and exposes a browser-displayable `image/png`; TypeScript only displays it. C06 does not reimplement QR generation or parsing, and its merchant-only payload remains `upi-demo://pay?merchant_id=M001`. The existing C05/zxing-cpp image buffer must be evaluated first for browser-image conversion. A new image-encoding dependency is permitted only if that proof demonstrates it is necessary and records the justification during authorized C06 work.

**Demo bootstrap:** An explicit local-only demo bootstrap, outside browser-accessible HTTP routes, must initialize the schema and reset/load only the deterministic C001/M001 fixture state before the interview flow. It must operate only against the local demo database, be deliberately invoked for demo preparation, and leave C04 payment execution and rollback behavior unchanged. A browser-accessible reset endpoint is not part of C06.

**Historical C06 ledger state:** Before C07 implementation, Conventional was the only functional ledger and Blockchain was displayed as unavailable. C06 did not send a ledger selector to `POST /payments`, simulate a result, create a receipt, or expose blockchain data.

**Current C07 presentation state:** The same minimal TypeScript UI sends `ledger=conventional|blockchain` only as FastAPI transport metadata. Each payment intent captures its selected ledger once; its payment request and post-payment balance/history refresh use that same ledger while both controls are disabled. The UI still does not implement payment correctness, receipt handling, or blockchain semantics. A browser-observed request duration remains labeled `Local API request time` or `UI-observed request duration`; it is not ledger latency, benchmark latency, blockchain confirmation time, or production latency. C08 remains the canonical source for benchmark timing.

---

## D11 — QR

**Decision:** Generate a real QR payload using the strict C05 merchant-URI contract.

**Status:** ADOPT

The only canonical C05 merchant QR payload is:

```text
upi-demo://pay?merchant_id=<single-non-empty-merchant-id>
```

Example:

```text
upi-demo://pay?merchant_id=M001
```

C05 parsing is strict: scheme `upi-demo`, authority/host `pay`, empty path, exactly one non-empty `merchant_id` query parameter, no duplicate or additional query parameters, and no fragment. Malformed payloads, wrong schemes, wrong authorities/hosts, and missing merchant IDs are rejected. C05 adds no merchant-ID regex beyond existing project/domain validation.

The QR contains merchant identity only. Amount, payer ID, payment ID, idempotency key, status, transaction ID, ledger choice, and persistence information remain outside the QR. Structured JSON is not an equivalent C05 payload.

For the interview version, scan may be simulated inside the application or test path; real camera integration is not required.

The QR layer ends after parsing and returning `merchant_id`. The decoded value enters the existing payment boundary:

```text
QR initiation
→ merchant_id
→ FastAPI/application boundary
→ selected PaymentService
→ selected LedgerInterface
→ ConventionalLedger or BlockchainLedger
```

Ledger selection is transport/composition metadata carried alongside the payment request, exactly as decided for C07 (see §14, C07 Architecture Decision Lock); it is not encoded in, derived from, or read out of the QR payload, which remains the same merchant-only C05 contract regardless of which ledger the request is routed to. Unknown merchants are rejected by the existing C04 account-validation behavior. C05 does not implement a merchant database, payment engine, or ledger behavior.

C05 reuses the delivered C04 payment-safety path and does not duplicate payment identity, idempotency, fingerprinting, replay, duplicate, conflict, balance, persistence, transaction, rollback, or error semantics.

Delivered C05 uses `zxing-cpp` for real QR generation and internal/test decoding.

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

The delivered C04 implementation had one execution context, `conventional`. Its historical statement that `idempotency_key` is globally unique means globally unique within that sole ConventionalLedger execution namespace; C04 runtime semantics and storage are unchanged by this decision.

For implemented C07 work, `ConventionalLedger` and `BlockchainLedger` are alternative experimental ledger contexts, not simultaneous financial settlement rails. Their execution namespaces are `ledger_type=conventional` and `ledger_type=blockchain`. Within either namespace, the C04 rules remain unchanged: the same idempotency key and canonical request returns or reconciles the original result without a second transfer; the same key with a different fingerprint raises `IdempotencyConflictError`; conflicting reuse of a payment ID raises `PaymentConflictError`; and a processed payment ID cannot execute a second transfer.

`payment_id` and `idempotency_key` are unique only as the pairs `(ledger_type, payment_id)` and `(ledger_type, idempotency_key)`. The same raw identifier may therefore exist once in each distinct namespace as two separate experimental executions. One namespace's journal or state must not mutate, satisfy, or reconcile the other namespace's identifiers. This is valid only because the contexts are alternative and independently reset for the experiment; it is not a production multi-rail settlement design. A future real multi-rail system would need a global coordinator, which is out of scope.

The immutable canonical request payload is exactly:

```text
payment_id
payer_id
merchant_id
amount
currency
```

The idempotency key, ledger selector, and mutable or transport-specific fields are excluded from the payload fingerprint. Ledger selection remains outside `Payment`, `PaymentRequest` canonical payload, the fingerprint, and `LedgerInterface`. `PaymentService` owns deterministic canonicalization so the rule remains ledger-neutral; each ledger adapter owns its technology-specific atomic coordination. PostgreSQL must enforce concurrency-safe coordination rather than relying on a Python-only pre-check.

The same ledger-neutral canonicalization function is reused during the bounded C03-to-C04 PostgreSQL schema initialization so already-committed C03 payments receive derived fingerprints and idempotency bindings without changing their balances, history, or business data. Inconsistent legacy key bindings fail initialization transactionally rather than being guessed or overwritten.

Reusing a completed `payment_id` with the same canonical payload returns its original logical result without another execution. Reusing it with a different canonical payload is a conflict. The API maps both identifier conflicts to HTTP 409 while keeping HTTP concepts outside the ledger adapter.

For C07, application-level request coordination is durably recorded in a small PostgreSQL blockchain operation journal scoped to the `blockchain` execution namespace. It records the idempotency key, canonical request fingerprint, payment ID, transaction hash, sender identity/address, nonce where required, lifecycle/status, and enough signed-transaction linkage to recover safely. This journal is not a second financial ledger and is never authoritative for blockchain balances; `PaymentLedger` remains authoritative for simulated balances and processed payment IDs. PostgreSQL and Ethereum/Anvil do not share one ACID transaction, so the design uses durable operation state, deterministic transaction identity, reconciliation, and exact-transaction recovery rather than claiming cross-system atomicity.

# 10. Address and Key Boundary

Each simulated Customer or Merchant maps deterministically one-to-one to a controlled Anvil test address. The mapping is application-managed and the backend controls signing. For a customer payment, `BlockchainLedger` signs locally with the deterministic Anvil test private key associated with the payer; the contract verifies that `msg.sender` is authorized for the debited payer identity. No private keys are exposed to the UI or placed in Payment/domain objects. This is a custodial/testing model, not production wallet architecture or production-safe key management.

# 11. Atomicity and Failure Strategy

The delivered C03 PostgreSQL baseline uses `READ COMMITTED`, `SELECT ... FOR UPDATE`, and deterministic locking of relevant account rows:

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

The Solidity ledger uses controlled reverts for invalid conditions and processed `payment_id` values to reject replay. Anvil/EVM transaction atomicity is limited to contract state: a revert leaves balances and processed-payment state unchanged. A lost response is reconciled by receipt/status lookup; it is not treated as failure and does not trigger a blind second submission.

# 12. Ambiguous Blockchain Status

For C07, the backend constructs and signs the exact transaction before broadcast, derives its transaction hash, and durably records a prepared operation before treating submission as complete. The journal lifecycle is semantically `PREPARED`, `SUBMITTED`, `SUCCESS`, `FAILED`, or `UNKNOWN`.

If submission or receipt status is ambiguous, retain the transaction hash and mark the ledger-neutral payment `PENDING` or `UNKNOWN`. Reconciliation first inspects the journal, transaction hash, Ethereum transaction/receipt state, and contract processed-payment state. It resolves to `SUCCESS`, `FAILED`, or an unresolved state that remains `PENDING`/`UNKNOWN`; it never builds a new transaction for the unresolved logical payment. If recovery needs rebroadcast, it may broadcast only the exact persisted signed raw transaction with the same transaction hash. Application idempotency and contract-level processed-payment tracking provide separate replay protection.

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

# 14. C07 Architecture Decision Lock

## Ledger Selection

Ledger choice is a FastAPI transport/composition concern, above `PaymentService`:

```text
FastAPI
→ ledger/service registry
→ selected PaymentService
→ selected LedgerInterface implementation
```

The implemented registry contains `conventional → PaymentService(ConventionalLedger)` and `blockchain → PaymentService(BlockchainLedger)`. C07 selection uses `ledger=conventional|blockchain` at the FastAPI transport boundary. Omitted selection remains backward-compatible conventional behavior. The selector applies to payment and ledger-dependent demo reads; merchant QR identity remains ledger-independent. `Payment`, `PaymentRequest` canonical payload, request fingerprint, and `LedgerInterface` method signatures remain ledger-neutral and unchanged. C07 is `COMPLETE`: its final independent re-audit passed, `C07-A01` through `C07-A09` are `CLOSED`, and controlled Git delivery completed at `d22d48a9253a1cdca86e311620365915d6a04a55`.

## PaymentLedger and Administrative Authority

`PaymentLedger` is the minimal on-chain authority for known-participant registration, deterministic application-identity-to-authorized-address mapping, integer-öre simulated balances, balance reads, payment execution, processed-payment-ID reads/protection, and payment-event evidence. It may retain a payment fingerprint/hash for replay/conflict inspection; request-level idempotency keys remain off-chain in the operation journal.

The contract defensively rejects unknown payer or merchant, zero amount, insufficient funds, unauthorized payer signer, and processed payment-ID replay. Negative amounts remain impossible at the Solidity `uint` boundary and remain rejected by the existing application/domain boundary. A failed/reverted payment must not partially change balances or mark the payment successful.

Administrative fixture setup uses one owner. OpenZeppelin `Ownable` is the preferred minimal baseline for account registration, initial balance seeding, and other strictly administrative fixture operations. Runtime payment execution uses the payer's signer and does not require an administrator to move funds. Fresh deterministic Anvil state or redeployment is preferred for reset; unrestricted runtime reseeding is not allowed. `AccessControl`, `AccessManager`, multisig, DAO governance, production-wallet infrastructure, and other complex authorization systems are out of scope.

## Completion and Evidence Boundary

Blockchain payment success means a successful Ethereum transaction receipt with successful receipt status. The transaction hash is the canonical blockchain transaction identifier exposed through ledger-neutral result and history representations. Raw Web3 objects remain inside `BlockchainLedger`.

C07 retains factual execution metadata—transaction hash, receipt status, gas used, submission timestamp, and confirmation timestamp—for later C08 work. C07 does not aggregate those facts, run workloads, or draw benchmark conclusions.

# 15. C08 Benchmark Implementation Boundary

C08 composes a benchmark-only transparent timing adapter around each existing
`LedgerInterface` implementation. Requests still traverse the existing
FastAPI → `PaymentService` → ledger path; no payment, fingerprint, domain,
conventional-ledger, blockchain-ledger, journal, API, or contract semantics are
changed for measurement. The adapter's primary interval wraps only
`execute_payment`, whose successful return already follows PostgreSQL commit or
successful local-Anvil receipt. An in-process ASGI request/response interval is
recorded separately as the secondary API metric.

The fixed C08 dataset is `C001`–`C020 = 100000` öre and `M001`–`M005 = 0` öre.
The sequential benchmark sequence uses a constant `1000` öre transfer. This is
distinct from the 100 SEK presentation scenario: repeating that presentation
amount for the prescribed 1000-payment workload would exhaust the fixed
customer dataset. The 10 SEK benchmark amount was selected before measured
execution, applied identically to both ledgers, and does not change the shared
positive-integer payment semantics.

Conventional reset recreates the exact PostgreSQL fixture. Blockchain reset
clears the operation journal and deploys a fresh contract with all 25
participants registered and seeded, so both active on-chain balances and
processed-payment identity are clean. Reset, deployment, seed, initial-state
verification, warm-up, final-state verification, and replay verification are
outside measured timing.

Normalized differential comparison retains payment status, payer and merchant
balance deltas, history linkage, replay outcome/balance stability, and value
conservation. It excludes transaction/hash identity, gas, receipt/event facts,
and timing. Any mismatch is a failed comparison and retains the logical
workload plus both raw and normalized outcomes.

C08 measured evidence and qualitative analysis live under
`evidence/benchmarks/`. Local Anvil results are not evidence for Ethereum
mainnet latency, public congestion, gas price, validator finality, or production
operations. C08 implementation, measured execution, self-audit, and final
independent closure re-audit are `PASS`; findings are `NONE` and the Exit Gate
is `PASS`. Human delivery approval was granted and controlled Git delivery is
complete. C08 is `COMPLETE`; C09 remains `NOT_STARTED / NOT_AUTHORIZED`.
