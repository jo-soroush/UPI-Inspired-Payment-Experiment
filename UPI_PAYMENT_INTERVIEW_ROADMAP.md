# UPI-Inspired Payment Experiment
## Interview Roadmap, Risk Controls, and Guardrails

**Purpose:** Build a small, interview-ready payment prototype that demonstrates technical reasoning, payment-system design, experimental comparison, and disciplined scope control.

**Source basis:** This roadmap was informed by the external project brief identified as id24 and provided to the project. That brief is not stored as a repository canonical file; the repository baseline below is self-contained and must not depend on accessing it during implementation.

---

## 1. Project Goal

Build one small payment scenario and implement it with two alternative ledger approaches:

1. **Conventional Ledger**
   - FastAPI
   - Application/payment service
   - PostgreSQL

2. **Blockchain-Based Ledger**
   - Same payment flow
   - Same domain rules
   - Same API contract where practical
   - Alternative ledger implementation

Then compare the two approaches using a fixed and repeatable experimental methodology.

The project is not intended to become a production banking platform. It is an engineering experiment and interview demonstration.

---

## 2. Core Demonstration Scenario

The primary end-to-end flow is intentionally small:

```text
Customer balance: 1000 SEK
        ↓
Customer scans merchant QR
        ↓
Customer enters / confirms 100 SEK
        ↓
Payment request is submitted
        ↓
Ledger processes transfer
        ↓
Customer balance: 900 SEK
Merchant balance: 100 SEK
        ↓
Transaction status: SUCCESS
        ↓
Transaction is visible in history
```

This exact scenario must be runnable against both ledger implementations.

---

## 3. Research Question

### Primary question

**Does a blockchain-based ledger provide meaningful advantages over a conventional transactional ledger for a small UPI-inspired instant-payment network?**

### Comparison dimensions

The experiment will compare:

- Speed / latency
- Throughput
- Cost
- Complexity
- Security model
- Scalability
- Auditability
- Failure handling
- Operational burden

The project must not assume in advance that blockchain is better.

---

## 4. Scope

### In Scope

- Customer identity
- Merchant identity
- Account / balance
- Payment
- Transaction record
- Instant customer-to-merchant payment
- QR-based payment initiation
- Transaction history
- Conventional ledger
- Blockchain-based ledger
- Shared payment interface
- Error handling
- Duplicate-payment protection
- Basic atomicity / consistency controls
- Simple demo UI
- Benchmarking
- Comparison report
- Interview-ready documentation

### Explicitly Out of Scope for the Interview Version

- Real money
- Real banking integration
- BankID
- Card networks
- Production KYC / AML
- Production fraud detection
- Native mobile applications
- Complex wallet infrastructure
- Public token launch
- Cryptocurrency speculation
- Complex smart-contract ecosystems
- High-scale production infrastructure
- Real NFC hardware integration
- Production-grade identity verification
- Full distributed banking settlement

These can be discussed as future extensions, but they must not block the interview prototype.

---

# 5. Architecture Principle

The architecture must isolate payment logic from ledger technology.

```text
                    Simple Demo UI
                          ↓
                       FastAPI
                          ↓
                    Payment Service
                          ↓
                    Ledger Interface
                    /              \
                   /                \
      ConventionalLedger      BlockchainLedger
              ↓                      ↓
          Database              Blockchain /
                                local chain
```

The `PaymentService` must not know the internal implementation details of the selected ledger.

This separation is critical because the research question is about comparing ledger alternatives without rebuilding the whole application twice.

---

# 6. Core Guardrails

## G01 — One Payment Flow

Both architectures must execute the same logical payment scenario.

No architecture receives an easier or more favorable workload.

---

## G02 — One Shared Domain Model

Both approaches use the same concepts:

- Customer
- Merchant
- Account
- Payment
- Transaction
- Payment status

Differences must remain inside the ledger implementation as much as possible.

---

## G03 — One Shared Payment Contract

The same payment request should work for both implementations.

Example:

```json
{
  "payment_id": "PAY-001",
  "payer_id": "C001",
  "merchant_id": "M001",
  "amount": 10000,
  "currency": "SEK",
  "idempotency_key": "REQ-001"
}
```

---

## G04 — Same Benchmark Workload

Performance comparisons must use identical workloads.

Example benchmark batches:

```text
10 payments
100 payments
500 payments
1000 payments
```

Exact benchmark sizes may be adjusted based on the chosen blockchain implementation, but the same workload must be applied to both systems.

---

## G05 — No Invented Results

No benchmark value may be written in the report before it is measured.

Latency, throughput, error rates, and resource observations must come from actual experiment runs.

---

## G06 — No Premature Blockchain Bias

