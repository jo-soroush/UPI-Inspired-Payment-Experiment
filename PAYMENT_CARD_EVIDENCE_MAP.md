# PAYMENT_CARD_EVIDENCE_MAP.md
## UPI-Inspired Payment Experiment — Card Evidence, Decision Rationale, and Learning Record

**Document purpose:**
This file is the evidence and learning record for every implementation Card in the UPI-inspired payment experiment.

It is intentionally separate from the roadmap.

The roadmap answers:

> What are we planning to build, in what order, and under which guardrails?

This file answers:

> Why was each Card necessary, why were specific technologies and designs selected, how was the work actually carried out, what evidence proves it, what went wrong, what alternatives existed, and what was learned?

---

# 1. Evidence Rules

## E01 — No invented completion

A Card may only be marked `COMPLETE` when implementation evidence exists.

Until then, fields describing actual implementation, test results, benchmark values, defects, and lessons must remain:

```text
NOT YET EXECUTED
```

Planned design and expected evidence may be documented before implementation, but must be clearly labeled as planned.

---

## E02 — Evidence before status

A Card cannot become `COMPLETE` based only on:

- code existing
- a demo appearing to work
- an assistant statement
- a developer statement
- an expected result

Completion requires recorded evidence.

---

## E03 — Every Card must explain the “why”

Each Card must document:

- why the Card exists
- why it is placed at this point in the roadmap
- why the chosen technology/design was selected
- what alternatives were considered
- what trade-offs were accepted
- what risk the Card reduces
- what future Cards depend on it

---

## E04 — Planned vs observed must stay separate

Every Card contains both:

```text
Planned approach
Actual implementation
```

These must never be mixed.

Recording convention:

- Sections labelled `Planned`, `Why`, `Goal`, `Decision`, `Planned approach`, or `Planned evidence` describe intended design only.
- Sections labelled `Actual`, `Tests`, `Results`, `Problems`, `Evidence artifacts`, or `Lessons learned` describe observed/executed work.
- Before implementation, every observed/executed field must remain `NOT YET EXECUTED`; planned design is not evidence of completion.

---

## E05 — Failures are evidence

Implementation failures, test failures, wrong assumptions, rejected designs, and remediation work are part of the engineering evidence and must be preserved.

---

## E06 — Reproducibility

Where practical, evidence should include:

- commands used
- test names
- benchmark configuration
- environment
- result artifacts
- commit SHA
- branch name
- files changed

---

# 2. Status Model

Each Card uses one of:

```text
NOT_STARTED
IN_PROGRESS
BLOCKED
READY_FOR_REVIEW
READY_FOR_DELIVERY
COMPLETE
```

Initial status:

```text
C01 NOT_STARTED
C02 NOT_STARTED
C03 NOT_STARTED
C04 NOT_STARTED
C05 NOT_STARTED
C06 NOT_STARTED
C07 NOT_STARTED
C08 NOT_STARTED
C09 NOT_STARTED
```

---

# 3. Standard Evidence Record for Every Card

Every Card must eventually contain these core completed fields:

```text
Card ID
Card title
Status
Goal
Why this Card exists
Why this design was chosen
Alternatives considered
Actual implementation
Files changed
Problems encountered
Root cause
Fix
Tests executed
Results
Evidence artifacts
Git branch
Commit SHA
Known limitations
Lessons learned
Exit Gate
```

The following are Card-specific optional fields and are required when materially relevant: `Why now`, `Dependencies`, why alternatives were rejected, benchmark artifacts, security considerations, data correctness considerations, performance considerations, trade-offs, what the Card enables next, pull request, and final reviewer notes.

---

# 4. C01 — Project Baseline & Experimental Design

## Status

`COMPLETE`

## Goal

Verify and operationalize the existing controlled project baseline before implementation begins. Reconcile any inconsistencies, confirm that scope and architecture are executable, and create only implementation or repository artifacts that are still missing.

## Why this Card exists

The project compares two ledger architectures. C01 validates the baseline already recorded in the repository and ensures it is executable because:

- scope may drift
- the two implementations may diverge
- benchmark criteria may change after results are known
- unsupported claims may appear
- the interview demo may become larger than necessary

C01 prevents those problems before implementation proceeds.

## Why this Card comes first

Architecture and experiment rules must exist before domain models, database logic, blockchain code, or benchmark code.

Otherwise later Cards would be built against assumptions that were never formally agreed.

## Planned architecture decision

```text
UI
 ↓
FastAPI
 ↓
PaymentService
 ↓
LedgerInterface
 ↙          ↘
ConventionalLedger   BlockchainLedger
```

## Why this architecture was selected

The comparison is about ledger approaches, not two completely different applications.

A shared `PaymentService` and `LedgerInterface` allows the payment logic to remain stable while the ledger implementation changes.

This reduces experimental bias and duplicate implementation work.

## Planned technology decisions

```text
Python
FastAPI
PostgreSQL
Anvil
Solidity
web3.py
pytest
Docker Compose
Minimal UI
```