Blockchain is an alternative implementation, not the assumed final solution.

The final conclusion must follow evidence.

---

## G07 — Payment Correctness Before Performance

A fast system that processes payments incorrectly is a failed system.

Correctness gates must pass before benchmarking begins.

---

## G08 — Keep UI Thin

The UI exists to make the demo understandable.

It must not become a separate frontend project.

The approved C06 frontend language is TypeScript. Use the smallest minimal web UI structure that satisfies the demo. React or another framework is not required by default and must not be introduced without C06 evidence and explicit human approval.

The TypeScript UI calls the existing FastAPI backend and remains a presentation/initiation layer. It must not own payment correctness, balance rules, merchant validation, idempotency, payment fingerprinting, persistence, ledger execution, rollback, or blockchain semantics.

---

## G09 — No Real Financial Integration

All users, balances, merchants, and transfers are simulated/test data.

No real financial credentials, bank integrations, or actual money are used.

---

## G10 — Stop Scope Creep

Any proposed feature must answer:

> Does this feature materially improve the research question or the interview demonstration?

If not, defer it.

---

# 7. Roadmap

## 7.1 Card Dependency Map

The dependency graph is:

```text
C01 → C02 → C03 → C04 → C05 → C06
                    └────→ C07

C03 + C04 + C07 → C08
C06 + C08 → C09
```

Definitions:

- C01 precedes all implementation.
- C02 depends on C01.
- C03 depends on C02.
- C04 depends on C03.
- C05 depends on C04.
- C06 depends on C05.
- C07 depends on C04 and must implement the same applicable safety semantics.
- C08 depends on C03, C04, and C07.
- C09 depends on C06 and C08.

The displayed Card order remains unchanged; the dependency graph makes the parallel relationship between C06 and C07 explicit.

## 7.2 Pre-Experiment Hypothesis

**Hypothesis — recorded before implementation and measurement:**

For a small local UPI-inspired payment network, the conventional PostgreSQL ledger is expected to have lower operational complexity and lower ledger-only latency, while the blockchain ledger may provide stronger immutability and audit-trace characteristics at the cost of additional execution and key-management complexity.

This is a pre-experiment hypothesis, not a conclusion. Results may confirm, partially confirm, or contradict it. Final conclusions must follow the recorded evidence.

## 7.3 Planned Repository Structure

This is documentation only; directories and files will be created by future Cards when needed.

```text
UPI-Inspired-Payment-Experiment/
├── src/upi_payment_experiment/
│   ├── domain/
│   ├── application/
│   ├── ledgers/
│   ├── api/
│   └── ui/
├── contracts/PaymentLedger.sol
├── tests/
│   ├── unit/
│   └── integration/
├── benchmarks/
├── evidence/
│   ├── c01/ ... c09/
│   └── benchmarks/
├── AGENTS.md
├── PROJECT_CONTROL.md
├── README.md
├── UPI_PAYMENT_INTERVIEW_ROADMAP.md
├── PAYMENT_CARD_EVIDENCE_MAP.md
├── ARCHITECTURE_AND_DECISIONS.md
├── BENCHMARK_AND_EXPERIMENT_PLAN.md
├── pyproject.toml
└── .gitignore
```

`benchmarks/` contains execution code; `evidence/benchmarks/` contains outputs. No `migrations/`, `infra/`, `scripts/`, `config/`, `.github/`, or other directories are planned at baseline.

## C01 — Project Baseline & Experimental Design

### Goal

Verify and operationalize the existing baseline before implementation.

Reconcile any inconsistencies, confirm that the scope and architecture are executable, and create only the implementation/repository artifacts that are still missing.

### Deliverables

Existing baseline artifacts to verify include:

- README
- roadmap and scope
- architecture decisions
- research question
- benchmark policy
- decision records

C01 execution deliverables/evidence may include:

- repository structure verification
- Python package baseline
- project configuration
- importability
- baseline tests
- environment/config validation
- canonical-document consistency validation
- evidence that implementation may safely begin

### Key Decision

The application will support two ledger implementations behind one interface.

### Exit Gate

C01 is complete only when:

- the existing baseline artifacts have been verified
- any baseline inconsistencies have been reconciled or documented
- scope and architecture are confirmed executable
- required implementation/repository artifacts that were still missing have been created
- project configuration and package importability are validated
- baseline tests and environment/config validation pass where applicable
- canonical-document consistency is validated
- no implementation-specific result is assumed
- evidence shows implementation may safely begin

---

## C02 — Domain Models

### Goal

Define the common payment domain.

### Suggested Models

```text
Customer
Merchant
Account
Payment
Transaction
PaymentStatus
LedgerResult
```

### Minimum Fields

#### Customer

```text
customer_id
name
payment_identity
```

#### Merchant

```text
merchant_id
name
payment_identity
```

#### Account

```text
account_id
owner_id
balance
currency
```

#### Payment

```text
payment_id
payer_id
merchant_id
amount
currency
idempotency_key
status
created_at
```

#### Transaction

```text
transaction_id
payment_id
ledger_type
status
timestamp
```

### Exit Gate

- validation exists
- negative amounts are rejected
- unsupported currencies are rejected
- domain tests pass
- models are ledger-independent

---

## C03 — Conventional Ledger

### Goal

Implement the first working payment system using a conventional transactional store.

### Primary Flow

```text
Customer: 1000 SEK
        ↓
Pay 100 SEK
        ↓
Customer: 900 SEK
Merchant: 100 SEK
        ↓
Transaction: SUCCESS
```

### Required Behaviors

- read payer balance
- validate sufficient funds
- debit customer
- credit merchant
- persist transaction
- return payment result
- preserve consistency on failure

### Important Engineering Requirement

The transfer must behave atomically.

The system must not allow this state:

```text
Customer debited
Merchant not credited
```

or the reverse.

### Exit Gate

- successful transfer works
- balances are correct
- failed payment leaves balances unchanged
- transaction history works
- tests pass

---

## C04 — Payment Safety & Failure Handling

### Goal

Make the conventional flow technically credible.

### Test Cases

- insufficient balance
- invalid payer
- invalid merchant
- zero amount
- negative amount
- duplicate payment
- repeated request with same idempotency key
- same idempotency_key reused with a different canonical payload → HTTP 409 Conflict
- failed persistence
- malformed request
- already-completed payment

### Idempotency Rule

`payment_id` is the logical/business payment identifier. `idempotency_key` is the client request duplicate-prevention identifier. They must remain distinct.

Repeating the same request must not charge the customer twice.

Example:

```text
Request #1
idempotency_key = ABC123
→ SUCCESS

Request #2
idempotency_key = ABC123
→ Return original result
→ No second debit

Same idempotency_key + different canonical payload
→ Reject with HTTP 409 Conflict
```

Canonical payload comparison may use a stable fingerprint or hash.

### Exit Gate

All safety tests pass.

---

## C05 — QR Payment Initiation

### Goal

Connect the payment system to a simple merchant QR flow.

### Canonical QR Payload

```text
upi-demo://pay?merchant_id=<single-non-empty-merchant-id>
```

Example:

```text
upi-demo://pay?merchant_id=M001
```

The C05 parser is strict: the scheme is exactly `upi-demo`, the authority/host is exactly `pay`, the path is empty, the query contains exactly one non-empty `merchant_id`, and there are no duplicate parameters, additional query parameters, or fragments. Malformed payloads, wrong schemes, wrong authorities/hosts, missing merchant IDs, duplicate merchant IDs, extra query parameters, and fragments are rejected. No additional merchant-ID regex is imposed by C05.

The QR contains merchant identity only. Amount, payer ID, payment ID, idempotency key, status, transaction ID, ledger choice, and persistence information remain outside the QR. The customer selects or enters the payment amount after decoding.

### Integration Boundary

QR parsing ends after returning `merchant_id`. The decoded value is passed into the existing payment request path:

```text
QR decode
→ merchant_id
→ FastAPI/application payment boundary
→ PaymentRequest.merchant_id
→ PaymentService
→ LedgerInterface
→ ConventionalLedger
```

An unknown merchant is rejected by the existing C04 account validation behavior. C05 does not implement a merchant database, account lookup, payment validation, or ledger behavior.

### Dependency

The planned minimal C05 dependency for real QR generation and internal/test decoding is `zxing-cpp`. It is not installed until C05 implementation is authorized.

### Important Boundary

QR is only the payment initiation mechanism.

The ledger remains responsible for the actual money movement.

C05 reuses the delivered C04 payment-safety path and does not reimplement payment IDs, idempotency keys, canonical fingerprints, replay or duplicate handling, conflicts, balance validation, persistence safety, transaction execution, rollback, or error semantics.

### Exit Gate

- merchant QR can be generated
- QR resolves to the correct merchant
- payment can be initiated from QR data
- invalid QR data is rejected

---

## C06 — Minimal Demo UI

### Goal

Make the experiment understandable during an interview.

### Suggested Screen

```text
-----------------------------------
UPI-Inspired Payment Prototype
-----------------------------------

Ledger:
(•) Conventional
( ) Blockchain

Customer:
John Demo

Balance:
1000 SEK

Merchant:
Demo Coffee Shop

[ Merchant QR ]

Amount:
[ 100 SEK ]

[ PAY ]

Status:
SUCCESS

Customer Balance:
900 SEK

Merchant Balance:
100 SEK

Latency:
XX ms

Transaction History:
...
-----------------------------------
```