## Why these technologies were selected

### Python

Chosen because:

- it supports rapid prototype development
- FastAPI and web3.py integrate naturally
- testing and benchmark automation are straightforward
- it keeps the experiment in one primary programming ecosystem

### FastAPI

Chosen because:

- lightweight API development
- clear request/response contracts
- easy test integration
- minimal framework overhead for the experiment

### PostgreSQL

Chosen because:

- transaction semantics are central to payment correctness
- atomic updates can be demonstrated clearly
- stronger concurrency semantics than a minimal file database
- commercially recognizable and interview-friendly

### Anvil

Chosen because:

- local Ethereum-compatible execution
- no real funds required
- deterministic local accounts
- fast reset
- receipt and gas data available
- low infrastructure overhead

Important limitation:

Anvil results do not represent Ethereum mainnet latency, congestion, or real-world transaction cost.

### Solidity

Chosen only for a minimal payment ledger contract.

No token ecosystem, wallet product, DeFi logic, or complex smart contracts are planned.

### web3.py

Chosen to keep blockchain interaction inside the Python backend.

### Docker Compose

Chosen as the canonical planned environment for repeatable PostgreSQL and local environment setup.

## Alternatives to document during implementation

Potential alternatives:

```text
SQLite
Hardhat local node
Ganache
public Ethereum testnet
different Python blockchain clients
full frontend framework
```

## Why alternatives are currently not preferred

### SQLite

Simpler, but less representative for transaction and concurrency behavior.

### Public testnet

Adds network variability, rate limits, external dependencies, test currency requirements, and reduced reproducibility.

### Complex frontend framework

Does not improve the research question enough to justify extra scope.

## Existing Baseline Artifacts

The following canonical artifacts already exist before C01:

```text
README
architecture decisions
scope / roadmap
research question
benchmark policy
decision records
```

## C01 Execution Evidence — PLANNED

C01 should verify or create only what is still missing:

```text
repository structure verification
Python package baseline
project configuration
importability
baseline tests
environment/config validation
mutual consistency of canonical documents
evidence that implementation may safely begin
```

## Risks reduced

- scope creep
- architecture drift
- invalid comparison
- retrospective benchmark design
- unnecessary blockchain complexity

## Actual implementation

Implemented the C01-only repository baseline:

- `pyproject.toml` with package metadata, setuptools configuration, and pytest configuration
- `src/upi_payment_experiment/__init__.py` as the minimal importable package
- `tests/test_c01_baseline.py` covering package importability, C01-only dependency configuration, and root-level canonical document placement

No domain models, payment logic, ledger logic, QR/UI functionality, blockchain functionality, or benchmark functionality was implemented.

## Problems encountered

The existing virtual environment had Python and pip but did not have pytest or setuptools installed.

The C01 test tooling was provisioned with pytest `8.4.2` and setuptools `84.0.0` in the existing `.venv`.

## Tests / validation

Executed validations:

```text
.venv/bin/python -m compileall -q src tests                PASS
.venv/bin/python importability check                       PASS
.venv/bin/python -m pytest                                 PASS — 3 collected, 3 passed
.venv/bin/python -m pip check                              PASS — no broken requirements
pyproject.toml TOML/configuration validation               PASS
repository structure validation                             PASS
secret-hygiene scan and .gitignore pattern checks           PASS
scope guard scan                                            PASS — no C02+ functionality symbols in C01 files
canonical-document consistency review                       PASS
```

## Evidence artifacts

Traceable evidence is recorded in this C01 section. No separate benchmark, runtime, database, blockchain, QR, UI, or production artifact was created.

## Exit Gate

C01 passes only when:

- architecture is documented and internally consistent
- scope is fixed enough to execute
- comparison criteria exist
- technology baseline is documented
- the repository/package baseline required for implementation exists
- project configuration is valid
- package/importability validation passes
- baseline tests/validation pass
- environment/config validation passes
- canonical documents are mutually consistent
- no benchmark result is invented
- blockchain limitations are explicitly stated
- evidence supports that implementation may safely begin

## C01 Phase 1 Self-Audit

`READY_FOR_INDEPENDENT_AUDIT` (Phase 1 state)

The C01-only baseline was independently audited with a passing result. Controlled delivery subsequently completed the C01 baseline and recorded the final Git metadata below.

## C01 Controlled Delivery Preparation

Independent C01 audit: `PASS`
C01 Exit Gate: `PASS`
Pre-delivery validation: `PASS`
Delivery status: `COMPLETE`
Delivery branch: `main` (the repository has no canonical branch requirement and no configured remote)
Pre-delivery base: `NONE` (the repository has no prior `HEAD`)
Initial C01 baseline commit: `f4fafcf77f43fe137a9b12398f1995f60dacea19`
C01 delivery evidence/state commit: `67dd21b7d1e8d94de230fc9cbb32bac1ca5f4b5c`
Post-delivery validation: `PASS`

Files included in the controlled C01 baseline:

```text
.gitignore
AGENTS.md
PROJECT_CONTROL.md
README.md
UPI_PAYMENT_INTERVIEW_ROADMAP.md
PAYMENT_CARD_EVIDENCE_MAP.md
ARCHITECTURE_AND_DECISIONS.md
BENCHMARK_AND_EXPERIMENT_PLAN.md
pyproject.toml
src/upi_payment_experiment/__init__.py
tests/test_c01_baseline.py
```

No ignored or runtime artifacts are included. No configured remote exists, so push, pull request, and merge delivery steps are not applicable to this initial baseline. Current repository `HEAD` is determined from Git and is not duplicated as a permanent evidence field because later documentation commits would change it.

## C01 Learning Record

### What did we build?

We built the minimal Python repository baseline: project configuration, an importable package, C01 baseline tests, and the validated root-level canonical document layout.

### Why did we build it this way?

The project needed a reproducible package and test baseline before later Cards implement domain, ledger, safety, UI, blockchain, or benchmark functionality. Keeping runtime dependencies empty preserves the approved scope.

### What did we initially misunderstand?

We initially expected the existing virtual environment to contain the C01 test and packaging tools. It had Python and pip, but pytest and setuptools were absent.

### What failed?

The initial test-tooling prerequisite was unavailable. No C01 test or implementation validation failed after the required tooling was provisioned.

### Why did it fail?

The pre-existing virtual environment was incomplete for running the new project configuration and baseline tests.

### How was it fixed?

pytest `8.4.2` and setuptools `84.0.0` were provisioned in the existing `.venv`, after which the validation suite passed.

### What other design could have been used?

A separate requirements file or system-level test tooling could have been used, but the optional test dependency in `pyproject.toml` keeps the C01 setup attached to the project configuration without adding runtime dependencies.

### What trade-off did we accept?

The baseline remains intentionally small and does not prove later runtime behavior. Later Cards must add and validate their own dependencies and functionality.

### What test proves the result?

Three C01 tests passed, covering package importability, C01-only dependency configuration, and root-level canonical document placement. Compile, pip, configuration, structure, secret-hygiene, and scope validations also passed.

### What would we do differently in a production payment system?

We would add controlled dependency locking, continuous integration, and production-specific operational and security review. Those concerns are outside this C01 experiment baseline.

### What did this Card teach us?

A small, evidence-backed package/configuration baseline can establish implementation readiness without prematurely implementing payment-system functionality.

## C01 Completion Checklist Result

All applicable C01 completion items passed: goal, rationale, architecture/design record, alternatives, actual implementation, files changed, problems and fixes, tests and recorded results, security review, known limitations, evidence artifacts, Git metadata, learning record, and Exit Gate.

The initial controlled C01 baseline commit is `f4fafcf77f43fe137a9b12398f1995f60dacea19` on `main`. The subsequent C01 delivery evidence/state commit is `67dd21b7d1e8d94de230fc9cbb32bac1ca5f4b5c`. No remote, pull request, or merge exists because the repository has no configured remote.

---

# 5. C02 — Domain Models

## Status

`IN_PROGRESS`

## Goal

Define one ledger-independent payment domain shared by both implementations.

## Why this Card exists

A fair comparison requires both ledgers to operate on the same business concepts.

Without common models, the conventional and blockchain implementations could accidentally implement different systems.

## Approved C02 Design Decision

The approved `PaymentStatus` vocabulary is exactly:

```text
PENDING
SUCCESS
FAILED
UNKNOWN
```

C02 defines this vocabulary only. Runtime transition behavior, retry and failure semantics, lost-response reconciliation, and safety enforcement remain later-Card concerns, primarily C04 and C07.

The implementation uses frozen standard-library dataclasses, a standard-library `Enum` for `PaymentStatus`, explicit `datetime` values, string identifiers, and integer minor-unit money. This keeps the domain ledger-independent without adding a dependency.

## Planned domain objects

```text
Customer
Merchant
Account
Payment
Transaction
PaymentStatus
LedgerResult
```

## Why these models were chosen

### Customer

Represents the payer.

### Merchant

Represents the payment recipient.

### Account

Represents a balance-bearing entity independently from identity.

### Payment

Represents the payment request and lifecycle.

### Transaction

Represents execution evidence produced by a ledger.

### PaymentStatus

Makes state transitions explicit.

### LedgerResult

Provides a shared result contract across ledger implementations.

## Money representation decision

Use integer minor units.

Example:

```text
1000 SEK = 100000 öre
100 SEK = 10000 öre
```

## Why floating-point money is avoided

Floating-point arithmetic can create rounding errors.

Payment values should use deterministic integer representation.

## Planned validations

- amount > 0
- supported currency only
- required payer
- required merchant
- unique payment identifier
- explicit payment status
- deterministic timestamps where test fixtures require them

## Alternatives considered

- merge Customer and Merchant into one generic Party
- keep balance directly on Customer/Merchant
- use decimal values instead of integer minor units

## Current decision

Prefer explicit models first because clarity matters more than premature abstraction in this small prototype.