### UI Rules

- no unnecessary animations
- no complex frontend state framework
- no full mobile application
- no design system work
- functional clarity over visual polish

The C06 frontend is a minimal TypeScript web UI. Framework selection, if any, is deferred to C06 preflight/implementation and must remain bounded to the demo.

### Contract-Locked C06 Scope

This planned scope is locked before C06 implementation; it does not authorize implementation or change C06 status.

- Plain TypeScript, HTML, and CSS compiled with `tsc`; React and Vite are not selected by default.
- FastAPI serves the compiled UI and static assets on the same origin as the API.
- The fixed presentation fixture is `C001` paying `M001` 100 SEK; fixture IDs are not a customer or merchant directory.
- The UI presents SEK with `.` as its sole decimal separator and deterministically transports integer öre to the existing payment boundary without binary floating-point multiplication.
- Opaque `payment_id` and `idempotency_key` values may be generated for a new request, but C04 remains responsible for canonical fingerprints, idempotency, conflicts, validation, execution, and rollback.
- C06 adds only the thin FastAPI balance, history, QR-delivery, static-serving, and local demo-bootstrap adapters required to demonstrate the delivered conventional path.
- Conventional is the only functional ledger. Blockchain is shown only as unavailable/disabled C07 work; no selector value is sent to the current payment API and no blockchain behavior is simulated.
- Any UI request-duration display is explicitly local/API-observed only. It is not C08 benchmark ledger latency.

`ARCHITECTURE_AND_DECISIONS.md` D10 owns the detailed C06 route, QR, bootstrap, and transport contracts. `PAYMENT_CARD_EVIDENCE_MAP.md` owns the planned acceptance, invariants, and evidence record.

### Exit Gate

C06 passes when:

- the UI shell is complete
- the conventional flow works end-to-end
- the UI is structurally ready to select multiple ledger implementations
- blockchain execution is not required until C07
- the locked C06 acceptance contract has passing executed evidence without changing C04/C05 semantics

C07 connects `BlockchainLedger` to the existing shared UI/application path. C09 packages the completed paths and does not add a major product feature.

---

## C07 — Blockchain Ledger

### Goal

Implement a second ledger capable of executing the same payment semantics.

### Critical Constraint

The rest of the application should change as little as possible.

Target design:

```text
PaymentService
      ↓
LedgerInterface
      ↓
BlockchainLedger
```

### Candidate Implementation Philosophy

Use the smallest blockchain environment that can provide a meaningful comparison.

The selection should favor:

- local reproducibility
- low setup complexity
- deterministic testing
- transparent transaction confirmation
- measurable execution behavior

The project must avoid turning into a blockchain-infrastructure project.

### Minimum Required Behaviors

- represent account ownership
- represent transfer
- record transaction
- return confirmation/failure
- prevent invalid balance transfer where applicable
- produce data usable for benchmark comparison

### Exit Gate

The C07 Exit Gate passes only when:

- the same logical payment scenario succeeds through `BlockchainLedger`
- applicable C04 safety semantics are proven for blockchain
- duplicate-payment protection works
- processed `payment_id` replay protection works
- controlled revert behavior is demonstrated
- balances are correct
- lost-response reconciliation is demonstrated
- no blind duplicate submission occurs after an ambiguous or lost response

Production wallet behavior and public-chain behavior remain out of scope.

---

## C08 — Benchmark & Comparative Experiment

### Goal

Produce evidence instead of opinions.

Detailed benchmark fairness, timing, reset, evidence, and reporting methodology is canonical in `BENCHMARK_AND_EXPERIMENT_PLAN.md`. This section is a roadmap-level summary and must not become an independent competing benchmark specification.

### Experimental Principle

Both ledger implementations receive:

- same Docker Compose environment where practical
- same host machine where practical
- same application version
- same `PaymentService`
- same domain models
- same deterministic dataset
- same payment amounts
- same workload sizes
- same benchmark code/script
- same number of repetitions
- same state reset rule

### Quantitative Metrics

Primary latency metrics:

- average ledger-only latency
- median ledger-only latency
- p95 ledger-only latency

Secondary API timing, reported separately:

- average API end-to-end latency
- median API end-to-end latency
- p95 API end-to-end latency

#### Throughput

Measure:

```text
payments / second
```

#### Error Rate

Measure:

```text
failed transactions / attempted transactions
```

#### Resource / Cost Observation

Keep cost evidence in three separate categories:

- measured local execution observations
- estimated real-world monetary/infrastructure cost
- qualitative operational cost

Detailed cost methodology remains canonical in `BENCHMARK_AND_EXPERIMENT_PLAN.md`. Never present estimates as measured values or combine these categories.

---

## Qualitative Comparison

The experiment should also evaluate:

### Complexity

Examples:

- lines/components added
- deployment requirements
- operational dependencies
- debugging difficulty

### Security Model

Discuss:

- trust assumptions
- central authority
- transaction integrity
- key management
- attack surface

### Auditability

Discuss:

- traceability
- immutability characteristics
- history inspection
- data correction / reversal implications

### Scalability

Discuss based on:

- measured behavior where available
- architecture characteristics
- clearly labelled inference where measurement is insufficient

---

## Example Final Comparison Table

Numbers below are placeholders until measured.

| Criterion | Conventional Ledger | Blockchain Ledger |
|---|---|---|
| Payment correctness | Measured | Measured |
| Average ledger-only latency | TBD | TBD |
| Median ledger-only latency | TBD | TBD |
| p95 ledger-only latency | TBD | TBD |
| Average API end-to-end latency | TBD | TBD |
| Median API end-to-end latency | TBD | TBD |
| p95 API end-to-end latency | TBD | TBD |
| Throughput | TBD | TBD |
| Success / failure counts | TBD | TBD |
| Final balance correctness | Tested | Tested |
| Duplicate protection | Tested | Tested |
| Auditability | Evaluated | Evaluated |
| Operational complexity | Evaluated | Evaluated |
| Security model | Evaluated | Evaluated |
| Measured local execution | TBD | TBD |
| Estimated monetary/infrastructure cost | TBD | TBD |
| Qualitative operational cost | Evaluated | Evaluated |
| Scalability | Measured / discussed | Measured / discussed |

---

## C09 — Interview Demo & Engineering Report

### Goal

Turn the engineering work into a clear technical story.

### Deliverables

- working demo
- architecture diagram
- short README
- experiment methodology
- benchmark results
- comparison table
- limitations
- future work
- clear explanation of why blockchain did or did not add value in this experiment

### Interview Story

The final explanation should follow this structure:

```text
1. I started from the payment problem, not from blockchain.

2. I implemented a small payment flow using a conventional ledger.

3. I added payment-safety controls such as idempotency and failure handling.

4. I exposed the same payment flow through a QR-based demo.

5. I implemented a second ledger using blockchain.

6. I ran the same workload against both approaches.

7. I compared speed, complexity, security assumptions,
   scalability, auditability, and cost.

8. I formed a conclusion based on the observed trade-offs,
   not on an assumption that blockchain must be better.
```

---

# 8. Premortem

Assume the project failed before the interview.

The following are the most likely reasons.

## Failure Mode 1 — Scope Explosion

### Scenario

The project expands into:

- real NFC
- wallets
- public blockchain
- advanced smart contracts
- authentication platform
- mobile apps
- cloud deployment
- fraud detection

### Impact

The core experiment is unfinished.

### Prevention

Every feature must pass the scope test:

> Is this required to execute or compare the core payment scenario?

If not, defer it.

---

## Failure Mode 2 — Blockchain Becomes the Project

### Scenario

Most time is spent configuring nodes, wallets, tooling, smart contracts, or chain infrastructure.

### Impact

The actual payment research question becomes secondary.

### Prevention

Choose the smallest blockchain setup that enables a meaningful ledger comparison.

Blockchain implementation time must remain bounded.

---

## Failure Mode 3 — The Payment System Is Only a Demo

### Scenario

The UI shows balances changing, but the backend cannot safely handle duplicate or failed requests.

### Impact

The project looks superficial to a technical interviewer.

### Prevention

C04 is mandatory before benchmarking.

---

## Failure Mode 4 — Invalid Comparison

### Scenario

The database version and blockchain version use different workflows, workloads, or data.

### Impact

Performance conclusions are not defensible.

### Prevention

One shared domain, one shared interface, one shared workload.

---

## Failure Mode 5 — Fake Precision

### Scenario

The report contains numbers based on expectation rather than measurement.

### Impact

Loss of technical credibility.

### Prevention

Every quantitative result must be traceable to a benchmark run.

---

## Failure Mode 6 — UI Consumes the Schedule

### Scenario

Too much time goes into frontend polish.

### Impact

Ledger comparison is incomplete.

### Prevention

UI remains intentionally minimal.

---

## Failure Mode 7 — Happy-Path Only

### Scenario

The demo works only when everything is correct.

### Impact

One unexpected input during the interview breaks the demonstration.

### Prevention

Test failure cases before presentation.

---

## Failure Mode 8 — No Clear Interview Narrative

### Scenario