## Actual implementation

Implemented the C02 ledger-independent domain module in `src/upi_payment_experiment/domain.py` with:

- `Customer`
- `Merchant`
- `Account`
- `Payment`
- `Transaction`
- `PaymentStatus`
- `LedgerResult`

The models validate required identifiers, supported `SEK`, integer minor-unit balances and amounts, positive payment amounts, explicit statuses, and explicit timestamps. `Transaction.transaction_id` is required; `LedgerResult.transaction_id` may be absent for an unresolved `UNKNOWN` result. No transition engine or runtime idempotency behavior was implemented.

Files created:

```text
src/upi_payment_experiment/domain.py
tests/test_c02_domain_models.py
```

Files modified for C02 state/evidence:

```text
PROJECT_CONTROL.md
README.md
PAYMENT_CARD_EVIDENCE_MAP.md
```

`pyproject.toml` was not modified; standard-library domain modeling was sufficient.

## Problems encountered

The first standalone import validation command omitted the configured `src` import path.

Root cause: the validation command did not apply the supported source-layout path.

Fix: reran the import validation with `src` explicitly on `sys.path`; the implementation and full test suite then passed.

## Tests

Executed validations:

```text
.venv/bin/python -m compileall -q src tests          PASS
domain import/status validation                      PASS
.venv/bin/python -m pytest                           PASS — 16 collected, 16 passed
.venv/bin/python -m pytest tests/test_c02_domain_models.py
                                                       PASS — 13 collected, 13 passed
.venv/bin/python -m pip check                        PASS — no broken requirements
project configuration validation                     PASS
secret-hygiene and .gitignore validation             PASS
ledger-independence review                           PASS
C03+/later-Card scope scan                           PASS
canonical-document consistency review               PASS
```

## Evidence artifacts

The C02 implementation and test files are the evidence artifacts. No persistence, API, QR, UI, blockchain, benchmark, or production artifacts were created.

At Phase 1 evidence capture, branch used: `main`. Git delivery was pending at that point; no `git add`, commit, push, PR, or merge had yet been performed.

## Exit Gate

- ledger-independent models exist
- invalid money values are rejected
- tests pass
- no database-specific or blockchain-specific concerns leak into core models

## C02 Phase 1 Self-Audit

`READY_FOR_INDEPENDENT_AUDIT`

At the end of Phase 1, the C02-only domain models and focused tests were implemented and validated. C02 was then `IN_PROGRESS`; independent audit and explicit delivery approval were still required before completion or Git delivery.

## C02 Learning Record — Phase 1

### What did we build?

We built seven frozen, ledger-independent domain models and focused tests for their canonical validations.

### Why did we build it this way?

Standard-library dataclasses and an enum provide the required domain clarity without coupling C02 to FastAPI, persistence, or either ledger implementation.

### What did we initially misunderstand?

The first standalone import check omitted the source-layout path, even though the project configuration supports `src` imports for tests.

### What failed?

That first validation command failed to import the package. No implementation or test assertion failed.

### Why did it fail?

The command did not add `src` to the import path.

### How was it fixed?

The check was rerun with the supported `src` path explicitly configured.

### What other design could have been used?

Pydantic models could be used later if an API boundary requires them, but the current C02 scope does not require that dependency.

### What trade-off did we accept?

The models intentionally do not provide persistence, transition orchestration, or runtime safety behavior; those concerns remain with later Cards.

### What test proves the result?

The C02-specific suite collected 13 tests and passed all 13, while the full suite collected 16 tests and passed all 16.

### What would we do differently in a production payment system?

We would separately specify and review lifecycle transitions, serialization contracts, persistence boundaries, and operational error handling.

### What did this Card teach us?

A small immutable domain layer can preserve payment semantics across future ledgers while keeping implementation-specific behavior outside the core models, including unresolved results that do not yet have an execution identity.

## C02 Independent Audit and Remediation Record

The independent C02 audit initially returned `FAIL`.

Root cause 1: this Evidence Map contained a duplicated mutable global status snapshot in its former global status section. The statement that the remaining Cards were unstarted became stale when C02 moved to `IN_PROGRESS`, even though `PROJECT_CONTROL.md` already owned live execution state.

Root cause 2: C02 validation coverage had been recorded at category level, but the tests did not directly exercise every required identifier and currency validation path. In particular, direct evidence was missing for empty `payment_id`, empty `merchant_id`, empty `idempotency_key`, Account identifiers, Transaction identifiers, and unsupported Payment currency.

Remediation:

- removed the duplicated mutable global status snapshot and replaced it with a durable evidence-oriented index that refers to `PROJECT_CONTROL.md` for live execution state;
- added the live project-state ownership rule to `AGENTS.md`;
- added direct C02 tests for the identified identifier, Payment currency, and status-validation paths;
- preserved `domain.py` unchanged because its C02 validations already covered the required behavior;
- kept C02 `IN_PROGRESS` and Git delivery pending.