The repository contains code but the design decisions are difficult to explain.

### Impact

The interviewer cannot easily see the reasoning ability behind the implementation.

### Prevention

Each Card records:

- what was built
- why it was built
- design decision
- alternative considered
- test evidence
- limitation
- lesson learned

---

# 9. Risk Register

| Risk | Probability | Impact | Control |
|---|---|---|---|
| Scope creep | High | High | Strict out-of-scope list |
| Blockchain setup complexity | Medium–High | High | Minimal local blockchain approach |
| Payment correctness bug | Medium | High | Mandatory safety tests |
| Duplicate payment | Medium | High | Idempotency key |
| Inconsistent balances | Medium | High | Atomic transaction handling |
| Weak benchmark methodology | Medium | High | Shared workload and repeatable tests |
| Unfair comparison | Medium | High | Shared interface and identical scenario |
| UI overengineering | Medium | Medium | Minimal UI guardrail |
| Demo instability | Medium | High | Automated tests + deterministic demo |
| Unmeasured claims | Medium | High | Evidence-only results |
| Interview time pressure | High | Medium | Prioritize C01–C08 before polish |

---

# 10. Card Priority

## Must Have

```text
C01 Project Baseline & Experimental Design
C02 Domain Models
C03 Conventional Ledger
C04 Payment Safety
C05 QR Payment
C06 Minimal UI
C07 Blockchain Ledger
C08 Benchmark & Comparison
```

## Final Packaging

```text
C09 Interview Demo & Engineering Report
```

If time becomes constrained, visual polish is reduced before any of the core experiment Cards are removed.

---

# 11. Definition of Success

The interview prototype is successful if all of the following are true:

1. A customer starts with `1000 SEK`.
2. A merchant can be identified through QR.
3. The customer can pay `100 SEK`.
4. The conventional ledger produces the correct final balances.
5. The blockchain ledger executes the same logical payment.
6. Duplicate or invalid payments are handled safely.
7. The transaction appears in history.
8. Both implementations are benchmarked using the same method.
9. Results are recorded without invented numbers.
10. The architecture and trade-offs can be explained clearly in an interview.

---

# 12. Final Project Boundary

The project is **not**:

> "Build a complete payment network."

The project **is**:

> "Build a small, controlled payment experiment that implements the same customer-to-merchant payment flow on a conventional ledger and a blockchain-based ledger, then compare the trade-offs using evidence."

That boundary should remain fixed unless the project brief or interview requirement changes.

---

# 13. Status Labels

For decisions made during implementation, use:

- **ADOPT** — clearly justified for the current prototype
- **EVALUATE** — useful candidate that needs evidence
- **WATCH** — potentially useful later, not needed now
- **AVOID** — introduces cost or complexity without enough value

Initial decisions:

| Item | Status | Reason |
|---|---|---|
| FastAPI backend | ADOPT | Small, clear API layer |
| Shared ledger abstraction | ADOPT | Required for fair comparison |
| Conventional transactional ledger | ADOPT | Baseline architecture |
| QR payment initiation | ADOPT | Directly relevant to the brief |
| Minimal UI | ADOPT | Improves interview demonstration |
| Blockchain ledger | EVALUATE | Core research alternative |
| Real NFC hardware | WATCH | Relevant, but not required for first experiment |
| Full mobile application | AVOID | High effort, low interview value |
| Real bank integration | AVOID | Out of scope and unnecessary |
| Complex smart-contract system | AVOID | High scope risk |
| Production cloud architecture | WATCH | Possible future extension |


---

# 14. Roadmap Decision Summary

This section records the roadmap-level baseline only. The canonical detailed architecture and technical-decision record is `ARCHITECTURE_AND_DECISIONS.md`; this summary must not become an independent competing source of truth.

These decisions are intentionally made **before implementation** so the project has a complete executable baseline. They are not permanent. A decision may change later if implementation evidence, benchmark results, or technical constraints justify the change.

**Change rule:** Do not change a decision only because another option looks more interesting. Record the reason, evidence, affected Cards, and expected benefit before changing the baseline.

## D01 — Conventional Database

**Decision:** Use **PostgreSQL**, preferably through Docker for local reproducibility.

**Why:**
- real transactional semantics
- stronger concurrency behavior than a simple file database
- appropriate for demonstrating atomic payment transfers
- widely used and easy to explain in an interview
- still small enough for the prototype

**Status:** ADOPT

**Fallback:** SQLite may be used only if PostgreSQL setup becomes a disproportionate blocker. If changed, the reason must be documented.

---

## D02 — Blockchain Environment

**Decision:** Use **Anvil**, the local Ethereum-compatible development node from the Foundry toolchain.

**Why:**
- runs locally
- no real money
- deterministic test accounts
- fast reset
- transaction receipts are available
- gas usage can be observed
- low infrastructure overhead
- suitable for repeatable interview experiments

**Important limitation:** Results from Anvil must not be presented as representative of Ethereum mainnet latency, congestion, or real production transaction cost.

**Status:** ADOPT for the interview experiment

---

## D03 — Smart Contract Design

**Decision:** Use one small custom `PaymentLedger` smart contract rather than an ERC-20 token or complex wallet system.

### Responsibilities

```text
mapping account → test balance
payment transfer
duplicate-payment protection
transaction event
payment result / revert
```

### Suggested operations

```text
seedBalance(...)
pay(...)
getBalance(...)
isProcessed(...)
```

### Payment identifier

Each logical payment receives a unique `payment_id`. The client request separately carries an `idempotency_key`; the contract records processed `payment_id` values so the same logical payment cannot be executed twice.

### Currency representation

The contract does **not** create a real SEK-backed token.

Balances represent **simulated SEK units** for the experiment.

Use integer minor units:

```text
1000 SEK = 100000 öre
100 SEK  = 10000 öre
```

Avoid floating-point money calculations.

**Status:** ADOPT

---

## D04 — Blockchain Integration from Python

**Decision:** The FastAPI backend talks to Anvil through **web3.py**.

The UI must not communicate directly with the blockchain.

```text
UI
 ↓
FastAPI
 ↓
PaymentService
 ↓
BlockchainLedger
 ↓
web3.py
 ↓
Anvil
 ↓
PaymentLedger contract
```

This keeps the application architecture comparable to the conventional implementation.

**Status:** ADOPT

---

## D05 — Definition of Payment Completion

A fair comparison requires an explicit completion point.

### Conventional Ledger

Operational completion boundary:

```text
database transaction COMMIT succeeds
```

### Blockchain Ledger

Operational completion boundary:

```text
transaction has been submitted
        ↓
included by Anvil
        ↓
successful transaction receipt is returned
```

### Timing Measurements

Record at least two blockchain timings where practical:

```text
submission latency
confirmation latency
```

For the primary ledger-only comparison, use the ledger operation start through the successful completion boundary. Full API end-to-end timing is secondary. See `BENCHMARK_AND_EXPERIMENT_PLAN.md` for the canonical timing definitions.

```text
ledger operation start → successful completion boundary
```

This definition must remain fixed during a benchmark run.

**Status:** ADOPT

---

## D06 — Benchmark Protocol

**Decision:** Use a deterministic benchmark protocol.

The detailed benchmark methodology is canonical in `BENCHMARK_AND_EXPERIMENT_PLAN.md`; this section is only a roadmap-level summary.

### Environment

- same Docker Compose environment where practical
- same host machine where practical
- same FastAPI application
- same PaymentService
- same test dataset
- same payment amounts
- same benchmark script
- same number of repetitions
- no unrelated heavy workload running intentionally during tests

### Initial Workloads

```text
10 payments
100 payments
500 payments
1000 payments
```

If the 1000-payment blockchain run becomes disproportionate in runtime or unstable, reduce the maximum workload for **both** implementations and document the reason.

### Repetitions

Run each workload **5 times** after a short warm-up.

### Warm-up

Run a small non-recorded warm-up before measured runs to reduce one-time startup effects.

### State Reset

Reset both ledger implementations to the same initial state before each measured run.

State reset and reset verification occur outside the measured benchmark interval.

### Initial Concurrency Policy

Primary benchmark is **sequential** to keep the first comparison controlled and understandable.

Concurrency is **OUT OF SCOPE** for the current benchmark. It may be added only through an explicitly approved future scope change.

### Quantitative Outputs

Record:

- total duration
- average ledger-only latency
- median ledger-only latency
- p95 ledger-only latency
- average API end-to-end latency, reported separately
- median API end-to-end latency, reported separately
- p95 API end-to-end latency, reported separately
- throughput
- success count
- failure count
- final balance correctness
- duplicate-payment correctness
- successful transaction gas usage where available
- failed/reverted transaction gas usage where available

**Status:** ADOPT

---

## D07 — Fixed Test Dataset

**Decision:** Use a deterministic synthetic dataset.

### Initial Dataset

```text
20 customers
5 merchants
```

### Initial Balance

Each customer:

```text
1000 SEK
```

represented internally as:

```text
100000 öre
```

Each merchant starts at:

```text
0 SEK
```

### Primary Demo Payment

```text
Customer C001
→ Merchant M001
→ 100 SEK
```

Expected result:

```text
Customer C001 = 900 SEK
Merchant M001 = 100 SEK
Transaction = SUCCESS
```