The remediation validation results are recorded below after execution. This failure and remediation are retained as C02 engineering evidence rather than hidden.

## C02 Remediation Validation

```text
.venv/bin/python -m compileall -q src tests          PASS
package importability with configured src path       PASS
domain import/status validation                       PASS
.venv/bin/pytest                                     PASS — 19 collected, 19 passed
.venv/bin/pytest tests/test_c02_domain_models.py     PASS — 16 collected, 16 passed
.venv/bin/python -m pip check                        PASS — no broken requirements
project configuration validation                     PASS
ledger-independence review                           PASS
secret-hygiene and .gitignore validation             PASS
C03+/later-Card scope scan                           PASS
canonical-document consistency review               PASS
live-state ownership scan                            PASS
```

The direct-test additions cover empty required identifiers across the C02 models, unsupported Payment currency, explicit `PaymentStatus` validation across status-bearing models, boolean account balances, and explicit datetime validation. No implementation change was required.

## C02 Final Audit and Delivery

```text
Independent initial audit: FAIL
Remediation: COMPLETE
Independent re-audit: PASS
Exit Gate: PASS
Delivery status: COMPLETE
Delivery branch: main
C02 delivery commit: 20098e9c4782d38137fb047711314c2b738de373
Push result: PASS — origin/main contains the C02 delivery commit
```

The C02 completion checklist is satisfied:

- goal, design rationale, alternatives, and actual implementation recorded;
- files changed, initial audit failure, root causes, remediation, tests, results, and known limitations recorded;
- Git delivery metadata and lessons learned recorded;
- independent re-audit and Exit Gate passed;
- delivery was pushed and C02 is complete.

The C02 delivery commit above is the immutable Git reference for this Card. Current repository HEAD is determined from Git and is not duplicated as a permanent evidence field because later documentation commits would change it.

---

# 6. C03 — Conventional Ledger

## Status

`NOT_STARTED`

## Goal

Implement the baseline payment ledger using PostgreSQL.

## Why this Card exists

The conventional implementation is the experimental control/baseline.

The blockchain implementation has little meaning without a conventional system to compare against.

## Primary scenario

```text
Customer = 1000 SEK
Merchant = 0 SEK

Customer pays 100 SEK

Expected:

Customer = 900 SEK
Merchant = 100 SEK
Payment = SUCCESS
```

## Why PostgreSQL was selected

- ACID transactions
- atomic debit/credit behavior
- recognizable production-style relational baseline
- suitable for failure rollback testing
- appropriate for demonstrating concurrency and consistency concepts

## Critical correctness rule

The system must never allow a partial transfer.

Invalid state:

```text
Customer debited
Merchant not credited
```

or:

```text
Merchant credited
Customer not debited
```

## PLANNED DESIGN — implementation strategy

```text
READ COMMITTED transaction
lock relevant account rows with SELECT ... FOR UPDATE
lock rows in deterministic order
validate balance and idempotency/payment state
debit payer and credit merchant
persist payment and transaction in one DB transaction
COMMIT
```

On failure:

```text
ROLLBACK
```

## Alternatives considered

- SQLite
- in-memory dictionary
- append-only flat file
- event store

## Why they are not the baseline

The experiment should compare blockchain against a credible transactional ledger, not against an intentionally weak storage implementation.

## Actual implementation

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Tests

Must eventually include:

```text
successful transfer
balance correctness
rollback on failure
transaction persistence
history retrieval
```

## Evidence artifacts

`NOT YET EXECUTED`

## Exit Gate

The full conventional payment flow works correctly and is covered by tests.

---

# 7. C04 — Payment Safety & Failure Handling

## Status

`NOT_STARTED`

## Goal

Prove that the payment system behaves correctly outside the happy path.

## Why this Card exists

A payment demo that only works when all inputs are perfect is not meaningful engineering evidence.

This Card converts the baseline from a visual demo into a technically credible payment prototype.

## Required scenarios

```text
insufficient balance
invalid payer
invalid merchant
zero amount
negative amount
duplicate payment
replayed idempotency key
same idempotency_key + same canonical payload
→ return original result
→ no second debit
same idempotency_key + different canonical payload
→ HTTP 409 Conflict
malformed request
persistence failure
already completed payment
```

## PLANNED DESIGN — Idempotency decision

Each client payment request intent carries an `idempotency_key`. The logical payment itself is identified separately by `payment_id`.

```text
same idempotency_key + same canonical payload
→ return original result
→ no second debit

same idempotency_key + different canonical payload
→ reject with HTTP 409 Conflict
```

The rule applies to both ledger implementations. `payment_id` remains the logical/business payment identifier; `idempotency_key` remains the request duplicate-prevention identifier. Canonical payload comparison may use a stable fingerprint/hash.

## Why idempotency matters

Payment clients retry requests.

A network timeout must not cause a customer to be charged twice.

## Planned evidence

- unit tests
- integration tests
- before/after balances
- same idempotency_key + same canonical payload returns the original result with no second debit
- same idempotency_key + different canonical payload is rejected with HTTP 409 Conflict
- canonical payload fingerprint/hash comparison evidence
- duplicate-request result
- rollback behavior
- transaction state evidence

## Alternatives considered

- rely only on unique database constraints
- rely only on frontend button disabling
- accept duplicate requests for prototype simplicity

## Why those are insufficient

Payment correctness must be enforced at the backend/ledger level, not delegated to the UI.

## Actual implementation

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Test evidence

`NOT YET EXECUTED`

## Exit Gate

All required failure scenarios pass without balance corruption, including:

- same idempotency_key + same canonical payload returns the original result with no second debit
- same idempotency_key + different canonical payload is rejected with HTTP 409 Conflict
- `payment_id` remains distinct from `idempotency_key`

---

# 8. C05 — QR Payment Initiation

## Status

`NOT_STARTED`

## Goal

Connect a real QR payload to the payment workflow without turning QR into the ledger.

## Why this Card exists

The project brief includes QR-based merchant payments.

This Card demonstrates how payment initiation is separated from payment settlement.

## Planned QR payload

Example:

```text
upi-demo://pay?merchant_id=M001
```

## Why the payload stays small

The QR should identify the payment target.

The ledger remains responsible for:

- balance validation
- transfer
- transaction status
- audit trail

## Planned interview behavior

A QR is actually generated.

Camera integration is optional.

For the first interview version, scanning may be simulated by reading/decoding the QR inside the demo application.

## Why camera scanning is not mandatory

Real camera integration adds frontend/device complexity but contributes little to the ledger comparison.

## Alternatives considered

- full mobile QR scanner
- static text instead of QR
- amount embedded in QR
- signed QR payload

## Future extension candidates

- dynamic QR
- order reference
- signed merchant payload
- expiry
- camera scanning

## Actual implementation

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Tests

`NOT YET EXECUTED`

## Exit Gate

- QR generated
- QR resolves to correct merchant
- invalid payload rejected
- payment can be initiated from decoded QR data

---

# 9. C06 — Minimal Demo UI

## Status

`NOT_STARTED`

## Goal

Create a small interface that makes the experiment understandable during an interview.

## Why this Card exists

A backend-only experiment is harder to demonstrate interactively.

The UI should expose the system without becoming the system.

## Planned screen

```text
Ledger:
Conventional / Blockchain

Customer balance
Merchant identity
Merchant QR
Payment amount
PAY button
Payment status
Updated balances
Latency
Transaction history
```

## Why the UI is deliberately minimal

The project is about payment architecture and ledger comparison.

Time spent on frontend complexity reduces time available for:

- payment correctness
- blockchain integration
- benchmark quality
- evidence

## Planned technology

Simple HTML/CSS/JavaScript or small server-rendered UI.

## Why React is not the default

React is not technically wrong.

It is simply unnecessary unless implementation evidence shows that the simple UI cannot support the demo requirements.

## Actual implementation

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Test evidence

`NOT YET EXECUTED`

## Exit Gate

C06 passes when:

- the minimal UI shell is complete
- the conventional payment flow works end-to-end through the UI
- the UI structure supports multiple ledger implementations
- blockchain execution is not required until C07

C07 owns actual `BlockchainLedger` integration. C09 remains interview packaging and presentation only.

---

# 10. C07 — Blockchain Ledger

## Status

`NOT_STARTED`

## Goal

Implement the same logical payment flow using a local Ethereum-compatible ledger.

## Why this Card exists

This is the experimental alternative required to answer the project question:

> Does blockchain add meaningful value compared with a conventional payment ledger?

## Selected environment

`Anvil`

## Why Anvil was selected

- local
- deterministic
- inexpensive
- resettable
- Ethereum-compatible
- exposes transaction receipts
- exposes gas usage
- supports repeatable experimentation

## Important limitation

Anvil is a local development blockchain.

Results must not be generalized to:

- Ethereum mainnet latency
- public-chain congestion
- real gas prices
- public network finality
- geographically distributed validator behavior

## Smart contract decision

Create one minimal custom `PaymentLedger`.

## Why a custom minimal contract

The experiment needs ledger behavior, not a cryptocurrency product.

A custom minimal contract allows the project to control exactly what is being tested.

## Planned responsibilities

```text
test balances
payment execution
duplicate-payment protection
transaction event
balance lookup
```

## Explicitly excluded

```text
ERC-20 token product
wallet product
DeFi logic
staking
bridges
NFTs
public deployment
complex access-control system
```

## Python integration

Use `web3.py`.

## Why backend-controlled blockchain interaction

It keeps both implementations behind the same application boundary:

```text
UI
 ↓
FastAPI
 ↓
PaymentService
 ↓
LedgerInterface
 ↓
BlockchainLedger
```

## Key management model

For the interview prototype:

- Anvil-provided deterministic test accounts and test private keys only
- no production private keys
- no real-fund custody
- no production custody claim
- key-management limitations documented explicitly

## Actual implementation

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Tests

Must eventually cover:

```text
successful transfer
insufficient balance
duplicate payment
processed payment_id replay protection
receipt status
balance correctness
event/transaction trace
controlled revert behavior
lost-response reconciliation
no blind duplicate submission after ambiguous/lost response
```

## Evidence artifacts

`NOT YET EXECUTED`

## Exit Gate

C07 passes only when:

- the same logical payment scenario succeeds through `BlockchainLedger`
- applicable C04 safety semantics are proven for blockchain
- duplicate payment protection works
- processed `payment_id` replay protection works
- controlled revert behavior is demonstrated
- balances are correct
- lost-response reconciliation is demonstrated
- no blind duplicate submission occurs

Production wallet behavior and public-chain behavior are not required.

---

# 11. C08 — Benchmark & Comparative Experiment

## Status

`NOT_STARTED`

## Goal

Produce evidence that allows the two architectures to be compared without inventing conclusions.

## Why this Card exists

The project question cannot be answered by implementation alone.

A controlled comparison is required.

## Fair-comparison rule

Detailed benchmark fairness, timing, reset, evidence, and reporting methodology is canonical in `BENCHMARK_AND_EXPERIMENT_PLAN.md`. This Card record keeps only the concise guardrail summary below.

Both implementations must use:

- same application
- same PaymentService
- same application version
- same domain models
- same deterministic dataset
- same payment amounts
- same logical payment semantics
- same workload sizes
- same benchmark script/code
- same number of measured runs
- same Docker Compose environment where practical
- same host machine where practical
- same state reset rule

## Transaction completion definition

### Conventional

```text
ledger operation start
→ PostgreSQL transaction COMMIT succeeds
→ ledger execution successfully complete
```

### Blockchain

```text
ledger operation start
→ transaction submitted
→ Anvil includes transaction
→ successful receipt returned
→ ledger execution successfully complete
```

## Why completion semantics must be explicit

Database commit and blockchain confirmation are not naturally identical concepts.

Without a documented boundary, latency comparison would be ambiguous.

## Primary workload

Initial target:

```text
10 payments
100 payments
500 payments
1000 payments
```

If the highest workload becomes disproportionate in runtime or unstable, reduce the maximum workload for both implementations and record the reason.

## Repetitions

Initial baseline:

```text
5 measured runs per workload
```

after warm-up.

## State reset

Both systems return to the same deterministic initial state before each measured run. State reset and reset verification occur outside the measured benchmark interval.

## Concurrency scope

The current benchmark uses sequential payments. Concurrency is **OUT OF SCOPE** for the current benchmark unless explicitly approved through a future scope change.

## Quantitative metrics

Measure:

```text
ledger-only average latency
ledger-only median latency
ledger-only p95 latency
throughput
success count
failure count
correct final balances
duplicate-payment correctness
successful transaction gas where applicable
failed/reverted transaction gas where available
```

Full API end-to-end metrics are secondary and reported separately from the primary ledger-only statistics.

Primary statistics are the ledger-only average, median, and p95 latency. Secondary statistics are the average, median, and p95 API end-to-end latency, reported separately. These definitions and timing boundaries are governed by `BENCHMARK_AND_EXPERIMENT_PLAN.md`.

## Qualitative dimensions

Analyze separately:

```text
architecture complexity
operational dependencies
trust assumptions
key management
attack surface
auditability
reversal/correction behavior
privacy implications
maintenance burden
scalability characteristics
```

## Why qualitative and quantitative results are separated

Some properties can be measured directly.

Others require architectural analysis and should not be disguised as numeric scores.

## Evidence storage

Machine-readable benchmark evidence:

```text
evidence/
  benchmarks/
    conventional/
    blockchain/
```

Required outputs:

```text
benchmark_results.json
benchmark_results.csv
raw per-transaction measurements where practical
```

## Prohibited behavior

Do not:

- invent benchmark values
- extrapolate Anvil results to Ethereum mainnet
- hide failed runs
- compare different workloads
- change methodology after seeing favorable results without documenting the change

## Actual benchmark results

`NOT YET EXECUTED`

## Problems encountered

`NOT YET EXECUTED`

## Lessons learned

`NOT YET EXECUTED`

## Exit Gate

A reproducible evidence set exists for both ledgers, and all conclusions are traceable to either measured evidence or explicitly labeled qualitative analysis.

---

# 12. C09 — Interview Demo & Engineering Report

## Status

`NOT_STARTED`

## Goal

Convert the technical work into a short, defensible interview demonstration.

## Why this Card exists

Engineering work has limited interview value if the candidate cannot explain:

- what problem was addressed
- why the architecture was chosen
- what was measured
- what failed
- what was learned
- what the limitations are

## Planned demo runbook

### Step 1 — Reset

```text
Customer C001 = 1000 SEK
Merchant M001 = 0 SEK
```

### Step 2 — Conventional

```text
select Conventional
show merchant QR
pay 100 SEK
show SUCCESS
show balances
show history
show latency
```

### Step 3 — Blockchain

Reset.