Dataset generation must be repeatable from a fixed seed or deterministic fixture.

**Status:** ADOPT

---

## D08 — QR Demonstration Method

**Decision:** Generate a real QR code, but do not require real mobile-camera integration for the interview version.

### QR Payload

Use the canonical C05 merchant URI above. Structured JSON is not an equivalent C05 payload.

Example:

```text
upi-demo://pay?merchant_id=M001
```

### Demo Behavior

Real QR generation plus simulated/internal QR scan decoding for the interview demo is **ADOPT**. The UI may simulate the scan step by decoding or loading the generated payload inside the demo application.

Real mobile camera integration remains **WATCH/deferred**.

### Boundary

QR only initiates the payment.

It does not perform ledger settlement.

**Status:** ADOPT

**Real camera / mobile integration:** WATCH / deferred

---

## D09 — Evidence and Benchmark Storage

**Decision:** Every measured result must be stored as machine-readable evidence.

Suggested structure:

```text
evidence/
  benchmarks/
    conventional/
    blockchain/
  test-results/
  demo/
```

### Benchmark Outputs

Store at least:

```text
benchmark_results.json
benchmark_results.csv
```

Each benchmark record should include:

```text
ledger_type
workload_size
run_number
timestamp
payment_id
ledger_latency_ms
api_end_to_end_latency_ms
submission_latency_ms
confirmation_latency_ms
status
successful_gas_used_if_applicable
failed_or_reverted_gas_used_if_applicable
```

These are raw per-transaction fields; fields that do not apply to an implementation may be omitted. Summary results should use the canonical primary ledger-only and separate secondary API end-to-end metrics, and remain reproducible from raw evidence where practical.

**Status:** ADOPT

---

## D10 — Interview Demo Runbook

**Decision:** Prepare a deterministic 2–3 minute demo path.

### Step 1 — Reset

Reset both ledger implementations to the same initial state.

```text
Customer C001 = 1000 SEK
Merchant M001 = 0 SEK
```

### Step 2 — Conventional Payment

```text
Select Conventional
→ show merchant QR
→ pay 100 SEK
→ show SUCCESS
→ show 900 / 100 balances
→ show transaction history
→ show measured latency
```

### Step 3 — Blockchain Payment

Reset state.

```text
Select Blockchain
→ use the same merchant
→ pay the same 100 SEK
→ show SUCCESS
→ show 900 / 100 balances
→ show transaction receipt
→ show measured latency
```

### Step 4 — Comparison

Show the measured benchmark summary:

```text
Conventional
vs
Blockchain
```

Explain:

- what was measured
- what was only qualitatively assessed
- limitations of the local blockchain experiment
- whether the evidence suggests meaningful blockchain value for this specific use case

**Status:** ADOPT

---

# 15. Baseline Technology Stack

The planned interview prototype baseline is:

```text
Python
FastAPI
Pydantic
PostgreSQL
SQLAlchemy or equivalent small persistence layer
pytest
Minimal TypeScript web UI
QR generation/decoding library: zxing-cpp for C05
Anvil
Solidity
web3.py
Docker Compose
```

Specific package choices may change if implementation evidence justifies it, but new technologies must not be added without a concrete project need.

---

# 16. Decision Status Summary

| Decision | Baseline | Status |
|---|---|---|
| Conventional database | PostgreSQL | ADOPT |
| Blockchain environment | Anvil | ADOPT |
| Blockchain value proposition | Blockchain ledger | EVALUATE |
| Blockchain contract | Minimal custom PaymentLedger | ADOPT |
| Python ↔ blockchain integration | web3.py | ADOPT |
| Conventional completion | Successful DB COMMIT | ADOPT |
| Blockchain completion | Successful transaction receipt | ADOPT |
| Benchmark protocol | Fixed, repeatable, 5 measured runs | ADOPT |
| Dataset | 20 customers / 5 merchants | ADOPT |
| Money representation | Integer öre | ADOPT |
| QR | Real QR, simulated scan acceptable | ADOPT |
| Evidence storage | JSON + CSV + raw measurements | ADOPT |
| Interview demo | Deterministic 2–3 minute runbook | ADOPT |
| Real NFC hardware | Deferred | WATCH |
| Real mobile camera scanning | Deferred | WATCH |
| Public blockchain | Not required for interview version | AVOID |
| Real banking integration | Out of scope | AVOID |

---

# 17. Change Control Rule

This baseline exists to prevent implementation drift.

A baseline decision may be changed later, but every change must record:

```text
Previous decision
New decision
Reason
Evidence
Cards affected
Risk introduced
Expected benefit
```

The roadmap is therefore **fixed enough to execute, but not frozen against evidence**.