```text
select Blockchain
same merchant
same 100 SEK payment
show SUCCESS
show balances
show receipt
show latency
```

### Step 4 — Comparison

Show benchmark evidence and explain trade-offs.

## Target duration

Approximately:

```text
2–3 minutes
```

for the main live demo.

Technical discussion may continue after the demo.

## Interview narrative

The intended explanation is:

```text
I started from the payment problem rather than assuming blockchain was the answer.

I built one shared payment flow.

I first implemented a conventional transactional ledger.

I added payment correctness controls.

I exposed the flow through QR.

I then implemented a blockchain ledger behind the same interface.

I ran the same controlled workload against both.

I separated measured results from qualitative architectural analysis.

I formed conclusions from the evidence and documented the limitations.
```

## What the final report must include

- problem statement
- scope
- architecture
- technology decisions
- alternatives considered
- payment correctness evidence
- benchmark methodology
- raw result references
- result summary
- limitations
- interpretation
- future work

## Actual implementation

`NOT YET EXECUTED`

## Demo evidence

`NOT YET EXECUTED`

## Final lessons

`NOT YET EXECUTED`

## Exit Gate

The project can be demonstrated and explained without relying on undocumented assumptions.

---

# 13. Cross-Card Decision Register

This register is a concise evidence-map summary. Canonical architecture and technical decisions remain in `ARCHITECTURE_AND_DECISIONS.md`; this register must not override or become a competing source of truth.

The following decisions currently form the planned baseline.

| Decision | Current choice | Status | Main reason |
|---|---|---|---|
| Backend | FastAPI | ADOPT | Lightweight shared API layer |
| Conventional ledger | PostgreSQL | ADOPT | Transactional correctness baseline |
| Blockchain environment | Anvil | ADOPT | Local, deterministic, repeatable |
| Contract language | Solidity | ADOPT | Native EVM contract implementation |
| Blockchain integration | web3.py | ADOPT | Keeps integration in Python backend |
| Money representation | Integer öre | ADOPT | Avoid floating-point money errors |
| QR | Real generated QR | ADOPT | Directly relevant to project brief |
| Interview scan behavior | Simulated/internal QR decoding | ADOPT | Real QR generation with no camera dependency |
| Real mobile camera integration | Deferred | WATCH | Device integration is outside the current interview scope |
| UI | Minimal web UI | ADOPT | Demo clarity without frontend scope |
| Public blockchain | Not in interview version | AVOID | Unnecessary variability and scope |
| Real NFC | Deferred | WATCH | Relevant but not required initially |
| Real bank integration | Excluded | AVOID | Outside experiment scope |

---

# 14. Evidence Folder Convention

Planned repository structure:

```text
AGENTS.md
PROJECT_CONTROL.md
README.md
UPI_PAYMENT_INTERVIEW_ROADMAP.md
PAYMENT_CARD_EVIDENCE_MAP.md
ARCHITECTURE_AND_DECISIONS.md
BENCHMARK_AND_EXPERIMENT_PLAN.md
.gitignore

evidence/
  c01/
  c02/
  c03/
  c04/
  c05/
  c06/
  c07/
  c08/
  c09/

evidence/benchmarks/
  conventional/
  blockchain/
```

Each Card folder may contain:

```text
test_output.txt
benchmark_output.json
benchmark_output.csv
screenshots/
notes.md
```

Only real outputs should be placed in evidence folders.

---

# 15. Per-Card Completion Checklist

Before any Card becomes `COMPLETE`, verify:

```text
[ ] Goal achieved
[ ] Why documented
[ ] Architecture/design decision documented
[ ] Alternatives documented
[ ] Actual implementation described
[ ] Files changed recorded
[ ] Problems recorded
[ ] Root causes recorded
[ ] Fixes recorded
[ ] Tests recorded
[ ] Test outputs preserved
[ ] Security implications reviewed when applicable
[ ] Data correctness reviewed when applicable
[ ] Known limitations documented
[ ] Evidence artifacts linked
[ ] Git metadata recorded
[ ] Lessons learned written
[ ] Exit Gate explicitly PASS
```

---

# 16. Learning Record Rule

Every completed Card must end with a short learning record answering:

### What did we build?

### Why did we build it this way?

### What did we initially misunderstand?

### What failed?

### Why did it fail?

### How was it fixed?

### What other design could have been used?

### What trade-off did we accept?

### What test proves the result?

### What would we do differently in a production payment system?

### What did this Card teach us?

This section is mandatory because the project is intended not only as a demo, but as evidence of engineering reasoning during the interview.

---

# 17. Evidence Record Index

Evidence recorded:

- C01 delivery evidence is recorded in the C01 section above.
- C02 Phase 1 implementation and remediation evidence is recorded in the C02 section above.
- Benchmark evidence: `NONE YET`.

Planned evidence requirements remain defined in advance. Live execution state is owned by `PROJECT_CONTROL.md`; this Evidence Map intentionally does not duplicate mutable global fields such as Active Card, authorization, blocker, or Next Allowed Card.
