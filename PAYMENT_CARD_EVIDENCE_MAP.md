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

## Verification Harness Record — C03 onward

For C03 onward, each Card must add a compact verification record with:

```text
Canonical sources
Derived Acceptance Contract
Critical Invariants
Verification Strategy
Requirement / Invariant → Implementation → Test / Evidence → Result traceability
Property / Invariant Testing applicability and result
Mutation Testing applicability and result
Independent Spec-Based Audit result
```

This record is evidence structure, not a new specification. Reference the applicable canonical clauses rather than copying them in full. Before implementation, only planned fields may be populated; implementation, test, result, and audit fields must remain `NOT YET EXECUTED`.

Deterministic invariant tests are required where meaningful. Generated property testing and mutation testing are conditional. Any `NOT_APPLICABLE` entry must state a short reason. Live execution state remains owned exclusively by `PROJECT_CONTROL.md` and must not be duplicated here.

A compact traceability table should use this form:

| ID | Canonical requirement or invariant reference | Implementation evidence | Test or verification evidence | Result |
|---|---|---|---|---|
| `<Card>-Vnn` | Reference only | Planned or actual location | Planned or executed evidence | `NOT YET EXECUTED` or observed result |

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

`COMPLETE`

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

`PASS — READY_FOR_INDEPENDENT_AUDIT`

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

`COMPLETE`

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
validate balance and C03-owned transaction state
debit payer and credit merchant
persist payment and transaction in one DB transaction
COMMIT
```

On failure:

```text
ROLLBACK
```

## Verification Harness — PLANNED

### Canonical sources

- `UPI_PAYMENT_INTERVIEW_ROADMAP.md` — C03 goal, required behaviors, atomicity requirement, and Exit Gate
- `ARCHITECTURE_AND_DECISIONS.md` — D03–D05, Payment Safety, and Atomicity and Failure Strategy
- `AGENTS.md` — payment correctness, architecture guardrail, Card workflow, and Verification Harness
- this C03 evidence record — planned design and evidence only

### Derived Acceptance Contract — PLANNED

The C03 Acceptance Contract is derived from the sources above. It covers the successful atomic transfer, correct final balances, payment and transaction persistence, transaction/history retrieval, and one controlled rollback proof. It does not replace or expand the canonical C03 Exit Gate.

### Critical Invariants — PLANNED

- a successful transfer applies the exact debit and credit in integer minor units;
- the payer and merchant balance delta is conserved for the no-fee transfer;
- payment and transaction records commit with the balance changes;
- a controlled failure cannot leave a partial transfer or committed payment/transaction residue;
- shared payment logic remains isolated from PostgreSQL-specific details behind the approved application and ledger boundaries.

### Approved C03/C04 boundary

C03 owns:

```text
successful atomic transfer
correct balances
payment and transaction persistence
transaction and history retrieval
one controlled rollback proof
```

C04 owns:

```text
idempotency
duplicate payment handling
comprehensive invalid-input handling
already-completed behavior
API conflict behavior
comprehensive persistence-failure matrix
```

### Verification Strategy — PLANNED

- applicable unit tests: planned where compact ledger-independent or mapping logic exists;
- PostgreSQL integration tests: planned for commit, persistence, history, and controlled rollback behavior;
- deterministic invariant tests: required for exact balance deltas, value conservation, and unchanged state after the controlled failure;
- generated property testing: `NOT_APPLICABLE` initially because deterministic pytest cases are sufficient for the bounded C03 invariants;
- mutation testing: conditional and not a C03 Exit Gate; no C03 run is planned unless compact high-risk pure logic provides concrete value. The first likely pilot remains C04.

### Planned traceability

| ID | Canonical requirement or invariant reference | Planned implementation evidence | Planned test or verification evidence | Result |
|---|---|---|---|---|
| C03-V01 | Roadmap C03 successful transfer and correct balances | C03 payment/ledger implementation | PostgreSQL integration plus deterministic balance-delta checks | `NOT YET EXECUTED` |
| C03-V02 | Roadmap C03 persistence and history behavior | C03 payment/transaction persistence and retrieval paths | PostgreSQL persistence and history integration checks | `NOT YET EXECUTED` |
| C03-V03 | Roadmap C03 consistency on failure; Architecture section 11 | C03 transaction boundary and controlled failure hook | Controlled rollback integration check with before/after state | `NOT YET EXECUTED` |
| C03-V04 | Architecture D04–D05 and `AGENTS.md` architecture guardrail | Shared service/interface and PostgreSQL adapter boundaries | Architecture/import review plus applicable tests | `NOT YET EXECUTED` |

### Executed traceability — Phase 1

| ID | Requirement or invariant | Implementation evidence | Executed test or verification evidence | Observed result |
|---|---|---|---|---|
| C03-V01 | Successful atomic transfer; exact payer and merchant deltas; value conservation | `payment_service.py`; `ledger.py`; `conventional_ledger.py` transaction implementation | `test_successful_atomic_transfer_persists_and_is_retrievable` against PostgreSQL 16 | `PASS` — `100000/0` became `90000/10000`; deltas were `-10000/+10000`; total value remained `100000` |
| C03-V02 | One successful Payment and one linked Transaction; history retrieval | `postgres_schema.sql`; `ConventionalLedger.get_payment`, `get_transaction`, and `list_transactions` | Successful-flow integration assertions plus fresh PostgreSQL reads | `PASS` — one `SUCCESS` Payment and one linked `SUCCESS` Transaction were retrieved |
| C03-V03 | Failure inside the transaction leaves no partial balance or persistence residue | `ConventionalLedger.execute_payment`, explicit rollback, and `_after_payer_debit` test seam | `test_controlled_failure_rolls_back_all_state` using a fresh ledger connection after injected failure | `PASS` — balances remained `100000/0`; Payment and Transaction counts were both zero |
| C03-V04 | PostgreSQL stays behind `LedgerInterface`; shared service and domain remain technology-neutral | `ledger.py`; `payment_service.py`; `conventional_ledger.py` | `test_postgresql_details_are_confined_to_the_adapter`; protected-file diff review | `PASS` — PostgreSQL/Psycopg references are confined to the adapter and integration test infrastructure |

### Property / Invariant Testing result

Deterministic invariant testing: `PASS`. The PostgreSQL integration test checks exact debit and credit deltas, no-fee value conservation, persisted-record agreement, and unchanged state after controlled rollback.

Generated property testing: `NOT_APPLICABLE` for C03 Phase 1. The bounded invariants are covered directly with deterministic pytest assertions; no generated-test dependency was added.

### Mutation Testing result

`NOT_APPLICABLE` for C03 Phase 1. Mutation testing is conditional, is not a C03 Exit Gate, and remains deferred to the likely C04 pilot because C03's principal risk is PostgreSQL transaction behavior rather than compact pure branching logic.

### Independent Spec-Based Audit result

`PASS` — independent spec-based audit found no major findings, minor findings, or blockers.

## Alternatives considered

- SQLite
- in-memory dictionary
- append-only flat file
- event store

## Why they are not the baseline

The experiment should compare blockchain against a credible transactional ledger, not against an intentionally weak storage implementation.

## Actual implementation

Implemented the shared `PaymentService → LedgerInterface → ConventionalLedger → PostgreSQL` path with:

- a technology-neutral structural ledger interface;
- a shared payment service that delegates without importing PostgreSQL details;
- direct Psycopg 3 parameterized SQL with explicit `READ COMMITTED` isolation;
- deterministic `SELECT ... FOR UPDATE` account locking;
- atomic debit, credit, Payment persistence, and Transaction persistence;
- explicit commit on success and rollback on exception;
- Payment, Transaction, balance, and history retrieval mapped to C02 domain models;
- a narrow protected failure seam used only for the controlled rollback proof;
- an isolated PostgreSQL 16 Docker Compose service using a named volume and synthetic test data.

Files created:

```text
compose.yaml
src/upi_payment_experiment/ledger.py
src/upi_payment_experiment/payment_service.py
src/upi_payment_experiment/conventional_ledger.py
src/upi_payment_experiment/postgres_schema.sql
tests/test_c03_conventional_ledger.py
```

Files modified during C03 Phase 1:

```text
PROJECT_CONTROL.md
PAYMENT_CARD_EVIDENCE_MAP.md
pyproject.toml
tests/test_c01_baseline.py
```

The C01 configuration assertion was updated only because the legitimate C03 runtime dependency means an empty runtime-dependency list is no longer a valid permanent baseline assertion. C02 domain implementation and tests were not changed.

## Problems encountered

The first full test run collected 22 tests. The 19 existing C01/C02 tests passed, while all three C03 tests stopped during fixture setup.

Root cause: the fixture called `executemany()` on a Psycopg 3 `Connection`; that API belongs to `Cursor`.

Fix: execute the fixture's parameterized seed batch through a cursor. The full suite was then rerun and all 22 tests passed. No production implementation defect or false successful result was hidden.

## Tests

Executed against the Compose-managed PostgreSQL 16 service:

```text
.venv/bin/python -m pytest -vv
PASS — 22 collected, 22 passed

.venv/bin/python -m pytest tests/test_c01_baseline.py -q
PASS — 3 passed

.venv/bin/python -m pytest tests/test_c02_domain_models.py -q
PASS — 16 passed

.venv/bin/python -m pytest tests/test_c03_conventional_ledger.py -q
PASS — 3 passed

.venv/bin/pip check
PASS — no broken requirements

docker compose ps
PASS — PostgreSQL service healthy

PostgreSQL default transaction isolation check
PASS — read committed

git diff --check
PASS

protected architecture/domain/test file diff review
PASS — no changes

C04 leakage scan
PASS — idempotency key is persisted as opaque data only

secret-pattern scan
PASS — no findings
```

## Evidence artifacts

The source, schema, Compose definition, and C03 integration tests listed above are the Phase 1 evidence artifacts. Tests used synthetic data only. No benchmark result was produced.

Phase 1 branch: `main`.

Git delivery: complete. Implementation delivery commit: `e626bc10eab7a33c5a03042e41a706d989168548`; push result: PASS — `origin/main` contains the commit. The completion-evidence documentation commit is intentionally not duplicated as a self-referential SHA.

Known limitations retained for later Cards:

- idempotency, duplicate/replay handling, API conflicts, already-completed behavior, and the comprehensive failure matrix remain C04-owned;
- C03 proves one controlled rollback point, not every persistence failure location;
- concurrency correctness is implemented through row locks and deterministic ordering, but broad contention/stress evidence is outside the C03 acceptance contract;
- local Docker PostgreSQL results are not production performance or durability claims.

## Exit Gate

The full conventional payment flow works correctly and is covered by tests.

Phase 1 self-assessment: `PASS`.

The independent spec-based audit and Exit Gate subsequently passed, human delivery approval was granted, and controlled delivery completed. The immutable implementation delivery SHA is recorded in the C03 Final Audit and Delivery Record below.

## C03 Phase 1 Self-Audit

`PASS — READY_FOR_DELIVERY`

- canonical Acceptance Contract: implemented and traced;
- critical invariants: deterministic checks passed;
- C03/C04 boundary: preserved;
- architecture: unchanged and PostgreSQL isolated behind the ledger boundary;
- C02 domain semantics: unchanged;
- dependencies: only `psycopg[binary]>=3,<4` added;
- SQL: parameterized for runtime data;
- rollback and connection cleanup: exercised against PostgreSQL;
- false-green review: assertions use exact state, record counts, identities, statuses, and fresh connections;
- independent audit: `PASS` — no findings.

## C03 Phase 1 Learning Record

### What did we build?

We built the conventional-ledger path `PaymentService → LedgerInterface → ConventionalLedger → PostgreSQL`. It executes the C03 atomic payment flow, persists the successful Payment and linked Transaction, retrieves committed payment and transaction history, and provides one controlled rollback proof after a simulated failure inside the database transaction.

### Why did we build it this way?

PostgreSQL provides the conventional transactional control baseline required for the later blockchain comparison. Its ACID transaction semantics support atomic debit and credit, rollback on failure, and explicit concurrency control through row locking. This makes it a credible relational baseline rather than an intentionally weak comparison target. Direct Psycopg was sufficient for this bounded prototype because it kept the persistence layer small while exposing the PostgreSQL transaction and locking behavior that C03 needed to prove.

### What did we initially misunderstand?

The integration-test fixture initially attempted to call `executemany()` on a Psycopg 3 `Connection` rather than executing the seed batch through a `Cursor`. This was a test-setup API mistake, not a production ledger implementation defect.

### What failed?

The initial full run collected 22 tests. The 19 existing C01 and C02 tests passed, while all three C03 tests stopped during fixture setup. No successful C03 result was claimed from that failed run.

### Why did it fail?

In the fixture setup path, Psycopg 3 provides the required `executemany()` operation through `Cursor`, not through `Connection` as the fixture attempted to use it.

### How was it fixed?

The parameterized fixture seed batch was executed through a cursor. The complete suite was then rerun and all 22 tests passed.

### What other design could have been used?

The persistence layer could have used SQLAlchemy or another persistence abstraction. SQLite or in-memory storage could also have produced a smaller local implementation. They were not selected for C03 because direct Psycopg kept the adapter minimal while preserving real PostgreSQL transaction, rollback, and locking semantics for the conventional baseline.

### What trade-off did we accept?

Direct Psycopg keeps the implementation small and makes PostgreSQL transaction behavior explicit, but it provides less ORM abstraction and portability than a higher-level persistence layer. C03 also intentionally accepts a bounded scope: it proves the successful flow and one rollback point but does not implement the C04 safety, idempotency, replay, conflict, or comprehensive failure matrix.

### What test proves the result?

The PostgreSQL integration tests prove that the successful transfer changes balances from `100000/0` to `90000/10000`, persists exactly one `SUCCESS` Payment and one linked `SUCCESS` Transaction, and returns the committed transaction through history retrieval. The controlled failure test proves that a failure after payer debit rolls balances back to `100000/0` and leaves zero new Payment or Transaction records. Final results were: full suite 22 passed; C01 3 passed; C02 16 passed; C03 3 passed.

### What would we do differently in a production payment system?

A production system would additionally require migration and schema-version management, stronger credential and secret handling, operational monitoring, broader concurrency and load validation, a comprehensive persistence-failure matrix, and production-grade idempotency and reconciliation. Those concerns are outside C03 and are not claimed as implemented.

### What did this Card teach us?

Transaction correctness must be demonstrated against the real database, and atomicity must include balances and persistence in one transaction. Integration setup failures must be corrected before evidence is accepted, and the complete suite must then be rerun so failed setup is not confused with successful implementation behavior. C03 now provides the conventional control baseline for the later ledger comparison.

## C03 Final Audit and Delivery Record

```text
Independent spec-based audit: PASS
Major findings: NONE
Minor findings: NONE
Blockers: NONE
Exit Gate: PASS
Human delivery approval: GRANTED
Delivery status: COMPLETE
Implementation delivery commit: e626bc10eab7a33c5a03042e41a706d989168548
Push result: PASS — `origin/main` contains the implementation delivery commit
Completion evidence: this documentation-only record; its SHA is intentionally not duplicated
```

---

# 7. C04 — Payment Safety & Failure Handling

## Status

`COMPLETE`

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

The rule applies to both ledger implementations within their execution context. `payment_id` remains the logical/business payment identifier; `idempotency_key` remains the request duplicate-prevention identifier. Canonical payload comparison uses a deterministic stable fingerprint over exactly `payment_id`, `payer_id`, `merchant_id`, `amount`, and `currency`. The `idempotency_key`, timestamps, status, database identifiers, transaction identifiers, and HTTP metadata are excluded. For delivered C04, ConventionalLedger was the only execution namespace, so “globally unique” meant globally unique within that conventional context and PostgreSQL provides its concurrency-safe coordination. The planned C07 ledger-scoped namespace decision does not alter C04 runtime behavior.

An existing completed `payment_id` with the same canonical payload returns the original logical result without another execution. Reusing that payment ID with a different canonical payload is a conflict. The minimal FastAPI boundary maps both identifier conflicts to HTTP 409 without placing HTTP semantics in the ledger adapter.

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
- concurrent same-key integration evidence proving one committed execution
- malformed-request API validation and conflict mapping evidence

## C04 Verification Harness — PLANNED

Canonical sources: the C04 roadmap clauses and Exit Gate, Architecture decisions A01/A02/D04/D05 and sections 5, 9, and 11, plus the explicitly approved C04 design decisions recorded above.

Acceptance Contract: preserve the C03 successful flow; reject invalid payer, invalid merchant, insufficient balance, zero/negative amount, and malformed API requests without balance corruption or successful persistence; return the original result for same-payload replays; reject different-payload identifier reuse; and roll controlled persistence failure back completely.

Critical invariants: rejected requests do not change balances; a replay cannot cause a second debit or credit; conflicts do not execute the ledger; one logical successful payment has one committed Transaction; balances and persisted SUCCESS state agree; rollback leaves no partial Payment, Transaction, balance, or terminal idempotency state; concurrent same-key requests cannot create two executions.

Verification strategy: deterministic unit checks for canonical fingerprints and API mappings, real PostgreSQL integration tests for safety/rollback/replay/concurrency, full regression suite, and later independent spec-based audit. Generated property testing is not planned unless implementation evidence shows a concrete need. Mutation testing remains conditional; after implementation, the compact pure decision logic will be evaluated as a possible targeted pilot.

Requirement/invariant traceability and executed results are recorded below after the planned contract so planned and observed evidence remain distinct.

Initial independent spec-based audit: `FAIL` — one blocker and three minor findings. Bounded remediation evidence is recorded below. The second independent re-audit was executed and returned `FAIL` only because one MINOR documentation inconsistency remained; all technical findings F-01 through F-04 were verified as resolved. Final independent documentation confirmation subsequently passed with no findings. At the time of the final independent documentation confirmation, C04 remained `IN_PROGRESS` and was `READY_FOR_HUMAN_APPROVAL`; human approval and delivery had not yet occurred.

## Alternatives considered

- rely only on unique database constraints
- rely only on frontend button disabling
- accept duplicate requests for prototype simplicity

## Why those are insufficient

Payment correctness must be enforced at the backend/ledger level, not delegated to the UI.

## Actual implementation

Phase 1 implemented the bounded C04 safety layer while preserving the C03 transaction path:

- `PaymentService` deterministically hashes only the approved immutable payload fields and passes the fingerprint through the ledger-neutral interface;
- `ConventionalLedger` acquires sorted PostgreSQL transaction-scoped advisory locks for both the idempotency key and payment ID before deciding whether to execute, replay, or conflict;
- `idempotency_records` gives each request key a PostgreSQL-enforced unique binding to one fingerprint and completed payment;
- schema initialization transactionally derives fingerprints and idempotency bindings for valid completed C03 rows, is idempotent on rerun, and refuses inconsistent legacy bindings rather than inventing data;
- the existing payments table records the immutable request fingerprint, while its original opaque idempotency-key field remains available as request evidence;
- same-key/same-payload and same-payment-ID/same-payload requests return the original committed `LedgerResult` without another balance update or Transaction;
- different-payload reuse raises stable ledger-neutral conflict errors; the minimal FastAPI `POST /payments` adapter maps those errors to HTTP 409;
- invalid accounts and insufficient funds roll the transaction back without persisted payment state, while Pydantic/domain validation rejects malformed and non-positive requests before ledger execution;
- a controlled failure after the Payment insert proves that balances, Payment, Transaction, and idempotency state all roll back and that the same request can then succeed on retry.
- payer-equals-merchant validation now uses a stable ledger-neutral application error and maps to HTTP 422 before ledger execution.

### Files changed in Phase 1

- `src/upi_payment_experiment/api.py`
- `src/upi_payment_experiment/errors.py`
- `src/upi_payment_experiment/ledger.py`
- `src/upi_payment_experiment/payment_service.py`
- `src/upi_payment_experiment/conventional_ledger.py`
- `src/upi_payment_experiment/postgres_schema.sql`
- `tests/test_c04_payment_safety.py`
- `tests/test_c03_conventional_ledger.py` (fixture reset includes the new C04 table)
- `tests/test_c01_baseline.py` (narrow dependency-baseline update)
- `pyproject.toml`
- `PROJECT_CONTROL.md`
- `ARCHITECTURE_AND_DECISIONS.md`
- `PAYMENT_CARD_EVIDENCE_MAP.md`

## Problems encountered

The first complete C04 run was functionally successful (`39 passed`) but emitted two deprecation warnings from the synchronous Starlette/FastAPI `TestClient` path. The runtime implementation itself did not fail.

Root cause: the first API tests imported the legacy synchronous `TestClient`, whose current dependency path warns about the httpx transition and a deprecated AnyIO alias.

Fix: the API tests were changed to the existing httpx dependency's native asynchronous `ASGITransport` and `AsyncClient`. The focused C04 suite and then the full suite were rerun without warnings; no runtime behavior or additional dependency changed.

## Test evidence

Executed against the real local PostgreSQL service:

```text
full suite: 41 passed
C01: 3 passed
C02: 16 passed
C03: 3 passed
C04: 19 passed
```

C04 evidence covers the preserved successful transfer, exact persisted state and history, invalid payer, invalid merchant, insufficient balance, zero/negative amount, malformed API input, self-transfer rejection, same-key replay, idempotency conflict, duplicate-payment replay, payment-ID conflict, already-completed replay, C03-era completed-payment migration, controlled persistence failure plus safe retry, HTTP conflict mapping, deterministic fingerprint behavior, and two requests forced to overlap on the same PostgreSQL coordination lock while producing one committed execution.

## EXECUTED Requirement / Invariant Traceability

| Requirement / invariant | Implementation | Test / evidence | Result |
|---|---|---|---|
| Canonical payload contains exactly five approved fields | `canonical_payment_fingerprint()` | independent variation of every included and represented excluded field in `test_canonical_fingerprint_uses_only_approved_immutable_payload` | PASS AFTER REMEDIATION |
| Successful C03 flow remains consistent | service, adapter, schema | `test_successful_c03_flow_still_commits_one_consistent_payment` plus C03 regression | PASS |
| Invalid accounts and insufficient balance do not mutate state | transactional validation in `ConventionalLedger` | parametrized rejected-ledger integration test | PASS |
| Zero, negative, and malformed requests do not execute/persist | FastAPI/Pydantic and domain validation | API validation integration tests | PASS |
| Same key and payload returns original result with no second debit | idempotency lookup under PostgreSQL lock | same-key replay integration test | PASS |
| Same key and different payload conflicts without execution | fingerprint comparison and `IdempotencyConflictError` | integration test plus HTTP 409 API test | PASS |
| Duplicate payment ID with same payload returns original result | payment lookup under PostgreSQL lock | duplicate-payment replay integration test | PASS |
| Duplicate payment ID with different payload conflicts | fingerprint comparison and `PaymentConflictError` | integration test plus HTTP 409 API test | PASS |
| Completed payment replays safely, including C03-era state | migration backfill plus committed-result reconstruction | new-path replay and real C03-schema migration/replay integration tests | PASS AFTER REMEDIATION |
| Persistence failure leaves no partial or terminal state and permits retry | one transaction plus controlled post-Payment-insert failure seam | controlled persistence-failure integration test | PASS |
| Concurrent same-key requests produce one committed execution | sorted transaction-scoped advisory locks plus persistent PK | deterministic two-thread test observes the second PostgreSQL session waiting on the held lock | PASS AFTER REMEDIATION |
| One logical success has one Payment and one Transaction agreeing with balances | PostgreSQL transaction and constraints | successful, replay, rollback, and concurrency state assertions | PASS |
| Self-transfer is a controlled invalid request | shared `InvalidPaymentError` plus FastAPI mapping | API and fresh database-state regression test | PASS AFTER REMEDIATION |

## Initial Independent Audit and Bounded Remediation

The initial independent C04 audit returned `FAIL`.

Findings retained as evidence:

- `F-01 BLOCKER`: valid C03-completed rows had no derived fingerprint or idempotency-table binding after schema upgrade. A same-key/different-payment audit probe executed a second transfer, and a same-payment replay conflicted instead of returning the original result.
- `F-02 MINOR`: the concurrency test synchronized thread starts but did not deterministically prove overlap inside the transaction.
- `F-03 MINOR`: the fingerprint test proved exclusions and amount inclusion but did not independently vary every required canonical field.
- `F-04 MINOR`: payer-equals-merchant raised a bare adapter `ValueError` and surfaced as HTTP 500.

Root causes:

- the incremental `request_fingerprint` column was nullable and no migration derived fingerprints or `idempotency_records` from existing C03 data;
- the original concurrency barrier ran before connection acquisition rather than after PostgreSQL coordination locks were held;
- canonical field coverage was asserted too broadly from a partial variation test;
- self-transfer validation lived only as an adapter check without a shared error mapping.

Bounded remediation:

- schema initialization now joins completed C03 Payment, account, and Transaction data, derives the exact canonical fingerprint with the shared ledger-neutral function, updates missing fingerprints, and inserts the original key binding in the same initialization transaction;
- rerunning initialization validates existing derived values and performs no duplicate write; inconsistent legacy bindings cause transactional failure rather than guessed state;
- a real isolated PostgreSQL schema test starts with the delivered C03-style tables and data, runs C04 initialization twice, replays the original result, rejects different-payload key reuse, and verifies unchanged balances plus one Payment and Transaction;
- the concurrency test pauses the first request after it holds both advisory locks, identifies the second connection by PostgreSQL `application_name`, observes `pg_stat_activity.wait_event_type = 'Lock'`, then releases the first request and verifies one execution;
- the fingerprint test independently varies payment ID, payer ID, merchant ID, amount, and currency, and separately verifies exclusion of idempotency key, timestamp, status, transaction ID, and HTTP metadata;
- shared `InvalidPaymentError` validation occurs in `PaymentService`, remains as adapter defense in depth, and maps to HTTP 422 with zero persisted state.

Remediation execution history:

- the first focused run stopped with 19 setup errors because the prior independent audit intentionally left an inconsistent synthetic duplicate-key state; the new migration correctly failed closed, and only the disposable test database state was reset;
- the next focused run produced `18 passed, 1 failed` because the new legacy fixture tried to combine parameterized inserts with multiple SQL commands; the fixture was corrected to execute DDL and parameterized inserts separately;
- final focused C04 result: `19 passed`;
- final full-suite result: `41 passed`.

Bounded remediation self-audit: `PASS FOR F-01 THROUGH F-04 — READY_FOR_INDEPENDENT_RE-AUDIT`. This is not an independent re-audit and does not grant the C04 Exit Gate.

## Property / Invariant Testing Result

Generated property testing is `NOT_APPLICABLE` for C04 Phase 1 because the bounded finite decision matrix is exercised deterministically, including the real database race. No Hypothesis dependency was added. Deterministic invariant tests are executed and PASS.

## Mutation Testing Result

Mutation testing remains conditional and was not run or added as a dependency. A later targeted pilot could provide value for the compact canonical-fingerprint field selection and replay/conflict equality branches, but mutation testing is not required to establish the PostgreSQL transaction and concurrency evidence in this Phase.

## Known limitations

- The API is intentionally limited to `POST /payments`; UI, QR, blockchain, and benchmarks remain later Cards.
- Rejected attempts are rolled back rather than stored as successful Payment or Transaction records; no production rejection journal is claimed.
- The schema is a prototype initialization script rather than a production migration/versioning system.
- Operational authentication, authorization, monitoring, reconciliation, and multi-node deployment behavior are not implemented.

## C04 Phase 1 Learning Record

### What did we build?

We added the minimal payment-safety path around the C03 ledger: deterministic canonical request identity, PostgreSQL-backed replay/conflict coordination, safe duplicate-payment behavior, invalid-request and failure rollback handling, and a small `POST /payments` FastAPI boundary.

### Why did we build it this way?

Canonicalization belongs in the shared service so it can remain stable for a future ledger, while PostgreSQL advisory locks, uniqueness, and atomic persistence remain inside the adapter. This preserves the architecture and makes the concurrency proof use the same database transaction as the payment.

### What did we initially misunderstand?

The initial C04 implementation correctly handled payments created through the new C04 path, but it missed the C03-to-C04 persisted-state migration requirement. Existing completed C03 payments had no derived request fingerprints or idempotency bindings, so legacy replay and legacy-key reuse were unsafe. Separately, the initial API-test implementation used the synchronous Starlette/FastAPI `TestClient` path without accounting for deprecations in the installed current versions.

### What failed?

The first full Phase 1 run passed all 39 tests but emitted two API-test deprecation warnings, so it was not accepted as the final warning-free evidence. More importantly, the first independent C04 audit returned `FAIL`: it demonstrated the F-01 legacy-payment/idempotency defect and identified F-02 through F-04. The green Phase 1 run therefore did not prove complete C04 correctness.

### Why did it fail?

The Phase 1 tests created payments through the new C04 path and did not exercise a genuine delivered C03 database upgraded into C04, so no migration/backfill derived fingerprint and idempotency state for existing C03 completed payments. The concurrency test synchronized too early to prove transaction overlap, the fingerprint evidence overclaimed required-field coverage, and self-transfer validation was not mapped through a stable shared error. Separately, the warnings came from the legacy synchronous test-client compatibility path rather than payment execution or the API contract.

### How was it fixed?

The bounded remediation added transactional C03-to-C04 migration/backfill with deterministic legacy fingerprint derivation and idempotency binding, and made inconsistent legacy state fail closed. It added a genuine C03-schema migration integration test, a deterministic PostgreSQL lock-wait concurrency test, complete included/excluded fingerprint-field tests, and shared `InvalidPaymentError` validation with HTTP 422 self-transfer mapping. The API tests were also moved to httpx `ASGITransport` and `AsyncClient`, already within the approved test dependency. C04 and the full suite were rerun successfully without warnings.

### What other design could have been used?

Alternatives included a Python-only pre-check, only a unique constraint, or an in-memory request cache. Those cannot atomically coordinate concurrent requests with balance and persistence changes. A dedicated reservation workflow with explicit in-progress states was also possible but would add unnecessary prototype complexity.

### What trade-off did we accept?

Transaction-scoped advisory locks plus a minimal idempotency table keep the design compact and concurrency-safe, but they are PostgreSQL-specific mechanics and the initialization SQL is not a production migration system. The ledger-neutral contract retains only the fingerprint and logical results.

### What test proves the result?

The original Phase 1 produced seventeen C04 tests and 39 full-suite passes. After the failed independent audit and bounded remediation, nineteen C04 tests use real PostgreSQL for migration, failure, replay, rollback, and deterministic lock-wait semantics and exercise the ASGI API for validation and conflict mapping. The remediated full regression result is 41 passed, including all 22 pre-C04 tests.

### What would we do differently in a production payment system?

A production system would add schema migrations, authenticated callers, operational observability, durable reconciliation and request-in-progress recovery, broader load/concurrency testing, and a retained audit model for rejected attempts. None is claimed as implemented here.

### What did this Card teach us?

Green tests are insufficient when they do not reproduce the previous persisted system state. Schema evolution must preserve prior committed business semantics, and migration boundaries need explicit integration tests. The independent audit caught a real financial correctness defect that the original test suite missed. Evidence must not claim more than tests prove. Duplicate safety must be decided while holding database-backed coordination, not with a process-local check; request identity and business payment identity require separate conflict rules; and rollback evidence must cover idempotency state together with balances, Payment, and Transaction persistence.

## Second Independent Re-Audit and Documentation Remediation Record

Second independent re-audit: `FAIL` — technical remediation was verified, but one `MINOR` documentation inconsistency remained.

Technical findings `F-01` through `F-04`: `PASS / RESOLVED`.

New finding: `R-01 MINOR` — the C04 Learning Record incorrectly denied the payment-semantic misunderstanding exposed by F-01 and described only the earlier TestClient warning under its failure history.

Required remediation: documentation only. This bounded work item corrects the Learning Record while preserving the initial audit failure, all four findings, remediation execution history, and executed test results. No final independent re-audit PASS, C04 Exit Gate PASS, human approval, or C04 completion is claimed.

## Final Independent Documentation Confirmation

Final independent documentation confirmation: `PASS`.

Results: PAYMENT_CARD_EVIDENCE_MAP, PROJECT_CONTROL, Roadmap C04/G03 consistency, AGENTS workflow consistency, cross-document consistency, and repository scope/Git state all passed. Findings: `NONE`.

Technical findings `F-01` through `F-04`: `RESOLVED`. `R-01`: `RESOLVED`.

C04 Exit-Gate readiness at the time of final confirmation: `READY_FOR_HUMAN_APPROVAL`. Human approval was then still `NOT GRANTED`; C04 was still `IN_PROGRESS` and not `COMPLETE`. No delivery had occurred at that point. C05 remained `NOT_STARTED`.

## Exit Gate

Original Phase 1 self-assessment: `PASS — READY_FOR_INDEPENDENT_AUDIT`.

Initial independent spec-based audit: `FAIL`.

Bounded remediation self-audit: `PASS FOR F-01 THROUGH F-04 — READY_FOR_INDEPENDENT_RE-AUDIT`.

All required failure scenarios have executed without balance corruption, including:

- same idempotency_key + same canonical payload returns the original result with no second debit
- same idempotency_key + different canonical payload is rejected with HTTP 409 Conflict
- `payment_id` remains distinct from `idempotency_key`

Second independent re-audit: `FAIL` — all technical findings were resolved; one `MINOR` documentation inconsistency remained.

Documentation remediation: performed in this bounded work item.

Final independent documentation confirmation: `PASS`; findings: `NONE`.

C04 remained `IN_PROGRESS` at the time of the pre-delivery Exit Gate record. Exit Gate: `PASS`, with human approval still required before delivery. Human approval was then `NOT GRANTED`; no delivery had occurred at that point. C05 remained `NOT_STARTED`.

## C04 Controlled Delivery Record

Human delivery approval for C04: `GRANTED`.

Controlled delivery: `COMPLETE`.

C04 delivery status: `COMPLETE`.

C04 status: `COMPLETE`.

C04 Exit Gate: `PASS`.

Final independent documentation confirmation: `PASS`; findings: `NONE`.

Technical findings `F-01` through `F-04`: `RESOLVED`. `R-01`: `RESOLVED`.

Final validation executed before completion-state closure:

```text
docker compose ps: PASS — PostgreSQL healthy
full suite: 41 passed
C04: 19 passed
C03 regression: 3 passed
compileall: PASS
pip check: PASS — No broken requirements found
git diff --check: PASS
```

Delivery branch: `main`.

The immutable delivery SHA is determined by Git after the single delivery commit and is reported in the final delivery output. It is intentionally not duplicated in this pre-commit documentation state, so no self-referential second documentation commit is created.

C05 status: `NOT_STARTED`.

C05 authorization: `NOT_GRANTED`.

No automatic advancement occurred. Active Card is `NONE`; Next Allowed Card is `C05` for sequence eligibility only.

---

# 8. C05 — QR Payment Initiation

## Status

`COMPLETE — PHASE 1 IMPLEMENTED; C05-A01/A02/A03 RESOLVED; FINAL INDEPENDENT RE-AUDIT PASS; CONTROLLED DELIVERY COMPLETE`

## Goal

Connect a real QR payload to the payment workflow without turning QR into the ledger.

## Why this Card exists

The project brief includes QR-based merchant payments.

This Card demonstrates how payment initiation is separated from payment settlement.

## Planned QR payload

The only canonical C05 merchant QR payload is:

```text
upi-demo://pay?merchant_id=<single-non-empty-merchant-id>
```

Example:

```text
upi-demo://pay?merchant_id=M001
```

The parser contract is strict:

- scheme is exactly `upi-demo`
- authority/host is exactly `pay`
- path is empty
- query contains exactly one `merchant_id`
- `merchant_id` is non-empty after normal URI parsing
- duplicate `merchant_id` parameters are rejected
- additional query parameters are rejected
- fragments are rejected
- malformed payloads, wrong schemes, wrong authorities/hosts, and missing merchant IDs are rejected
- C05 adds no merchant-ID regex beyond existing project/domain validation

## Why the payload stays small

The QR should identify the payment target.

The QR contains merchant identity only. Amount, `payer_id`, `payment_id`, `idempotency_key`, status, `transaction_id`, ledger choice, and persistence information are not encoded. Amount remains a separate payment input after decoding.

The ledger remains responsible for:

- balance validation
- transfer
- transaction status
- audit trail

## Planned interview behavior

A QR is actually generated.

Camera integration is optional.

For the first interview version, scanning may be simulated by reading/decoding the QR inside the demo application.

The planned minimal C05 dependency for real QR generation and internal/test decoding is `zxing-cpp`. At contract-lock time it was not yet installed or added to project configuration; the subsequent authorized Phase 1 installation is recorded below.

## Integration boundary and unknown merchants

QR logic ends after safely parsing and returning `merchant_id`. It does not implement a merchant database or business lookup. The decoded value is passed into the existing path:

```text
QR decode
→ merchant_id
→ existing FastAPI/application payment boundary
→ PaymentRequest.merchant_id
→ PaymentService
→ LedgerInterface
→ ConventionalLedger
```

An unknown merchant cannot successfully initiate payment because the existing C04 account-validation behavior rejects it. C05 does not duplicate `ACCOUNT_NOT_FOUND` or any payment-validation logic.

## C04 reuse

C05 reuses the delivered C04 safety path. It does not reimplement `payment_id` semantics, `idempotency_key` semantics, canonical payment fingerprinting, replay handling, duplicate-payment handling, conflict handling, balance validation, persistence safety, transaction execution, rollback behavior, or C04 error semantics.

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

C05 Phase 1 added `src/upi_payment_experiment/qr.py`, an isolated QR/application adapter with:

- canonical merchant URI construction using only `merchant_id`;
- strict parsing for the approved scheme, authority, empty path, one non-empty merchant parameter, no additional parameters, and no fragment;
- raw ASCII-control-character rejection before URI parsing can normalize malformed text;
- strict UTF-8 percent decoding plus decoded ASCII-control-character rejection for query keys and values;
- raw fragment-delimiter rejection, including an empty fragment delimiter;
- controlled QR-specific exceptions that prevent raw library failures from becoming payment-domain behavior;
- real QR creation through `zxingcpp.create_barcode()` and `Barcode.to_image()`;
- real internal decoding through `zxingcpp.read_barcode()` followed by strict payload parsing;
- no account lookup, payment execution, ledger access, persistence, idempotency, or C04 safety implementation.

No new API endpoint was added. C05 integration supplies the decoded `merchant_id` to the delivered `POST /payments` request, which continues through `PaymentService`, `LedgerInterface`, and `ConventionalLedger`.

The approved runtime dependency is declared as `zxing-cpp>=3,<4`; the actually installed and executed version is `3.1.1`.

### Files changed in C05 Phase 1

- `src/upi_payment_experiment/qr.py`
- `tests/test_c05_qr_payment_initiation.py`
- `pyproject.toml`
- `tests/test_c01_baseline.py` (narrow dependency-baseline update)
- `PROJECT_CONTROL.md`
- `UPI_PAYMENT_INTERVIEW_ROADMAP.md`
- `ARCHITECTURE_AND_DECISIONS.md`
- `PAYMENT_CARD_EVIDENCE_MAP.md`

## Problems encountered

`zxing-cpp` was not initially installed. Version `3.1.1` was installed into the existing `.venv`, and its live Python API was inspected before implementation. The binding exposed the current `create_barcode()` API, `Barcode.to_image()`, and `read_barcode()`.

The first smoke probe generated and decoded the QR but failed while trying to print a non-existent `zxingcpp.Image.width` attribute. Root cause: the binding's image object exposes its dimensions through the Python buffer protocol rather than a `width` attribute. The probe was corrected to use `memoryview(image)`, then verified a 165 by 165 image buffer and the exact decoded URI.

During strict-contract review, Python's `urlsplit()` was observed to normalize an uppercase URI scheme to lowercase. Root cause: relying only on `parsed.scheme` would have accepted `UPI-DEMO`, contrary to the exact lowercase contract. A raw-scheme check was added before parsing, malformed percent escapes were rejected explicitly, and focused cases were added. The final focused suite passed all 21 cases, including controlled decoder-error translation.

The formal independent audit then found `C05-A01` (`MAJOR`): `urlsplit()` also removes raw TAB, newline, and carriage-return characters before later authority validation. As a result, the raw payload `upi-demo://pa<TAB>y?merchant_id=M001` could decode and resolve as `M001`, even though its raw authority was not exactly `pay`. This made the original parser matrix and its claim of complete malformed/wrong-authority coverage incomplete.

Bounded remediation added a raw ASCII control-character guard in `parse_merchant_qr_payload()` before `urlsplit()` or query parsing. The guard rejects `U+0000` through `U+001F` and `U+007F`, without adding a merchant-ID regex or changing valid merchant/payment semantics. Public parser regressions cover TAB, newline, and carriage return in the authority and representative scheme, query-key, and query-value locations.

The subsequent independent re-audit resolved `C05-A01`, but found `C05-A02` (`MAJOR`): syntactically complete percent escapes were passed to `parse_qsl()` with replacement decoding, so invalid UTF-8 such as `merchant_id=%C3%28` became `�(` and was accepted. Percent-encoded ASCII controls such as `%00`, `%0A`, and `%7F` could similarly become accepted merchant-ID content. This meant malformed-payload rejection was still incomplete.

Bounded C05-A02 remediation retained the C05-A01 raw-input guard, configures `parse_qsl()` with UTF-8 and `errors="strict"`, and rejects decoded ASCII controls in every parsed query key and value before the one-`merchant_id` contract is accepted. It adds direct public-parser regressions for invalid UTF-8, malformed percent syntax, encoded controls in values and a query key, canonical input, and valid UTF-8 merchant text. Mutation-resistance tests demonstrate that replacement decoding, removal of the decoded-control guard, or removal of percent-triplet validation restores acceptance of representative invalid inputs.

The second independent re-audit resolved C05-A02 but found `C05-A03` (`MAJOR`): the parser rejected only a non-empty `parsed.fragment`, so `upi-demo://pay?merchant_id=M001#` had an empty parsed fragment and incorrectly resolved to `M001`. This violated the canonical requirement that no fragment is permitted.

Bounded C05-A03 remediation rejects a raw `#` delimiter before URI parsing, including when its fragment text is empty, while leaving percent-encoded `%23` available as merchant data. Direct public-parser regressions cover empty and non-empty fragments, canonical input, percent-encoded hash input, and a mutation-resistance proof that removal of the raw-delimiter guard restores the original empty-fragment acceptance.

## Tests

Executed against `zxing-cpp 3.1.1` and the healthy local PostgreSQL Compose service:

```text
QR dependency import/version check: PASS — 3.1.1
QR generation/decode smoke: PASS — decoded merchant_id M001
C05 focused suite: 21 passed
C04 regression: 19 passed
C03 regression: 3 passed
full suite: 62 passed
compileall: PASS
pip check: PASS — No broken requirements found
git diff --check: PASS
```

No skipped, xfailed, unexpectedly deselected tests, or warnings were reported.

### C05-A01 remediation validation

Executed after the formal independent audit against the healthy local PostgreSQL Compose service:

```text
Focused C05-A01 control-character regressions: 6 passed (the targeted selection intentionally deselected 21 other C05 tests)
Direct real-QR audit probes: PASS — TAB, newline, and carriage-return authority variants decode as raw text but are rejected with INVALID_QR_PAYLOAD
Canonical payload probe: PASS — upi-demo://pay?merchant_id=M001 → M001
C05 focused suite: 27 passed
C04 regression: 19 passed
C03 regression: 3 passed
full suite: 68 passed
```

At the end of C05-A01 remediation, the formal independent audit remained `FAIL` until a separate independent re-audit verified the fix. The subsequent audit resolved C05-A01 and found C05-A02; the final independent re-audit record below supersedes this historical state.

### C05-A02 remediation validation

The independent re-audit that found C05-A02 was `FAIL`; C05-A01 is `RESOLVED`. The following bounded remediation validation was executed afterward against the healthy local PostgreSQL Compose service:

```text
Focused C05-A02 regressions: 16 passed; 27 other C05 tests intentionally deselected by the focused selection
Direct parser probes: PASS — %C3%28, %C3, %, %0, %GG, %00, %09, %0A, %0D, %1F, and %7F rejected with INVALID_QR_PAYLOAD
Canonical parser probe: PASS — upi-demo://pay?merchant_id=M001 → M001
Valid UTF-8 parser probe: PASS — upi-demo://pay?merchant_id=M%C3%A5l → Mål
C05-A01 authority probes: PASS — raw TAB, newline, and carriage return variants rejected with INVALID_QR_PAYLOAD
C05 focused suite: 43 passed
C04 regression: 19 passed
C03 regression: 3 passed
full suite: 84 passed
compileall: PASS
pip check: PASS — No broken requirements found
git diff --check: PASS
```

No skips, xfails, warnings, or unintentional deselections were reported. The 27 focused-test deselections above were intentional and are not counted as passes. At the end of C05-A02 remediation, another independent re-audit was pending; that audit resolved C05-A02 and found C05-A03.

### C05-A03 remediation validation

The second independent re-audit that found C05-A03 was `FAIL`; C05-A01 and C05-A02 are `RESOLVED`. The following bounded remediation validation was executed afterward against the healthy local PostgreSQL Compose service:

```text
Focused C05-A03 regressions: 5 passed; 43 other C05 tests intentionally deselected by the focused selection
Direct parser probes: PASS — empty and non-empty raw fragment delimiters rejected with INVALID_QR_PAYLOAD
Canonical parser probe: PASS — upi-demo://pay?merchant_id=M001 → M001
Percent-encoded hash probe: PASS — upi-demo://pay?merchant_id=M%23001 → M#001
C05-A01 probes: PASS — raw TAB, newline, and carriage-return authority variants rejected with INVALID_QR_PAYLOAD
C05-A02 probes: PASS — malformed UTF-8, malformed percent syntax, and decoded ASCII-control variants rejected with INVALID_QR_PAYLOAD; valid M%C3%A5l → Mål
C05 focused suite: 48 passed
C04 regression: 19 passed
C03 regression: 3 passed
full suite: 89 passed
compileall: PASS
pip check: PASS — No broken requirements found
git diff --check: PASS
```

No skips, xfails, warnings, or unintentional deselections were reported. The 43 focused-test deselections above were intentional and are not counted as passes. At the end of C05-A03 remediation, the final independent re-audit was pending.

## Final Independent Re-Audit Record

Final independent re-audit: `PASS`.

- C05-A01: `RESOLVED`
- C05-A02: `RESOLVED`
- C05-A03: `RESOLVED`
- Findings: `NONE`
- All 16 C05 acceptance items: independently confirmed `PASS`
- C05 focused tests: `48/48 passed`
- C04 regression: `19/19 passed`
- C03 regression: `3/3 passed`
- Full suite: `89/89 passed`
- compileall, pip check, and `git diff --check`: `PASS`
- Architecture boundary, real QR generation/decode, C04 safety preservation, and scope review: `PASS`
- C05 Exit Gate: `PASS`
- READY_FOR_HUMAN_DELIVERY_APPROVAL: `YES`

Before controlled delivery, C05 was `IN_PROGRESS` pending explicit human delivery approval and controlled Git delivery. The controlled delivery record below supersedes that pending state.

## C05 Controlled Delivery Record

- Human delivery approval: `GRANTED`
- Final independent re-audit: `PASS`
- Findings: `NONE`
- Exit Gate: `PASS`
- Delivery status: `COMPLETE`
- Delivery branch: `main`
- C05 focused suite: `48 passed`
- C04 regression: `19 passed`
- C03 regression: `3 passed`
- Full suite: `89 passed`
- `compileall`: `PASS`
- `pip check`: `PASS — No broken requirements found`
- `git diff --check`: `PASS`
- Push result and the immutable delivery SHA are reported in the final delivery output after post-delivery verification; they are intentionally not duplicated here to avoid a self-referential documentation commit.

Evidence artifacts are the C05 module and focused test file listed above, the executed command outputs, and this traceable record. QR images were generated and decoded in memory; no runtime QR artifact, secret, or customer data was persisted.

## Planned C05 Acceptance Contract

C05 must eventually prove:

1. a real QR is generated;
2. the generated QR contains the exact canonical merchant URI;
3. the QR can be decoded internally;
4. decoded `merchant_id` equals the intended merchant;
5. malformed payload is rejected;
6. wrong scheme is rejected;
7. wrong authority/host is rejected;
8. missing `merchant_id` is rejected;
9. duplicate `merchant_id` is rejected;
10. extra query parameters are rejected;
11. fragment-bearing payload is rejected;
12. an unknown merchant cannot produce a successful payment;
13. a valid decoded `merchant_id` can initiate the existing conventional payment flow;
14. amount remains outside the QR;
15. existing C04 safety behavior remains unchanged;
16. QR logic contains no ledger, persistence, or idempotency implementation.

## EXECUTED Requirement / Invariant Traceability

| Requirement / invariant | Implementation | Test / evidence | Result |
|---|---|---|---|
| Real QR generated, exact URI encoded, internally decoded, intended merchant returned | `build_merchant_qr_payload()`, `generate_merchant_qr()`, `decode_merchant_qr()` | `test_real_qr_generation_and_decode_round_trip_uses_zxingcpp` independently invokes `zxingcpp.read_barcode()` on the generated image before strict parsing | PASS |
| Malformed payload and wrong scheme rejected | raw exact-scheme check, raw/decoded ASCII-control guards, complete-percent validation, and strict UTF-8 query decoding | initial parametrized noncanonical test plus C05-A01 and C05-A02 public-parser regressions | Initial audit: `FAIL` for raw-control normalization; C05-A01 independent re-audit: `RESOLVED`; subsequent re-audit: `FAIL` for C05-A02 malformed decoding; final independent re-audit: `PASS` |
| Wrong authority and non-empty path rejected | raw ASCII-control guard, exact `netloc`, and empty-path checks | initial wrong-authority/path cases plus TAB/newline/carriage-return authority regressions | Initial independent audit: `FAIL` for raw-control normalization; final independent re-audit: `PASS` |
| Missing, empty, or duplicate merchant ID rejected | exact one-item query contract and non-empty decoded value | parametrized missing, empty, whitespace-only, and duplicate cases | PASS |
| Extra query parameters and fragments rejected | exact one-item query contract and raw fragment-delimiter guard | parametrized extra-amount/non-empty-fragment cases plus C05-A03 empty-fragment and percent-encoded-hash public-parser regressions | Initial audits did not cover an empty fragment delimiter; second independent re-audit: `FAIL` for C05-A03; final independent re-audit: `PASS` |
| Unknown merchant cannot successfully pay | QR returns `M404`; existing C04 account validation remains authoritative | `test_unknown_decoded_merchant_uses_existing_c04_rejection` proves HTTP 404 `ACCOUNT_NOT_FOUND` and unchanged database state | PASS |
| Valid decoded merchant initiates the existing conventional path | decoded `merchant_id` is placed in the existing `POST /payments` request | `test_valid_decoded_merchant_uses_existing_safe_payment_path` proves SUCCESS, balances `90000/10000`, one Payment, one Transaction, and one idempotency record | PASS |
| Amount and all other payment/ledger fields remain outside QR | merchant-only payload builder | `test_canonical_payload_contains_only_merchant_identity` | PASS |
| C04 safety remains intact and is not bypassed | unchanged API/service/ledger implementation; replay uses existing idempotency path | valid C05 integration replays once without a second debit; focused C04 regression 19 passed | PASS |
| QR has no ledger, persistence, or idempotency implementation | isolated imports limited to `urllib` and `zxingcpp` | `test_qr_module_is_isolated_from_payment_and_persistence_logic` plus source/diff review | PASS |

## Deterministic Invariant Result

Original Phase 1 result: `PASS`. The formal independent audit found `C05-A01` because the original finite parser matrix omitted raw ASCII-control-character normalization cases, so it did not fully prove malformed-payload or wrong-authority rejection. C05-A01 bounded remediation and independent re-audit resolved that finding. The subsequent independent re-audit found `C05-A02`: the matrix also omitted invalid UTF-8 and decoded-control percent-encoding cases; C05-A02 remediation and independent re-audit resolved it. The next independent re-audit found `C05-A03`: an empty raw fragment delimiter was omitted from the deterministic matrix. C05-A03 bounded remediation added direct public-parser and mutation-resistance evidence that pass. The final independent re-audit resolved C05-A01, C05-A02, and C05-A03, found no additional findings, and returned `PASS`.

## Property Testing Result

Generated property testing is `NOT_APPLICABLE FOR C05 PHASE 1`. The canonical grammar is intentionally finite and strict. The original deterministic-matrix rationale overstated its coverage until C05-A01, C05-A02, and C05-A03 added raw-control, malformed-percent, strict-UTF-8, decoded-control, and raw-fragment-delimiter cases. No Hypothesis dependency was added.

## Mutation Testing Result

Mutation testing is `NOT_APPLICABLE FOR C05 PHASE 1`. The exact payload, remediated parser branch outcomes, real library round trip, excluded-field assertions, and import-boundary assertions provide direct evidence for the bounded QR adapter. No mutation dependency was added.

## Known limitations

- QR generation and decoding are internal/in-memory only; camera and device integration remain deferred.
- C05 supports one static merchant-identity URI and intentionally excludes amount, order data, signatures, and expiry.
- The QR layer does not pre-resolve merchants; unknown merchants are rejected only when the existing payment path validates accounts.
- No UI, blockchain integration, benchmark, authentication, production bank integration, or real-money behavior is implemented.

## C05 Phase 1 Learning Record

### What did we build?

We built a strict merchant-only QR adapter that constructs the canonical URI, generates a real QR image, decodes that image through `zxing-cpp`, validates the decoded URI, and returns only `merchant_id` for the existing payment path.

### Why did we build it this way?

Keeping QR mechanics in a dedicated module preserves the boundary between initiation and settlement. The existing API and C04 service/ledger path remain the single payment engine.

### What did we initially misunderstand?

The installed binding's image dimensions are exposed through the buffer protocol rather than a `width` attribute, and standard URI parsing normalizes both scheme case and raw control characters even though the approved contract requires exact raw URI structure.

### What failed?

The first smoke command failed only while printing `Image.width`; QR generation and decoding had already executed. No implementation or final validation test failed.

### Why did it fail?

The smoke probe assumed an image-object attribute that the installed nanobind API does not expose.

### How was it fixed?

The probe and tests use `memoryview(image)` for image evidence. The parser checks the raw scheme and raw ASCII control characters before `urlsplit()`, and rejects malformed percent escapes, preventing normalization from weakening the contract.

### What other design could have been used?

Separate generation and decoding libraries, a camera stack, or a new QR API endpoint were possible. They were not selected because `zxing-cpp` provides both required operations and the existing payment endpoint already owns submission.

### What trade-off did we accept?

The QR module depends on a native binding and supports only the bounded static merchant URI, in exchange for one real generator/decoder dependency and a small auditable surface.

### What test proves the result?

The primary real-QR test independently decodes the generated image through `zxingcpp.read_barcode()` and then verifies the module returns `M001`. Database-backed API tests prove unknown-merchant rejection and one safe successful/replayed payment.

### What would we do differently in a production payment system?

A production design could add signed and expiring payloads, merchant-directory controls, authenticated callers, device scanning, and operational telemetry after defining those requirements explicitly.

### What did this Card teach us?

Library API assumptions and URI normalization both need executable checks. A tiny initiation adapter can provide real QR evidence while leaving payment correctness entirely in the already-tested application and ledger path.

## C05 Phase 1 Self-Audit

Original Phase 1 result: `PASS — READY_FOR_INDEPENDENT_AUDIT`.

The completed diff and source were reviewed against all 16 planned acceptance items. The review found no C06+ work, QR-to-ledger coupling, duplicate payment or merchant-lookup logic, amount or payment fields in the QR, alternate accepted payload format, deprecated `write_barcode()` usage, unnecessary dependency, mocked/false-green primary QR proof, weakened C04 behavior, undocumented changed file, secret, or stale live state. Protected C03/C04 implementation files are unchanged, and C06 remains `NOT_STARTED` and unauthorized.

The initial formal independent audit result was `FAIL` on `C05-A01` (`MAJOR`); the first independent re-audit resolved C05-A01 and returned `FAIL` on C05-A02 (`MAJOR`). The second independent re-audit resolved C05-A02 and returned `FAIL` on C05-A03 (`MAJOR`). The final independent re-audit resolved C05-A01, C05-A02, and C05-A03, found `NONE` remaining, and returned `PASS`.

At that pre-delivery point, human delivery approval was `NOT YET GRANTED` and Git delivery was `NOT PERFORMED`. The subsequent controlled delivery record supersedes that pending state.

## Exit Gate

- QR generated
- QR resolves to correct merchant
- invalid payload rejected
- payment can be initiated from decoded QR data

Original Phase 1 Exit Gate self-assessment: `PASS — SUBJECT TO INDEPENDENT AUDIT`. The formal independent audit set the C05 Exit Gate to `FAIL` for `C05-A01`; the first independent re-audit resolved C05-A01 but found C05-A02, and the second resolved C05-A02 but found C05-A03. The final independent re-audit resolved C05-A01, C05-A02, and C05-A03, found `NONE` remaining, and returned `PASS`. C05 Exit Gate: `PASS`. READY_FOR_HUMAN_DELIVERY_APPROVAL: `YES`. The subsequent controlled delivery record records human approval and completion.

---

# 9. C06 — Minimal Demo UI

## Status

`COMPLETE`

## Authorization and provenance

The committed baseline at `267ef0644b692e3322cacf93cb282d9b409b1e46` recorded C06 as `NOT_STARTED` and `NOT_GRANTED`. A substantial uncommitted C06 candidate implementation existed before later explicit human authorization. The authorization adopted that candidate for formal inspection and verification only; it did not retroactively authorize the earlier work. The subsequent independent audits, remediation, human delivery approval, and controlled delivery closure below established C06 completion.

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

Minimal TypeScript web UI calling the existing FastAPI boundary. TypeScript is required for C06; React is optional and not selected by default. The smallest frontend structure that satisfies the demo should be used.

The UI remains a presentation/initiation layer and must not own payment correctness, balance rules, merchant validation, idempotency, payment fingerprinting, persistence, ledger execution, rollback, or blockchain semantics.

## Why React is not the default

React is not required. It may be considered only if C06 implementation evidence shows that a smaller TypeScript structure cannot support the bounded demo requirements and explicit human approval is recorded.

## C06 Contract Lock — Planned Only

This contract was locked before implementation. It remains the canonical design contract for the previously created candidate now under authorized verification. Executed evidence is recorded only after the corresponding verification command completes.

### Frontend and demo fixture

- Use plain TypeScript, HTML, and CSS compiled with `tsc`.
- Serve compiled assets and API routes same-origin from FastAPI; no separate frontend runtime server or primary-demo CORS requirement.
- Use no framework by default. React, Vite, state-management libraries, and UI libraries are not selected.
- Present only fixture identities `C001` and `M001`; they are not a customer or merchant directory.
- Begin the prepared local demo with `C001 = 100000` öre and `M001 = 0` öre; submit `10000` öre and show `SUCCESS`, `90000` öre, and `10000` öre.

### SEK-to-öre transport

The presentation input accepts only a non-negative decimal string matching:

```text
^(0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$
```

`.` is the sole decimal separator. No whitespace, sign, comma, grouping separator, scientific notation, or more than two fractional digits is accepted. Normalize no fraction to `00`, one fractional digit to two digits, concatenate the decimal text into öre, and convert only that integer representation for the existing integer `amount` API field. Do not use binary floating-point multiplication. Reject malformed presentation input and values outside JavaScript's safe-integer range for usability only; the FastAPI/C04 path remains authoritative for amount validity and all business rules.

```text
100    → 10000 öre
100.0  → 10000 öre
100.00 → 10000 öre
```

### Request identifiers

The current `POST /payments` contract requires distinct `payment_id` and `idempotency_key` values. For one new user payment intent, the UI may generate opaque values with `crypto.randomUUID()`. It must not compute the canonical payment fingerprint, determine a replay result, or decide an idempotency conflict. It must not automatically retry an ambiguous request; any later retry control must reuse the original payload and identifiers so the C04 backend determines the outcome.

### Planned C06 FastAPI adapters

The detailed route contract is canonical in `ARCHITECTURE_AND_DECISIONS.md` D10. C06 plans only these additions:

| Capability | Planned route / representation | Existing behavior reused | Boundary |
|---|---|---|---|
| Balance read | `GET /accounts/{owner_id}/balance` → `owner_id`, `currency`, `balance_ore` | `PaymentService` delegation to `LedgerInterface.get_balance()` | no PostgreSQL detail in API/UI |
| History read | `GET /transactions` → deterministic list of transaction ID, payment ID, ledger type, status, timestamp | `PaymentService` delegation to `LedgerInterface.list_transactions()` | no filtering, pagination, analytics, or second model |
| Merchant QR | `GET /merchants/{merchant_id}/qr` → `image/png` | existing C05 QR generator | UI displays only; no TypeScript QR generator/parser |
| Static UI | `GET /` plus static assets | FastAPI static serving | same-origin API/UI |
| Demo preparation | explicit local-only bootstrap, not HTTP | schema initialization and deterministic fixture pattern | no browser reset endpoint |

The QR remains the C05 merchant-only URI `upi-demo://pay?merchant_id=M001`; amount stays outside the QR. Existing C05/zxing-cpp capabilities must be proved before adding an image encoder dependency.

### Ledger selector and latency

Conventional is visible, selected, and functional. Blockchain is visible but disabled/unavailable and clearly labeled C07 / not yet implemented. C06 neither sends a ledger selector to `POST /payments` nor simulates blockchain results, receipts, balances, contracts, or web3.py behavior.

The UI may show `Local API request time` or `UI-observed request duration`. It must not call this ledger latency, benchmark latency, blockchain confirmation time, or production latency. C08 owns authoritative ledger-only benchmark measurements.

### Planned acceptance contract

1. A real compiled TypeScript UI exists.
2. The UI is served through the FastAPI application.
3. The C001/M001 fixture context is displayed.
4. A real C05 merchant QR is displayed.
5. QR semantics remain owned by C05.
6. User-entered SEK is deterministically transported as integer öre.
7. Payment is submitted through the existing `POST /payments` boundary.
8. Opaque UI-generated identifiers remain distinct; C04 owns fingerprints, replay, idempotency conflicts, and validation.
9. Payment status and transaction identity are displayed from the existing payment response.
10. Updated C001/M001 balances are read from backend adapters.
11. Transaction history is displayed from backend read behavior.
12. UI-observed request duration is explicitly distinguished from C08 benchmark metrics.
13. Conventional is functional.
14. Blockchain is visible only as unavailable/disabled until C07.
15. No frontend payment-correctness logic is authoritative.
16. C04 safety semantics remain unchanged.
17. C05 QR semantics remain unchanged.
18. C07 blockchain implementation remains absent.

### Planned critical invariants and evidence

| Invariant | Planned verification evidence |
|---|---|
| Frontend cannot bypass C04 validation or cause a double debit | Existing `POST /payments` API integration plus C04 regression evidence |
| UI does not compute canonical fingerprints or own replay/conflict semantics | TypeScript source/import review and repeated-request API proof |
| QR stays merchant-only and C05-owned | QR route response decoded/validated through existing C05 test capability; TypeScript source review |
| Transported amount is deterministic integer öre | Focused TypeScript conversion checks and API request evidence for `100`, `100.0`, and `100.00` |
| Displayed balances/history originate from backend state | Balance/history API integration before and after successful payment |
| Blockchain cannot execute before C07 | UI behavior/source review; no blockchain adapter, contract, web3.py, or receipt path |
| UI timing is not benchmark timing | UI label/source review; C08 methodology unchanged |
| No wallet, private key, or blockchain credential enters the browser | Source/dependency review |

### Planned test strategy

Required planned evidence:

1. TypeScript compilation/type-check and production asset preparation pass.
2. API integration tests cover balance read, history read, QR delivery, static UI serving, and the unchanged `POST /payments` path.
3. C04 and C05 regression suites pass.
4. One deterministic browser/demo smoke proves C001 at 1000 SEK, M001 and a real QR visible, 100 SEK submission, `SUCCESS`, 900/100 SEK balances, and visible transaction history.

React/Vitest/Jest and a large browser-testing framework are not required by default. A deterministic browser/demo smoke plus API/integration evidence is sufficient for this bounded interview Card unless actual implementation evidence demonstrates a real gap.

### Explicitly out of C06

- real camera scanning, NFC, React unless later justified and explicitly approved, Next.js/Vue/Svelte/Angular, frontend state-management framework, and design system;
- authentication, customer directory, merchant directory, wallet, private keys, blockchain execution, smart contracts, web3.py integration, benchmark implementation, production deployment, public blockchain, real bank integration, and real money.

## Actual implementation

Pre-existing candidate implementation adopted for authorized verification: plain TypeScript source compiled to FastAPI-served static assets; C001/M001 fixture UI; C04 `POST /payments` reuse; thin balance, history, QR-PNG, and static-serving adapters; local-only bootstrap; and C06-focused tests. This implementation was present before authorization and was verified without feature expansion.

## Problems encountered

No required verification failure or implementation defect was observed in this phase. Non-blocking package-metadata observation: the existing untracked `src/upi_payment_experiment.egg-info/SOURCES.txt` omits `static/app.js` and `static/money.js`, while `pyproject.toml` explicitly configures `static/*` as package data. No package artifact was built in this phase, so fresh-package inclusion was not executed; the configured glob covers all four static files.

## Test evidence

### Authorized recovery and verification results — 2026-09-21

The following results concern the pre-existing candidate adopted after explicit human authorization; they do not imply retroactive authorization, independent-audit approval, Exit Gate PASS, completion, or delivery.

- TypeScript typecheck: `PASS` — `npm run typecheck` completed with no TypeScript diagnostics.
- TypeScript build: `PASS` — `npm run build` completed. SHA-256 values for generated `static/app.js` and `static/money.js` were unchanged before and after the build, confirming the candidate outputs correspond to the current TypeScript source.
- Frontend tests: `PASS` — `npm run test:frontend`: `4 passed`, `0 failed`, `0 skipped`, `0 todo`; the command rebuilds before Node's native test runner.
- PostgreSQL prerequisite: `PASS` — the local Compose `postgres` service was healthy on `127.0.0.1:55432`.
- C06 focused suite: `PASS` — `.venv/bin/python -m pytest tests/test_c06_minimal_demo_ui.py -q`: `6 collected`, `6 passed` in `0.53s`; `0 failed`, `0 skipped`, `0 xfailed`, and no warning output.
- C05 regression: `PASS` — `.venv/bin/python -m pytest tests/test_c05_qr_payment_initiation.py -q`: `48 collected`, `48 passed` in `0.25s`; `0 failed`, `0 skipped`, `0 xfailed`, and no warning output.
- C04 regression: `PASS` — `.venv/bin/python -m pytest tests/test_c04_payment_safety.py -q`: `19 collected`, `19 passed` in `0.69s`; `0 failed`, `0 skipped`, `0 xfailed`, and no warning output.
- C03 regression: `PASS` — `.venv/bin/python -m pytest tests/test_c03_conventional_ledger.py -q`: `3 collected`, `3 passed` in `0.15s`; `0 failed`, `0 skipped`, `0 xfailed`, and no warning output.
- Full suite: `PASS` — `.venv/bin/python -m pytest -q`: `95 collected`, `95 passed` in `1.06s`; `0 failed`, `0 skipped`, `0 xfailed`, and no warning output. A subsequent collect-only command confirmed `95 tests collected`.
- Static/package checks: `PASS` — `.venv/bin/python -m compileall -q src tests`, `.venv/bin/python -m pip check`, and `git diff --check` all exited `0`. `pip check` reported `No broken requirements found` and emitted a non-failing warning that its user cache was not writable.
- Bootstrap: `PASS` — approved local `upi_payment_test` reset produced `C001 = 100000` öre, `M001 = 0` öre, and zero payment, transaction, and idempotency rows. The focused suite also proved rejection of a remote host and a non-demo database name.
- API/runtime smoke: `PASS` — a temporary local Uvicorn process served `GET /`, both balance routes, empty `GET /transactions`, and `GET /merchants/M001/qr` as `image/png` (416 bytes). A `POST /payments` for `10000` öre returned `SUCCESS`; identical replay returned the same transaction; balances were `90000` / `10000` öre and history contained exactly one `ConventionalLedger` transaction.
- Browser smoke: `PASS` — an existing browser mechanism opened the local FastAPI UI after bootstrap and visibly confirmed C001 at `1000.00 SEK`, M001 at `0.00 SEK`, merchant QR, disabled `Blockchain — available in C07`, `100.00` SEK input, UI-submitted `SUCCESS`, transaction ID, `Local API request time`, `900.00` / `100.00` SEK balances, and one ConventionalLedger history row.
- Protected-card review: `PASS` — C02 `UNCHANGED`; C03/C04/C05 `TOUCHED BUT SEMANTICS PRESERVED`. C06 adds read/presentation adapters and consumes C05 QR generation, while payment fingerprinting, idempotency/replay/conflict behavior, atomic ledger transfer, C05 payload/parser semantics, and existing C04 `POST /payments` behavior remain unchanged. The focused and regression results above support this conclusion.
- Acceptance-contract coverage: all 18 planned contract items have implementation and executed verification evidence. Conventional is functional; Blockchain remains disabled/unimplemented C07 work; the UI contains no canonical-fingerprint, replay/conflict-decision, ledger-correctness, web3, wallet, or private-key logic.

Phase 1 Verification: `PASS`.

READY_FOR_INDEPENDENT_AUDIT: `YES`.

## Independent Audit Failure and Bounded Remediation — 2026-09-21

The independent C06 audit returned `FAIL`. It found two confirmed issues; the original audit result remains part of the C06 record and is not superseded by the remediation evidence below.

### C06-A01 — CRITICAL — RESOLVED

- Root cause: `_require_local_demo_target()` accepted a permitted `host` without validating the separately parsed libpq `hostaddr`. A local-looking host could therefore mask a remote numeric `hostaddr` before the explicit bootstrap performed destructive truncation.
- Remediation: added an explicit approved-loopback `hostaddr` allowlist (`127.0.0.1`, `::1`). Any supplied non-loopback `hostaddr` is rejected while the existing permitted host and `upi_payment_test` database checks remain required. The guard does not use DNS resolution.
- Regression proof: focused C06 guard tests directly exercised the guard without opening remote connections. They reject `host=localhost hostaddr=203.0.113.10`, `hostaddr=203.0.113.10`, an ordinary remote hostname, and a non-demo database; they accept existing `host=localhost`, loopback `hostaddr=127.0.0.1`, and loopback `hostaddr=::1` forms.

### C06-A02 — MAJOR — RESOLVED

- Root cause: the successful `POST /payments` response and the secondary balance/history refresh shared one error boundary. A refresh failure could replace a confirmed successful payment presentation with an error.
- Remediation: the payment result is now rendered as authoritative immediately after the successful response. Balance/history refresh runs in a nested secondary error boundary; a refresh failure preserves `SUCCESS`, the transaction ID, and a clear warning: `Payment succeeded, but balance/history refresh failed. Do not retry the payment.` No payment retry or replacement request is generated.
- Regression proof: dependency-free native Node UI tests execute the compiled UI with a controlled DOM/fetch runtime. They prove: (1) successful payment plus successful refresh retains `SUCCESS` and updates balances/history; (2) successful payment plus refresh failure retains `SUCCESS` and transaction ID, shows the warning, and sends exactly one payment POST; and (3) a failed payment POST remains an error presentation.

### C06-A03 — CRITICAL — RESOLVED

The subsequent independent re-audit returned `FAIL` after confirming C06-A01/A02. It found that `service=<name> dbname=upi_payment_test` could pass the prior parser-based guard while libpq resolved the service profile later to an unvalidated target.

- Safety invariant: the bootstrap must never permit an explicit, implicit, or service-resolved connection target to bypass the approved local `upi_payment_test` policy.
- Remediation: non-empty explicit `service` input is rejected. The bootstrap derives one explicit approved `host` from the validated `host`, validated loopback `hostaddr`, or the approved `localhost` fallback; it removes input `service` and `hostaddr` before constructing the final connection string. During the destructive bootstrap operation, `PGHOST`, `PGHOSTADDR`, `PGSERVICE`, and `PGSERVICEFILE` are temporarily removed and restored afterward, preventing libpq environment/service defaults from changing the explicit target. No DNS resolution is used as a security decision.
- Service regression proof: direct guard tests reject both `service=myservice dbname=upi_payment_test` and the same input with `host=localhost`. A mocked bootstrap test sets remote-looking `PGHOST`, `PGHOSTADDR`, `PGSERVICE`, and `PGSERVICEFILE`, then proves all three downstream bootstrap connections receive only `dbname=upi_payment_test` and explicit `host=localhost`, with no `service` or `hostaddr` parameter. The test also proves the environment is restored afterward. A separate temporary local-only runtime probe configured an unusable service profile (`localhost:1`) and still completed bootstrap through its explicitly supplied `127.0.0.1:55432` target; no remote connection was attempted.
- Host/hostaddr regression proof: remote `hostaddr`, host-plus-remote-`hostaddr`, remote hostname, and non-demo database are rejected; `localhost`, `127.0.0.1`, loopback `hostaddr` values, and existing Docker `host=postgres` remain accepted.

### Remediation verification results

- TypeScript typecheck: `PASS` — `npm run typecheck`.
- TypeScript build: `PASS` — `npm run build`; generated `static/app.js` changed only through the TypeScript build for C06-A02.
- Frontend tests: `PASS` — `npm run test:frontend`: `7 passed`, `0 failed`, `0 skipped`, `0 todo` in `44.101208ms`.
- C06 focused suite: `PASS` — `.venv/bin/python -m pytest tests/test_c06_minimal_demo_ui.py -q`: `17 passed` in `0.83s`, including A01/A03 target-selection and environment-fallback regressions.
- C05 regression: `PASS` — `48 passed` in `0.28s`.
- C04 regression: `PASS` — `19 passed` in `0.69s`.
- C03 regression: `PASS` — `3 passed` in `0.16s`.
- Full pytest suite: `PASS` — `106 passed` in `1.42s`.
- Static validation: `PASS` — `.venv/bin/python -m compileall -q src tests`, `.venv/bin/python -m pip check` (`No broken requirements found`), and `git diff --check` all exited successfully.
- Protected-card review: `PASS` — C02 domain, C03 ledger, C04 fingerprint/idempotency/replay/conflict/atomic transfer, and C05 QR payload/parser/generator semantics were not changed by this bounded remediation.

## Final Independent Re-Audit Record

Final independent re-audit: `PASS`.

- C06-A01: `RESOLVED`
- C06-A02: `RESOLVED`
- C06-A03: `RESOLVED`
- New findings: `NONE`
- Open findings: `NONE`
- Bootstrap safety invariant: `PASS`
- Frontend tests: `7 passed`
- C06 focused suite: `17 passed`
- C05 regression: `48 passed`
- C04 regression: `19 passed`
- C03 regression: `3 passed`
- Full suite: `106 passed`
- TypeScript typecheck/build: `PASS`
- Browser smoke: `PASS`
- C02/C03/C04/C05 protection: `PASS`
- C06 Exit Gate: `PASS`
- READY_FOR_HUMAN_DELIVERY_APPROVAL: `YES`

C06 was `IN_PROGRESS` pending explicit human delivery approval and controlled Git delivery at the time of this historical re-audit record.

## Exit Gate

C06 passes when:

- the minimal UI shell is complete
- the conventional payment flow works end-to-end through the UI
- the UI structure supports multiple ledger implementations
- blockchain execution is not required until C07
- the locked C06 acceptance contract has passing executed evidence without changing C04/C05 semantics

C07 owns actual `BlockchainLedger` integration. C09 remains interview packaging and presentation only.

C06 Exit Gate: `PASS`.

READY_FOR_HUMAN_DELIVERY_APPROVAL: `YES`.

## Controlled Delivery Closure — 2026-09-21

- Status: `COMPLETE`
- Final Independent Re-Audit: `PASS`
- C06-A01/A02/A03: `RESOLVED`
- Findings: `NONE`
- Exit Gate: `PASS`
- Human Delivery Approval: `GRANTED`
- Controlled Delivery: `COMPLETE`
- Branch: `main`
- Final validation: frontend `7 passed`; C06 `17 passed`; C05 `48 passed`; C04 `19 passed`; C03 `3 passed`; full pytest `106 passed`; TypeScript typecheck/build `PASS`; browser smoke `PASS`; compileall, pip check, and diff check `PASS`.
- C07: `NOT_STARTED / NOT_AUTHORIZED`
- The immutable delivery SHA is reported from Git after the controlled commit; no SHA is embedded in this pre-commit evidence record.

---

# 10. C07 — Blockchain Ledger

## Status

`IN_PROGRESS`

Authorization: `GRANTED FOR C07 PHASE 1 ONLY`.

Decision-lock delivery and final independent re-preflight: `PASS`. Authorized Phase 1 implementation, deterministic verification, and self-audit completed. The independent audit history below records an initial `FAIL` on C07-A01 through C07-A05, a first bounded remediation, a re-audit `FAIL` that reopened C07-A01/A03 and found C07-A06, a second bounded remediation, and manually discovered C07-A07 (test-database-target safety), C07-A08 (UI ledger-selection race), and C07-A09 (C06 test-database-target safety) findings with their remediations. The final independent C07 re-audit recorded at the end of this section confirms `C07-A01` through `C07-A09`: `CLOSED`, new findings `NONE`, and C07 Exit Gate `PASS`. C07 remains `IN_PROGRESS`: human delivery approval is `NOT_GRANTED`, Git delivery is `NOT_PERFORMED`, and C08 remains `NOT_STARTED / NOT_GRANTED`.

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

## Preflight Remediation and Architecture Decision Lock — 2026-09-21

The prior read-only C07 preflight was `BLOCKED`. This documentation-only remediation locks the previously unresolved architecture decisions; it does not authorize implementation, create a contract, install tooling, or change C07 status.

### Shared selection boundary

Ledger selection belongs at the FastAPI transport/composition boundary, above `PaymentService`:

```text
FastAPI → ledger/service registry → selected PaymentService → selected LedgerInterface
```

The planned registry contains `conventional` and `blockchain` services. C07 selection is `ledger=conventional|blockchain`; omitted selection preserves existing conventional behavior. The selector may apply to payment and ledger-dependent demo reads, while merchant QR identity remains ledger-independent. `Payment`, the canonical payment payload/fingerprint, and the five-method `LedgerInterface` remain unchanged and ledger-neutral.

### Two-layer idempotency and operation recovery

`PaymentLedger` is authoritative for simulated balances, known participants, payment execution, transfer atomicity, processed `payment_id` protection, and payment events. A small durable PostgreSQL blockchain operation journal is authoritative for request/execution coordination: idempotency key, request fingerprint, payment ID, transaction hash, sender identity/address, nonce where required, lifecycle/status, and sufficient signed-transaction linkage for safe recovery.

The journal is not a second financial ledger and is never authoritative for blockchain balances. It enforces the existing C04 outcomes: same key and canonical request returns or reconciles the original logical payment; same key with a different fingerprint raises `IdempotencyConflictError`; conflicting reuse of a payment ID raises `PaymentConflictError`; no second logical transfer is allowed.

PostgreSQL and Ethereum/Anvil cannot participate in one shared ACID transaction. C07 therefore uses durable operation state, deterministic transaction identity, reconciliation, and exact-transaction recovery rather than claiming cross-system atomicity.

### State machine and lost-response handling

The backend constructs and signs the exact payer transaction locally before broadcast, derives its transaction hash, and records a prepared operation durably. The required semantic lifecycle is `PREPARED`, `SUBMITTED`, `SUCCESS`, `FAILED`, and `UNKNOWN`.

Successful receipt resolves to `SUCCESS`; a receipt showing EVM failure/revert resolves to `FAILED`. Ambiguous submission or receipt state resolves to ledger-neutral `PENDING` or `UNKNOWN` while retaining the transaction hash. Retry first inspects the journal, transaction hash, Ethereum transaction/receipt state, and contract processed-payment state. It must never build a new transaction for an unresolved logical payment; controlled recovery may rebroadcast only the exact persisted signed raw transaction with the same hash.

### Signing, account authority, and fixture administration

Application identities map deterministically one-to-one to controlled Anvil test accounts. The backend signs a customer payment with the payer's deterministic Anvil test key. The contract must require `msg.sender` authorization for the payer identity whose balance is debited; arbitrary addresses cannot debit another participant. Keys are backend-only, test-only, excluded from Payment/domain/UI/Git, and are not production key management.

One owner performs account registration, initial balance seeding, and other strictly administrative fixture operations. OpenZeppelin `Ownable` is the preferred minimal baseline. Runtime payments do not require the owner to move customer funds; fresh deterministic Anvil state or redeployment is preferred for reset. Complex access-control, multisig, DAO, wallet, token, DeFi, public-chain, bridge, staking, and governance features remain excluded.

### Planned acceptance, invariants, and evidence

The minimal contract must provide known-account registration, deterministic identity/address authorization, integer-öre balances, balance reads, payment execution, processed-payment reads/protection, and payment events. It rejects unknown payer/merchant, zero payment, insufficient funds, unauthorized payer signer, and processed payment replay. Negative values remain rejected by the existing application/domain boundary and are impossible at the Solidity `uint` boundary. Reverts must leave balances and processed state unchanged.

Critical C07 invariants to verify during authorized work are: value conservation during normal payment execution; no balance change on revert; no second transfer for processed payment ID; no unauthorized debit; exact payer/merchant balance deltas on success; and reconciliation that never creates a second logical transfer. Required evidence includes Foundry/Forge Solidity unit tests, fuzz/property or invariant tests where justified, deterministic Anvil tests, and Python/web3.py adapter integration tests. No such tests have been implemented or executed by this remediation.

The blockchain transaction hash is the canonical blockchain transaction identifier in ledger-neutral result/history representations. Raw Web3 objects remain inside `BlockchainLedger`. Raw factual execution data—hash, receipt status, gas used, submission timestamp, and confirmation timestamp—may be retained for later C08 measurement only; C07 does not benchmark, aggregate, or compare it.

### C07-DL01 — Cross-Ledger Identity / Idempotency Scope

Status: `RESOLVED`.

`ConventionalLedger` and `BlockchainLedger` are alternative, independently reset experimental contexts, not two simultaneous settlement rails. Planned C07 identity and idempotency namespaces are `(ledger_type, payment_id)` and `(ledger_type, idempotency_key)`, where `ledger_type` is `conventional` or `blockchain`. Selection remains outside `Payment`, the canonical request payload, the fingerprint, and `LedgerInterface`; the delivered C04 conventional implementation remains unchanged. The previous independent re-preflight `BLOCKED` result is historical. The final independent C07 re-preflight confirmed this decision as resolved. C07 remains `NOT_STARTED` and `NOT_GRANTED`; this decision lock does not authorize implementation.

Within one namespace, same key and canonical request returns or reconciles the original result without a second transfer; same key with a different fingerprint raises `IdempotencyConflictError`; conflicting reuse of `payment_id` raises `PaymentConflictError`; and processed-payment replay cannot transfer twice. Across namespaces, the same raw payment ID or idempotency key is allowed once per context as separate experimental executions. No cross-namespace journal/state may mutate, satisfy, or reconcile the other. This is not a production multi-rail model; a global coordinator would be required for that out-of-scope future case.

For planned C08 work, payer, merchant, amount, currency, workload, ordering, and reset conditions remain equivalent. Execution identifiers are deterministically scoped by ledger type, benchmark run, and payment index; raw identifiers need not match between contexts.

| ID | Requirement / expected result | Executed verification result |
| --- | --- | --- |
| R1 | Same blockchain idempotency key and canonical request returns or reconciles the original result; no second submission. | `PASS AFTER C07-A01 REMEDIATION` — terminal SUCCESS/FAILED replay returns the durable result without a provider query or second broadcast; genuinely unresolved operations retain the original reconciliation path. |
| R2 | Same blockchain idempotency key with a different fingerprint raises `IdempotencyConflictError`. | `PASS` — journal conflict test raises the ledger-neutral exception before broadcast. |
| R3 | Conflicting blockchain `payment_id` reuse raises `PaymentConflictError`. | `PASS` — journal conflict test raises the ledger-neutral exception before broadcast. |
| R4 | A processed blockchain payment ID replay causes no second transfer. | `PASS` — Solidity replay test and real-Anvil replay verify one exact debit/credit. |
| R5 | The same raw payment ID in distinct ledger namespaces is allowed as separate experimental executions. | `PASS` — cross-ledger integration executes the same raw payment ID once in each isolated ledger. |
| R6 | The same raw idempotency key in distinct ledger namespaces is allowed as separate experimental executions. | `PASS` — cross-ledger integration records independent conventional and blockchain bindings. |
| R7 | C08 uses the same logical workload with deterministic ledger/run-scoped identifiers. | `PASS (STRUCTURAL C07 SCOPE)` — namespace schema and tests preserve ledger-scoped identity; no C08 runner or measurement was implemented. |
| R8 | An ambiguous blockchain response reconciles the original operation and does not create a new blockchain transaction. | `PASS AFTER C07-A01/A03 REMEDIATION` — real submission plus injected receipt loss retains the hash and reconciles once; malformed/ambiguous receipt data becomes UNKNOWN without raw exceptions or false FAILED classification. |
| R9 | Conventional behavior remains the delivered C04 behavior. | `PASS` — all 19 C04 tests and the browser conventional path pass unchanged. |
| R10 | One ledger namespace's journal or state cannot mutate or satisfy the other namespace. | `PASS AFTER C07-A02 REMEDIATION` — cross-ledger integration verifies independent balances/bindings, and the local-only bootstrap reset clears only blockchain journal tables while preserving conventional state. |

## Final Independent C07 Re-Preflight and Decision-Lock Delivery Record

Final independent C07 re-preflight: `PASS`.

- C07-DL01: `RESOLVED`
- C07-RP01: `RESOLVED`
- Previous decision-lock blockers A–M: `RESOLVED`
- New findings: `NONE`
- Open blocking decisions: `NONE`
- LedgerInterface change required: `NO`
- Payment domain change required: `NO`
- C08 boundary: `PASS`
- Canonical consistency: `PASS`
- R1–R10 traceability: planned; all results remain `NOT YET EXECUTED`
- Ready for decision-lock delivery: `YES`
- Human approval for decision-lock documentation delivery: `GRANTED`
- C07 Decision-Lock Documentation Delivery: `COMPLETE`

C07 remains `NOT_STARTED`; C07 authorization remains `NOT_GRANTED`; implementation remains `NOT STARTED`. No C07 implementation tests are claimed. Historical blocked preflight and remediation records are preserved above. This documentation delivery does not authorize C07 implementation.

## Actual implementation

Authorized Phase 1 implemented the locked path `UI → FastAPI ledger selection → shared PaymentService → existing LedgerInterface → BlockchainLedger → web3.py → local Anvil → PaymentLedger` without changing `Payment`, `PaymentRequest`, the canonical fingerprint, or the five `LedgerInterface` signatures.

- `PaymentLedger.sol` uses pinned OpenZeppelin `Ownable` for owner-only participant registration and one-time fixture seeding. Ordinary payer-signed transactions enforce known participants, positive integer-öre amount, sufficient funds, authorized sender, processed-payment replay protection, exact debit/credit, atomic revert, and event evidence.
- `BlockchainLedger` maps distinct C001/M001 identities to backend-only test signers, signs locally, persists exact signed raw transactions before broadcast, validates receipt structure/status before terminal classification, preserves durable terminal results during replay, reconstructs payment/history, and contains provider/Web3 objects and errors.
- PostgreSQL stores operational coordination only under `(ledger_type, payment_id)` and `(ledger_type, idempotency_key)`, including fingerprint, hash, sender, nonce, signed raw transaction, lifecycle, timestamps, receipt status, and gas used. Blockchain balances remain contract-authoritative.
- FastAPI and the existing TypeScript UI select `conventional|blockchain` as query metadata; omission defaults to conventional, payment JSON stays ledger-neutral, and QR remains unchanged.
- The explicit fresh-chain bootstrap initializes schema, clears only blockchain operation-journal rows, deploys/registers/seeds a fresh local contract, and never embeds or prints private keys.

## Problems encountered

The first browser smoke against a freshly redeployed local chain retained journal rows from an earlier chain. The journal correctly reserved a nonce above its durable history, but that nonce was not executable on the fresh chain, leaving the UI unresolved. Root cause: the explicit fresh-chain bootstrap initialized schema but did not align operational coordination state with the deliberately replaced chain. The fix adds a scoped reset of only `blockchain_idempotency_records` and `blockchain_operations`; a deterministic integration test proves the reset and proves conventional tables are unchanged. The repeated real browser smoke then passed for both ledgers.

Foundry emitted a non-product warning because its optional signature cache under the user home directory was not writable in the sandbox; compilation and all tests still exited zero. pip similarly disabled its user cache but reported no broken requirements.

## Independent Audit Failure and Bounded Remediation — 2026-09-21

The formal independent spec-based audit returned `FAIL`. It preserved the Phase 1 execution history but invalidated the earlier self-audit conclusion and the portions of R1, provider-error containment, bootstrap safety, and UI-switch evidence that the original tests did not actually prove.

- `C07-A01` (`MAJOR`): replay of a durable `SUCCESS` or `FAILED` entered provider reconciliation, so a provider outage could overwrite the terminal journal state with `UNKNOWN`. The audit's real-Anvil probe observed `SUCCESS → UNKNOWN` while retaining the hash and already-applied balances. Remediation makes terminal journal states immutable replay sources: they return directly without receipt lookup, transaction lookup, or rebroadcast. Focused real-Anvil evidence verifies durable journal/payment/transaction/history `SUCCESS`, the same hash, unchanged `90000/10000` balances, zero replay provider queries, and one broadcast. A definite `FAILED` receipt is likewise durable on replay.
- `C07-A02` (`MAJOR`): the fresh-chain bootstrap accepted unrestricted PostgreSQL DSNs and RPC URLs before executing a destructive journal reset. Remediation reuses the C06 validated local-demo database policy, additionally requires an explicit host, rejects `PGHOST`/`PGHOSTADDR`/`PGSERVICE`/`PGSERVICEFILE` target redirection, accepts only explicit loopback HTTP RPC URLs with a port, verifies the connected client is Anvil, and still truncates only `blockchain_idempotency_records` and `blockchain_operations`. Tests reject remote host, remote `hostaddr`, service indirection, missing/ambiguous host, implicit target environment, remote/non-loopback/malformed RPC, and verify conventional tables remain unchanged.
- `C07-A03` (`MAJOR`): direct `int(receipt[...])` conversion could leak raw exceptions and classified every non-1 value as definite failure. Remediation accepts only a mapping with integer (not boolean) status exactly `0` or `1` and non-negative integer gas. Status `1` becomes `SUCCESS`; status `0` becomes `FAILED`; missing, malformed, wrong-type, unexpected integer, malformed-object, or provider-format failures produce the existing ledger-neutral `UNKNOWN` result while preserving the known transaction hash. Terminal states are checked before receipt interpretation and cannot be corrupted.
- `C07-A04` (`MINOR`): two application identities could resolve to one Ethereum address. Adapter construction and bootstrap deployment now normalize/check participant addresses and reject duplicates before deployment or payment activity. The regression verifies `C001 == M001` fails deterministically and does not advance the Anvil block number.
- `C07-A05` (`MINOR`): switching ledgers could display the previous ledger's result as if it belonged to the new selection. The existing UI now immediately replaces status with `Loading selected ledger…` and clears transaction ID and request timing before refreshing balances/history. The frontend regression performs Conventional payment → Blockchain switch/payment → Conventional switch and verifies both cleanup directions and the newly selected result.

The five findings are `REMEDIATED_PENDING_INDEPENDENT_RE_AUDIT`; this record is remediation evidence, not an independent re-audit. Human delivery approval remains `NOT_GRANTED`, Git delivery remains `NOT_PERFORMED`, and C08 remains `NOT_STARTED / NOT_GRANTED`.

## Tests

Original Phase 1 execution on 2026-09-21 (historical; later found insufficient for C07-A01-A05):

- `forge fmt --check`, `forge build`, `forge test -vv`: `PASS`; 10 Solidity tests, 0 failures, including 256 fuzz runs for exact deltas/value conservation and deterministic revert/no-mutation, authorization, event, replay, balance, and owner-only checks.
- `.venv/bin/pytest -q tests/test_c07_blockchain_ledger.py`: `PASS`; 13 tests using actual local Anvil and PostgreSQL, including canonical 100000/0 → 90000/10000 execution, receipt/event/hash mapping, conflicts, failure mapping, exact-raw recovery, nonce reservation, cross-ledger isolation, API selection, and scoped bootstrap reset.
- Lost-response proof: an actually submitted Anvil transaction has its normal receipt response deliberately suppressed once; retry reconciles the retained original hash, the broadcast counter remains one, and balances move exactly once. A separate controlled pre-broadcast failure proves byte-for-byte/hash-identical rebroadcast.
- C03/C04/C05/C06 regressions: `3/3`, `19/19`, `48/48`, and `17/17` passed.
- `.venv/bin/pytest -q`: `PASS`; 119 tests, 0 failures.
- `npm run typecheck`, `npm run build`, `npm run test:frontend`: `PASS`; 9 frontend tests, 0 failures.
- `.venv/bin/python -m compileall -q src tests`, `.venv/bin/pip check`, and `git diff --check`: `PASS`; no broken requirements or whitespace errors.
- Real local browser smoke after fresh conventional/bootstrap and fresh Anvil deployment: conventional and blockchain each visibly changed `1000.00/0.00 SEK` to `900.00/100.00 SEK` with `SUCCESS`; blockchain displayed its transaction hash/history, QR loaded through FastAPI, and captured browser warning/error logs were empty.

Bounded remediation execution on 2026-09-21:

- `/Users/jo.soroush/.foundry/bin/forge fmt --check && /Users/jo.soroush/.foundry/bin/forge build && /Users/jo.soroush/.foundry/bin/forge test -vv`: `PASS`; 10 Solidity tests, 0 failures, including 256 fuzz runs. The signature-cache warning remained non-failing.
- `.venv/bin/python -m pytest tests/test_c07_blockchain_ledger.py -q`: `PASS`; 39 tests in 19.03s on final closure verification. Added evidence covers terminal SUCCESS/FAILED replay, strict receipt validation, local-only bootstrap target validation, duplicate-address rejection, preservation of conventional and unrelated tables, and the existing real-Anvil/lost-response paths.
- `.venv/bin/python -m pytest -q tests/test_c07_blockchain_ledger.py::test_real_anvil_canonical_payment_and_ledger_interface tests/test_c07_blockchain_ledger.py::test_terminal_success_replay_is_provider_independent_and_immutable tests/test_c07_blockchain_ledger.py::test_lost_receipt_reconciles_original_hash_without_new_transaction`: `PASS`; 3 tests in 3.19s, separating canonical success, terminal-outage replay, and genuinely unresolved reconciliation.
- C03/C04/C05/C06 focused regressions: `PASS`; `3/3` in 0.20s, `19/19` in 0.74s, `48/48` in 0.27s, and `17/17` in 0.73s.
- `.venv/bin/python -m pytest -q`: `PASS`; 145 tests in 20.46s on final closure verification, 0 failures.
- `npm run typecheck` and `npm run test:frontend` (which runs the build before tests): `PASS`; TypeScript typecheck/build succeeded and 10 frontend tests passed, including two-way stale-result cleanup.
- `.venv/bin/python -m compileall -q src tests`, `.venv/bin/pip check`, and `git diff --check`: `PASS`; no broken requirements, compile errors, or whitespace errors.
- Fresh explicit local bootstrap and browser smoke: `PASS`; conventional and blockchain each visibly changed `1000.00/0.00 SEK` to `900.00/100.00 SEK` with `SUCCESS`; blockchain displayed transaction hash `0x603b…124d`. The first switch visibly showed `Loading selected ledger…`, transaction `—`, and timing `—`; the reverse switch showed conventional `Ready`, transaction `—`, timing `—`, and the correct ConventionalLedger history. Browser warning/error logs were empty.
- Security inspection: `PASS`; no test key, private-key field, Web3 client, Anvil RPC URL, or direct RPC port occurs in frontend or served static assets. Signer selection remains the fixed backend C001/M001 mapping; SQL executed by the bootstrap uses fixed table names and no interpolated target/input.
- Final remediation closure verification on 2026-09-22: `PASS`. Forge formatting/build/tests remained `10/10` with 256 fuzz runs; C03/C04/C05/C06 remained `3/3`, `19/19`, `48/48`, and `17/17`; frontend typecheck/build/tests remained `10/10`; compileall, pip check, and `git diff --check` passed. This closure performed no source or test edits and did not perform an independent re-audit or Git delivery.

## Evidence artifacts

- Contract and deterministic Solidity evidence: `contracts/PaymentLedger.sol`, `contracts/test/PaymentLedger.t.sol`, `foundry.toml`.
- Adapter/recovery evidence: `src/upi_payment_experiment/blockchain_ledger.py`, `src/upi_payment_experiment/blockchain_journal.py`, `src/upi_payment_experiment/blockchain_bootstrap.py`, and the journal schema in `postgres_schema.sql`.
- Transport/UI evidence: `api.py`, `demo_app.py`, `frontend/app.ts`, compiled `static/app.js`, `static/index.html`, and frontend tests.
- Real-Anvil/API/fault-injection/namespace evidence: `tests/test_c07_blockchain_ledger.py`.

Known limitations: Anvil is a single-process local development chain, test keys are backend-only ephemeral fixtures, the journal and chain do not share ACID atomicity, unresolved provider outcomes require later retry/reconciliation, and the fresh-chain bootstrap intentionally clears operational journal state only when deliberately invoked. These results are not evidence for public Ethereum latency, cost, consensus finality, custody, production reliability, or C08 benchmark conclusions.

Original Phase 1 self-audit: `PASS`, superseded by the formal independent audit `FAIL` on C07-A01-A05. The first bounded-remediation self-check was later superseded by the following independent re-audit: its terminal-replay checks covered only an already-observed terminal snapshot and did not prove that a stale nonterminal resolver could not overwrite a concurrently persisted terminal row. It also did not validate runtime `BlockchainLedger.from_environment()` against non-local RPC targets. Independent re-audit is still required after the second remediation record below.

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

The formal independent audit set the C07 gate to `FAIL` for C07-A01-A05. Bounded remediation verification now self-assesses `PASS — READY_FOR_INDEPENDENT_RE_AUDIT`, but does not independently close the gate. C07 remains `IN_PROGRESS`; human delivery approval is `NOT_GRANTED`; Git delivery is `NOT_PERFORMED`; C08 remains `NOT_STARTED / NOT_GRANTED`.

---

## Independent Re-Audit Failure and Second Bounded Remediation — 2026-09-22

The first post-remediation independent re-audit returned `FAIL`. It confirmed `C07-A02`, `C07-A04`, and `C07-A05` as closed, but kept `C07-A01` and `C07-A03` open and identified `C07-A06`.

- `C07-A01` (`MAJOR`, reopened): `BlockchainOperationJournal.update_status()` could unconditionally write `UNKNOWN` from a stale `PREPARED` operation object after another resolver had already persisted `SUCCESS` or `FAILED`. The object-level terminal check in `BlockchainLedger` was insufficient because it did not protect the PostgreSQL row.
- `C07-A03` (`MAJOR`, reopened): strict receipt parsing correctly controlled malformed evidence for a genuinely nonterminal operation, but its `UNKNOWN` path used the same unconditional journal write and could therefore corrupt a concurrently terminal row.
- `C07-A06` (`MAJOR`, new): `BlockchainLedger.from_environment()` passed the configured RPC URL directly to `HTTPProvider`; a public URL could construct the runtime adapter without local-loopback, Anvil-client, or chain-ID validation.

### Second remediation

- Journal status updates now use a PostgreSQL conditional update that excludes durable `SUCCESS` and `FAILED`. If the update loses a race, the journal returns the current authoritative operation instead of overwriting it. This protects every existing `SUBMITTED`, `UNKNOWN`, `SUCCESS`, and `FAILED` write path because all status changes use `update_status()`.
- Direct real-Anvil/PostgreSQL regressions retain a stale `PREPARED` snapshot, independently persist `SUCCESS` or `FAILED`, then exercise a provider-outage or malformed-receipt path. They prove status, hash, receipt facts, payment, transaction, history, and balances remain authoritative, with no stale-handler broadcast.
- Runtime composition now reuses explicit loopback HTTP URL validation, establishes a connection, requires Anvil client metadata, and requires local chain ID `31337` before constructing `BlockchainLedger`. Public/remote/non-loopback/malformed/userinfo URLs, a reachable non-Anvil endpoint, and a reachable wrong-chain endpoint are rejected before signing or payment activity. A real local-Anvil environment composition test executes the canonical payment successfully.

### Second-remediation verification

- `forge fmt --check`, `forge build`, and `forge test`: `PASS`; 10 Solidity tests, including 256 fuzz runs.
- `.venv/bin/python -m pytest tests/test_c07_blockchain_ledger.py -q`: `PASS`; 51 tests in 22.36s. The count increased by 12: stale terminal `SUCCESS`/`FAILED` PostgreSQL race tests, seven unsafe-runtime-URL rejections, reachable non-Anvil/wrong-chain rejection tests, and real local runtime composition/execution.
- C03/C04/C05/C06 focused regressions: `PASS`; `3/3`, `19/19`, `48/48`, and `17/17`.
- `.venv/bin/python -m pytest -q`: `PASS`; 157 tests in 23.01s.
- `compileall`, `pip check`, TypeScript typecheck/build, and frontend tests: `PASS`; frontend `10/10`, including ledger-switch stale-context cleanup.
- Scoped-bootstrap reset, duplicate-address rejection, and frontend ledger-switch regressions remain covered by the passing C07/C06/frontend suites; no source changes were made for A02/A04/A05.

Second remediation self-audit: `PASS — READY_FOR_INDEPENDENT_RE_AUDIT`. This is remediation evidence only. It does not change the independent-audit result, C07 Exit Gate, C07 completion, human delivery approval, Git delivery, or C08 authorization.

---

## Final Independent C07 Re-Audit — 2026-09-22

Final independent re-audit: `PASS`.

- `C07-A01` through `C07-A06`: `CLOSED`.
- Findings: `NONE`.
- C07 Exit Gate: `PASS`.
- C07 remained `IN_PROGRESS` pending human delivery approval and controlled Git delivery.
- Human delivery approval: `NOT_GRANTED`.
- Git delivery: `NOT_PERFORMED`.
- C08: `NOT_STARTED / NOT_GRANTED`.

This independent result is historical evidence. The following manually discovered C07-A07 test-harness safety finding reopens the need for a bounded independent re-audit; it does not erase the original audit failure, either remediation record, or this final re-audit result.

---

## C07-A07 — Test Database Target Safety Remediation — 2026-09-22

### Finding and root cause

Manual post-final-audit review found that `tests/test_c07_blockchain_ledger.py` obtained `UPI_TEST_DATABASE_DSN` directly and assigned it to `TEST_DSN` without a mandatory test-harness target check. That module uses `TEST_DSN` for `ConventionalLedger(...).initialize_schema()`, `psycopg.connect(...)`, `bootstrap_demo(...)`, `BlockchainLedger(...)`, `TRUNCATE`, an isolated `CREATE TABLE`, and the matching `DROP TABLE`. A mistakenly configured remote, service-resolved, socket/default, non-test, or otherwise ambiguous target could therefore have been mutated.

### Bounded remediation

The test module now follows one authoritative boundary at module initialization:

```text
raw UPI_TEST_DATABASE_DSN
→ _validated_c07_test_dsn(raw value)
→ validated TEST_DSN
→ all C07 fixture and test database use
```

The guard reuses the established C06/C07 local-demo safety model while making the C07 test harness stricter: it requires a non-empty `postgresql` URI, an explicit loopback host (`127.0.0.1`, `::1`, or `localhost`), and database `upi_payment_test`; it rejects `hostaddr`, `service`, and every implicit libpq target override (`PGHOST`, `PGHOSTADDR`, `PGSERVICE`, `PGSERVICEFILE`). It returns a parsed validated conninfo only after every check passes. Unsafe input is rejected; it is never rewritten into a safe target.

Because `TEST_DSN` is initialized before fixtures, `BlockchainLedger` construction, schema initialization, connections, or destructive SQL are reachable, the entire module is protected rather than relying on scattered per-test checks. No blockchain, payment, contract, architecture, interface, fingerprint, QR, or C08 behavior changed.

### Direct fail-before-connect evidence

A controlled module-load probe replaced `psycopg.connect` with a recorder and executed the module boundary without running tests. Every rejected case recorded zero connection attempts:

- remote DSN `postgresql://upi@203.0.113.10:55432/upi_payment_test`: `REJECTED BEFORE DATABASE ACTIVITY`;
- local wrong database: `REJECTED BEFORE DATABASE ACTIVITY`;
- `hostaddr` bypass: `REJECTED BEFORE DATABASE ACTIVITY`;
- `service` indirection: `REJECTED BEFORE DATABASE ACTIVITY`;
- `PGHOST`, `PGHOSTADDR`, and `PGSERVICE` redirection: each `REJECTED BEFORE DATABASE ACTIVITY`;
- canonical `postgresql://upi@127.0.0.1:55432/upi_payment_test`: `ACCEPTED WITHOUT DATABASE ACTIVITY`.

The focused regressions also cover remote hostname, remote IP, hostaddr, service, wrong database, missing host, and all four implicit libpq target variables. They prove rejection requires no remote database access.

### Executed verification

- `.venv/bin/python -m pytest tests/test_c07_blockchain_ledger.py -q`: `PASS`; `62 passed` in 22.60s. This is `+11` tests from the 51-test pre-A07 baseline: one canonical-acceptance test, six unsafe-DSN cases, and four implicit-environment cases.
- `.venv/bin/python -m pytest tests/test_c03_conventional_ledger.py -q`: `PASS`; `3 passed`.
- `.venv/bin/python -m pytest tests/test_c04_payment_safety.py -q`: `PASS`; `19 passed`.
- `.venv/bin/python -m pytest tests/test_c05_qr_payment_initiation.py -q`: `PASS`; `48 passed`.
- `.venv/bin/python -m pytest tests/test_c06_minimal_demo_ui.py -q`: `PASS`; `17 passed`.
- `.venv/bin/python -m pytest -q`: `PASS`; `168 passed` in 23.83s, also `+11` from the 157-test pre-A07 baseline.
- `.venv/bin/python -m compileall -q src tests`: `PASS`.
- `.venv/bin/python -m pip check`: `PASS` — no broken requirements (the pre-existing non-writable pip-cache warning was non-failing).
- `npm run typecheck`, `npm run build`, and `npm run test:frontend`: `PASS`; frontend tests `10/10`.
- `/Users/jo.soroush/.foundry/bin/forge fmt --check`, `build`, and `test`: `PASS`; Solidity tests `10/10`, including 256 fuzz runs. The existing non-failing signature-cache warning remained due sandbox permissions.
- `git diff --check`: `PASS`.

### Scope and self-audit

- Every C07 database operation in the module uses the single validated `TEST_DSN`.
- No destructive C07 database operation can execute before module-level validation.
- Remote, wrong-database, hostaddr, service, implicit-environment, and no-host targets fail closed before connection activity.
- `C07-A01` terminal-state immutability, `C07-A02` local-only bootstrap, `C07-A03` receipt classification, `C07-A04` duplicate-address rejection, `C07-A05` UI switch safety, and `C07-A06` local-Anvil runtime composition all remain covered by the passing C07, frontend, and Solidity evidence.
- No secrets were introduced. No payment/blockchain production source changed. No C08 work occurred.

`C07-A07 Remediation: PASS`. This is a bounded remediation self-audit, not the independent A07 re-audit. C07 remains `IN_PROGRESS`; human delivery approval is `NOT_GRANTED`; Git delivery is `NOT_PERFORMED`; C08 remains `NOT_STARTED / NOT_GRANTED`; readiness for the A07 independent re-audit is `YES`.

---

## Independent C07-A07 Re-Audit — 2026-09-22

Independent C07-A07 re-audit: `PASS`.

- C07 module-level `TEST_DSN` validation was confirmed to precede all PostgreSQL connections, schema initialization, ledger construction, bootstrap, and destructive SQL.
- Controlled module-load probes rejected remote hostname/IP, wrong database, hostaddr, service, every implicit libpq target variable, and no-host targets with zero `psycopg.connect` calls.
- The canonical loopback `upi_payment_test` URI was accepted.
- `C07-A07`: `CLOSED`.
- No open A07 technical finding remained after the independent re-audit.

---

## C07-A08/A09 Consolidated Remediation — 2026-09-22

Manual frontend review after the A07 re-audit found `C07-A08`: a payment request could begin on one selected ledger while the UI selection changed before its result and refresh completed, allowing the presentation to combine result context from one ledger with reads from another. Manual C06 test-harness review found `C07-A09`: `tests/test_c06_minimal_demo_ui.py` assigned its raw `UPI_TEST_DATABASE_DSN` to `TEST_DSN` before using it in `ConventionalLedger`, `bootstrap_demo`, and direct `psycopg.connect` calls.

### A08 remediation

Each valid payment intent now captures the selected ledger once. Its `POST /payments` request and every associated balance/history refresh receive that captured ledger explicitly. Both ledger radios are disabled while the payment outcome and refresh are active, and the change handler ignores a forced change event during that interval. Controls are restored only for resolved outcomes where a new payment intent is permitted; `PENDING`/`UNKNOWN` retains the existing no-second-intent lock. The confirmed `SUCCESS` refresh-failure protection is unchanged.

The deterministic frontend regression begins a Conventional payment, holds its fetch unresolved, verifies both controls are disabled, forces a Blockchain change event while the request remains in flight, then resolves the payment. It proves the POST, post-payment balances, and history all use `ledger=conventional`, the displayed transaction/history are Conventional, and controls are restored after the resolved success.

### A09 remediation

The C06 test module now has the same authoritative module-load boundary as the C07 harness: raw `UPI_TEST_DATABASE_DSN` is checked before `TEST_DSN` is assigned. It requires a `postgresql` URI with explicit loopback host and database `upi_payment_test`, rejects `hostaddr`, service indirection, remote targets, no-host targets, and `PGHOST`/`PGHOSTADDR`/`PGSERVICE`/`PGSERVICEFILE`. It then reuses the C06 canonical demo-DSN validator. Every C06 database path continues to use the resulting validated `TEST_DSN`.

Focused C06 regressions cover canonical acceptance; remote hostname/IP; hostaddr; service; wrong database; no host; and all four implicit target variables. Their patched `psycopg.connect` recorder proves rejected inputs make zero connection attempts.

A separate controlled fresh module-load probe independently confirmed remote, wrong-database, hostaddr, service, `PGHOST`, `PGHOSTADDR`, `PGSERVICE`, and `PGSERVICEFILE` cases each rejected with `connect_calls=0`; the canonical local URI loaded with `connect_calls=0`.

### Executed verification

- `npm run typecheck`: `PASS`.
- `npm run test:frontend`: `PASS`; `11/11` frontend tests, up from 10 by the deterministic A08 in-flight race regression.
- `.venv/bin/python -m pytest tests/test_c03_conventional_ledger.py -q`: `PASS`; `3/3`.
- `.venv/bin/python -m pytest tests/test_c04_payment_safety.py -q`: `PASS`; `19/19`.
- `.venv/bin/python -m pytest tests/test_c05_qr_payment_initiation.py -q`: `PASS`; `48/48`.
- `.venv/bin/python -m pytest tests/test_c06_minimal_demo_ui.py -q`: `PASS`; `28/28`, up from 17 by 11 A09 acceptance/rejection and zero-connection tests.
- `.venv/bin/python -m pytest tests/test_c07_blockchain_ledger.py -q`: `PASS`; `62/62`.
- `.venv/bin/python -m pytest -q`: `PASS`; `179/179`, up from 168 by the 11 A09 tests.
- `.venv/bin/python -m compileall -q src tests`: `PASS`.
- `.venv/bin/python -m pip check`: `PASS` — no broken requirements; the existing non-writable cache warning was non-failing.
- `/Users/jo.soroush/.foundry/bin/forge test`: `PASS`; `10/10` Solidity tests, including 256 fuzz runs. The existing sandbox signature-cache warning was non-failing.
- `git diff --check`: `PASS`.

`C07-A08` and `C07-A09` are `REMEDIATED_PENDING_INDEPENDENT_REAUDIT`. This is remediation evidence, not an independent re-audit. C07 remains `IN_PROGRESS`; human delivery approval remains `NOT_GRANTED`; Git delivery remains `NOT_PERFORMED`; C08 remains `NOT_STARTED / NOT_GRANTED`.

---

## Final Independent C07 Re-Audit (Post A08/A09) — 2026-09-22

Final independent C07 re-audit: `PASS`.

- `C07-A01` through `C07-A09`: `CLOSED`.
- New findings: `NONE`.
- C07 Exit Gate: `PASS`.
- Ready for Human Delivery Approval: `YES`.

This re-audit independently re-executed validation rather than relying on the A08/A09 remediation self-assessment above:

- `npm run test:frontend`: `PASS`; `11/11`.
- `npm run typecheck`: `PASS`.
- `.venv/bin/python -m pytest tests/test_c03_conventional_ledger.py -q`: `PASS`; `3/3`.
- `.venv/bin/python -m pytest tests/test_c04_payment_safety.py -q`: `PASS`; `19/19`.
- `.venv/bin/python -m pytest tests/test_c05_qr_payment_initiation.py -q`: `PASS`; `48/48`.
- `.venv/bin/python -m pytest tests/test_c06_minimal_demo_ui.py -q`: `PASS`; `28/28`.
- `.venv/bin/python -m pytest tests/test_c07_blockchain_ledger.py -q`: `PASS`; `62/62`.
- `.venv/bin/python -m pytest -q`: `PASS`; `179/179`.
- `/Users/jo.soroush/.foundry/bin/forge test`: `PASS`; `10/10` Solidity tests, including 256 fuzz runs.
- `.venv/bin/python -m compileall -q src tests`: `PASS`.
- `.venv/bin/python -m pip check`: `PASS` — no broken requirements.
- `git diff --check`: `PASS`.

This independent re-audit made no source, test, or contract changes and performed no Git actions; it is execution-only verification of the already-remediated `C07-A01` through `C07-A09` findings.

C07 remains `IN_PROGRESS` pending human delivery approval and controlled Git delivery. Human delivery approval remains `NOT_GRANTED`. Git delivery remains `NOT_PERFORMED`. C08 remains `NOT_STARTED / NOT_GRANTED`.

---

## Human Delivery Approval — 2026-09-22

- Status: `IN_PROGRESS`
- Final Independent C07 Re-Audit (Post A08/A09): `PASS`
- C07-A01 through C07-A09: `CLOSED`
- Findings: `NONE`
- Exit Gate: `PASS`
- Human Delivery Approval: `GRANTED`
- Git Delivery: `NOT_PERFORMED` — controlled delivery has not yet been committed or pushed at the time of this record
- C08: `NOT_STARTED / NOT_GRANTED`

Approval covers controlled C07 Git delivery only. It does not authorize C08, C09, or any unrelated change. `CLAUDE.md` remains excluded from C07 delivery scope. The immutable delivery SHA is reported from Git after the controlled commit; no SHA is embedded in this pre-commit evidence record.

---

# 11. C08 — Benchmark & Comparative Experiment

## Status

`COMPLETE — IMPLEMENTATION, EXECUTION, SELF-AUDIT, FINAL INDEPENDENT CLOSURE RE-AUDIT, HUMAN APPROVAL, AND CONTROLLED DELIVERY PASS`

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

### Actual implementation and decisions

`src/upi_payment_experiment/benchmark.py` implements one runner for both
ledgers through the existing FastAPI → `PaymentService` → `LedgerInterface`
path. A transparent timing adapter measures only `execute_payment`; because the
existing implementations return after PostgreSQL commit or local-Anvil receipt,
the primary boundary retains each canonical completion definition. The same
request is separately timed around an in-process ASGI request/response for the
secondary API metric.

The deterministic fixture contains `C001`–`C020` at `100000` öre and
`M001`–`M005` at `0` öre. Each benchmark payment is `1000` öre. This constant
amount was selected before measured execution because repeating the 100 SEK
presentation payment 1000 times would exceed the canonical fixture's total
customer balances; 10 SEK preserves the existing positive-integer payment
semantics and makes the prescribed maximum workload feasible without reseeding
inside a run. Both ledgers receive the identical payer, merchant, amount,
currency, ordering, and workload sequence. Payment and idempotency identifiers
are deterministically scoped by ledger, workload, run, and payment index.

Before every measured conventional run, all payment, transaction,
idempotency, blockchain-journal, and account fixture state is cleared and the
exact 25-account dataset is restored. Before every measured blockchain run,
the same PostgreSQL fixture/journal reset occurs and a fresh `PaymentLedger`
contract is deployed, with all 25 participants registered and seeded. Thus the
active on-chain balance and processed-payment state is new as well as the
off-chain journal. All 25 initial balances and empty history are verified
before timing. One three-payment warm-up per ledger/workload is discarded.
Reset, deployment, seed, warm-up, reset verification, final-state checks, and
replay checks are outside the measured interval.

The actual matrix executed sequentially with no reduction:

```text
workloads: 10, 100, 500, 1000
measured runs: 5 per workload per ledger
measured runs total: 40
measured payments: 8050 per ledger; 16100 total
invalid/failed measured runs: 0
payment failures: 0
```

Observed workload aggregates below are computed from raw valid transaction
measurements. Latencies are milliseconds; throughput is payments/second.

| Ledger | Workload | Ledger avg / median / p95 | API avg / median / p95 | Mean run throughput |
|---|---:|---:|---:|---:|
| Conventional | 10 | 7.841 / 5.680 / 16.385 | 8.809 / 6.683 / 18.545 | 126.048 |
| Conventional | 100 | 5.976 / 5.704 / 7.413 | 7.125 / 6.880 / 9.047 | 139.877 |
| Conventional | 500 | 6.095 / 5.846 / 7.659 | 7.401 / 7.214 / 9.197 | 134.406 |
| Conventional | 1000 | 6.399 / 6.034 / 8.056 | 7.630 / 7.348 / 9.531 | 130.429 |
| Blockchain | 10 | 92.436 / 100.255 / 108.451 | 93.591 / 101.355 / 109.874 | 10.228 |
| Blockchain | 100 | 92.656 / 100.234 / 113.104 | 93.954 / 101.389 / 114.668 | 10.178 |
| Blockchain | 500 | 94.683 / 101.987 / 113.146 | 95.969 / 103.186 / 114.727 | 9.957 |
| Blockchain | 1000 | 97.084 / 102.964 / 112.550 | 98.358 / 104.239 / 114.034 | 9.725 |

Blockchain submission/confirmation and successful gas remain separate:

| Workload | Submission avg / median / p95 ms | Confirmation avg / median / p95 ms | Successful gas avg / median / p95 |
|---:|---:|---:|---:|
| 10 | 32.854 / 32.667 / 40.881 | 51.633 / 60.781 / 63.345 | 73559.72 / 73553 / 82115 |
| 100 | 34.519 / 34.181 / 44.561 | 50.650 / 61.165 / 63.637 | 65864.072 / 65015 / 65015 |
| 500 | 35.169 / 35.061 / 42.999 | 51.954 / 61.484 / 63.759 | 65180.331 / 65015 / 65015 |
| 1000 | 34.966 / 35.241 / 41.169 | 54.464 / 61.784 / 63.605 | 65094.745 / 65015 / 65015 |

No measured payment failed or reverted, so failed/reverted gas count is `0`
and its statistics remain inapplicable rather than being mixed with successful
gas. Every measured run passed final-balance, value-conservation,
transaction/history-linkage, and exact-replay/no-second-transfer checks.

Normalized differential comparison: `PASS` for all `20` paired workload/run
contexts, with `0` mismatches. Transaction hashes/IDs, timing, gas, and
receipt/event identity were excluded from equality; payment status, payer and
merchant balance deltas, history linkage, replay outcome and balance stability,
and absence of partial transfer were retained.

### Execution environment

```text
Git baseline: main @ 57bad6527c8bab6907680642a51b20af44c36f06
Host: Darwin 25.6.0 arm64
Python: 3.13.12
PostgreSQL: 16.15 at explicit loopback upi_payment_test target
Anvil: 1.8.3, ephemeral loopback process, chain ID 31337
Node.js: 24.19.0
npm: 11.17.0
```

The runner accepts only the explicit local `upi_payment_test` PostgreSQL target,
rejects libpq redirection, starts its own loopback Anvil process, and verifies
the Anvil client identity and chain ID before use.

### Verification and traceability

- Focused C08: `16 passed`.
- C03–C07 regression selection: `160 passed`.
- Full Python suite: `195 passed`.
- Frontend typecheck: `PASS`.
- Frontend tests: `11 passed`.
- Solidity tests: `10 passed`, including `256` fuzz runs for the value-conservation property.
- Python compileall: `PASS`.
- `pip check`: `PASS` (`No broken requirements found`).
- `git diff --check`: `PASS`.

The focused tests cover deterministic/reproducible sequence generation,
ledger-scoped identifier uniqueness, logical equivalence, exact fixture setup,
safe local target validation with zero connection on rejection, non-loopback RPC
rejection before provider calls, real PostgreSQL reset, real fresh-contract Anvil
reset, reset/timing separation, excluded warm-up, sequential execution, timing
boundaries, evidence schemas and all three writers, invalid-run retention,
separate gas populations, raw mismatch retention, differential mismatch
detection, rejection of equal-invalid-run false positives, replay behavior,
final balances, value conservation, and exclusion
of implementation identity/timing/gas from normalization.

### Independent audit history and final closure

The initial independent audit was `BLOCKED` only because the auditor sandbox
could not execute the required test commands. Its source, architecture,
methodology, evidence-integrity, differential, reset, timing, security, and
documentation inspection found no defect. The block was environmental and did
not identify a C08 implementation or evidence finding.

The required commands were subsequently executed in the real project
environment. The final independent closure re-audit independently reproduced
the missing executions:

- focused C08: `16 passed`;
- full pytest: `195 passed`;
- Solidity: `10 passed`;
- Solidity value-conservation fuzzing: `256 runs`;
- `pip check`: `PASS`;
- the previously established frontend tests, TypeScript typecheck, and Python
  compileall verification remain `PASS`.

Final independent closure re-audit: `PASS`. Findings: `NONE`. C08 Exit Gate:
`PASS`. `READY_FOR_HUMAN_DELIVERY_APPROVAL: YES`. Human Delivery Approval:
`NOT_GRANTED`. Git Delivery: `NOT_PERFORMED`. C08 remains `IN_PROGRESS` until
approved delivery completes. C09 remains `NOT_STARTED`.

Property/invariant verification uses exhaustive uniqueness and deterministic
generation assertions for the maximum 1000-payment workload plus deterministic
normalized-outcome and value-conservation checks. A generated Python property
framework was not added because the fixed canonical sequence is fully
enumerated. Mutation testing is `NOT_APPLICABLE`: no concrete incremental value
was identified beyond the focused boundary, negative, real-service reset, and
differential false-green tests.

### Evidence artifacts

```text
src/upi_payment_experiment/benchmark.py
tests/test_c08_benchmark.py
evidence/benchmarks/conventional/benchmark_results.json
evidence/benchmarks/conventional/benchmark_results.csv
evidence/benchmarks/conventional/per_transaction_results.jsonl
evidence/benchmarks/blockchain/benchmark_results.json
evidence/benchmarks/blockchain/benchmark_results.csv
evidence/benchmarks/blockchain/per_transaction_results.jsonl
evidence/benchmarks/differential_results.json
evidence/benchmarks/qualitative_comparison.md
```

## Problems encountered

- The canonical 100 SEK presentation payment cannot be repeated 1000 times
  against 20 customers holding 1000 SEK each without exhaustion. A fixed 10 SEK
  benchmark payment was selected symmetrically before measurement; all existing
  payment rules remain unchanged.
- `forge` was not on the interactive shell `PATH`. The repository's installed
  `/Users/jo.soroush/.foundry/bin/forge` was invoked explicitly; all 10 Solidity
  tests passed. Foundry emitted a non-test warning because its global signature
  cache is outside the writable workspace.
- An exact C01 dependency-baseline assertion initially failed after `httpx`
  moved from the test extra to declared runtime dependencies for the benchmark
  entry point. The exact assertion was updated to the new explicit dependency
  contract; the final full suite passed without weakening the check.
- Self-audit found that two identically invalid ledger runs could have matching
  normalized outcomes and leave the top-level differential result at `PASS`.
  The final verdict now applies run validity after differential comparison, so
  any invalid run forces `FAIL` and remains listed with its exclusion reason.
- No workload was unstable or disproportionate. The full 1000-payment workload
  completed for both ledgers, so no symmetric reduction was made.

## Lessons learned

- Correctness evidence must accompany throughput: all runs retained explicit
  balance, linkage, replay, and conservation results.
- A fresh contract deployment is the smallest reliable reset for both balances
  and processed-payment identity; clearing only the PostgreSQL journal would be
  an invalid blockchain reset.
- Ledger-only and API timing can be captured on the same payment without
  changing C03–C07 implementations by composing a transparent timing adapter.
- Local PostgreSQL commit and local Anvil receipt are useful measured boundaries
  but do not imply equivalent guarantees or authorize public-network claims.
- C08 implementation, benchmark execution, self-audit, and final independent
  closure re-audit are complete with findings `NONE` and Exit Gate `PASS`.
  The Card remains `IN_PROGRESS` pending explicit human delivery approval and
  controlled Git delivery; C09 remains `NOT_STARTED`.

## Exit Gate

A reproducible evidence set exists for both ledgers, and all conclusions are traceable to either measured evidence or explicitly labeled qualitative analysis.

C08 Exit Gate: `PASS`. Final independent closure re-audit: `PASS`. Findings:
`NONE`. `READY_FOR_HUMAN_DELIVERY_APPROVAL: YES`. Human Delivery Approval:
`NOT_GRANTED`. Git Delivery: `NOT_PERFORMED`. C08 remains `IN_PROGRESS`; C09
remains `NOT_STARTED`.

## Human Delivery Approval and Controlled Delivery — 2026-09-22

- C08 Status: `COMPLETE`
- Final Independent Closure Re-Audit: `PASS`
- Findings: `NONE`
- Exit Gate: `PASS`
- Human Delivery Approval: `GRANTED`
- Controlled Delivery: `COMPLETE`
- Branch: `main`
- Git Delivery: `COMPLETE`
- C09: `NOT_STARTED / NOT_AUTHORIZED`

The immutable delivery SHA is determined by Git and reported in the final
delivery output. No commit SHA is embedded in this delivery record.

Approval covers controlled C08 delivery only. It does not authorize C09 or any
other work. No automatic Card advancement occurred.

---

# 12. C09 — Interview Demo & Engineering Report

## Status

`COMPLETE — Phase 1, independent audit, human approval, and controlled delivery PASS`

Explicit human authorization for C09 Phase 1 was granted on 2026-09-22 after C08 delivery. This authorization does not grant human delivery approval, Git delivery, or a later Card. Current live execution state is owned by `PROJECT_CONTROL.md`.

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

Phase 1 packaged the delivered prototype without changing its behavior:

- `README.md` was rewritten as the public landing page with the implemented shared payment flow, observed fixture, actual setup/build/bootstrap/server commands, C08 result summary, interpretation limits, and links to primary evidence.
- `DEMO_RUNBOOK.md` was created with separate pre-demo setup, a 2–3 minute two-ledger walkthrough, safe reset instructions, optional local receipt inspection, and a bounded interview narrative.
- `ENGINEERING_REPORT.md` was created with the required 18 sections, a Mermaid diagram of the implemented architecture, decision rationale, measured C08 table, normalized differential outcome, separate qualitative trade-offs, and primary evidence references.
- The C09 record in this Evidence Map and the live state in `PROJECT_CONTROL.md` were updated. No application, frontend, contract, test, benchmark methodology, or benchmark evidence file was edited for C09.

The acceptance basis was the C09 goal/deliverables in `UPI_PAYMENT_INTERVIEW_ROADMAP.md`, the Exit Gate below, `AGENTS.md` scope/evidence rules, the actual source and bootstrap interfaces, and `BENCHMARK_AND_EXPERIMENT_PLAN.md` for measured claims. Traceability: setup commands → `pyproject.toml`, `package.json`, `compose.yaml`, `demo_bootstrap.py`, `blockchain_bootstrap.py`, and `demo_app.py`; demo behavior → `frontend/app.ts`, `api.py`, live API/browser observations below; architecture → `ledger.py`, `payment_service.py`, both ledger adapters and the architecture record; results → C08 aggregate JSON, raw records, differential JSON, and qualitative comparison under `evidence/benchmarks/`.

## Demo evidence

On 2026-09-22, using the documented local `upi_payment_test` database and a fresh Anvil chain ID 31337:

- `docker compose up -d postgres`, `upi-demo-bootstrap`, `forge build`, `upi-blockchain-bootstrap`, and `uvicorn upi_payment_experiment.demo_app:create_demo_app --factory` executed successfully. The server reported `http://127.0.0.1:8000/`. The contract bootstrap deployed a fresh address and seeded the C001/M001 fixture. Test keys were kept out of repository files.
- Before payment, the live API returned `C001=100000` and `M001=0` öre on **both** ledger selections. A real HTTP `POST /payments?ledger=conventional` for 10000 öre returned `SUCCESS`; subsequent balance reads returned `90000/10000`, and history linked the payment to a conventional transaction ID. The equivalent real HTTP blockchain POST returned `SUCCESS`, `90000/10000`, and a blockchain transaction-hash history entry.
- `cast receipt` for the observed local blockchain transaction returned status `1 (success)` and `82115` gas used. This is a **single C09 demo receipt**, not a new benchmark measurement or a public-chain cost claim.
- A real browser smoke at the served UI showed the merchant QR, conventional balances/history after the API payment, and blockchain balances/history after selecting Blockchain. Live `GET /merchants/M001/qr` returned HTTP 200 with `image/png`. The browser's Pay button was **not clicked** in this smoke; payment submission was verified through the live HTTP API and existing UI tests. The UI exposes transaction hash and local request time, not receipt/gas fields.
- Documented Python editable install, `npm run build`, Foundry build, database bootstrap, blockchain bootstrap, and Uvicorn invocation were executed. The first `npm ci` attempt was blocked by ownership of the user's existing npm cache; `npm ci --cache /tmp/upi-payment-npm-cache` succeeded, followed by a clean frontend build. This was an environment cache issue, not an application defect.

Verification after documentation work: `.venv/bin/python -m pytest -q` → **195 passed**; `npm run test:frontend` → **11 passed**; `forge test --offline` → **10 passed**, including **256 fuzz runs**; `.venv/bin/python -m pip check` → **PASS**. The complete C08 benchmark matrix was **not rerun**; existing immutable C08 artifacts were inspected directly. Documentation diff and whitespace validation are part of the Phase 1 self-audit below.

## Final lessons

The executable demo needs two independently initialized fixtures: resetting PostgreSQL does not reset an existing on-chain contract. The live UI's request timer and C08's ledger-only completion timing answer different questions. The UI shows a blockchain hash; receipt status/gas require separate local-chain inspection. The benchmark's 10 SEK measured payment must not be confused with the interview demo's 100 SEK payment. All four distinctions are now explicit in the public docs and report.

## Phase 1 self-audit and delivery boundary

Documentation/source/evidence cross-check and `git diff --check` found no C09 product-scope expansion, protected C02–C08 implementation/test changes, benchmark regeneration, or unsupported mainnet/production claim. The C09 Exit Gate has **not** been independently assessed or marked `PASS` in this Phase 1 record. The documentation and live demo evidence support `READY_FOR_INDEPENDENT_AUDIT`, subject to that separate audit. Human Delivery Approval: `NOT_GRANTED`. Git Delivery: `NOT_PERFORMED`. C09 remains `IN_PROGRESS`.

## Exit Gate

The project can be demonstrated and explained without relying on undocumented assumptions.

## Independent Audit and Controlled Delivery — 2026-09-23

- Phase 1 Verification: `PASS`; Self-Audit: `PASS`.
- Independent Audit: `PASS`; blocking findings: `NONE`; Exit Gate: `PASS`; Ready for Human Delivery Approval: `YES`.
- Independent verification confirmed README usability, demo runbook, engineering report, architecture diagram, benchmark traceability, conventional and blockchain live execution, Python **195 passed**, frontend **11 passed**, Solidity **10 passed** including **256 fuzz runs**, package integrity, and `git diff --check`. The README/runbook setup was independently exercised. Browser/UI verification was partial but honestly documented and **NON-BLOCKING**: the browser Pay button was not independently clicked; do not infer otherwise from API execution or UI tests.
- The auditor noted only non-blocking observations: manually copying Anvil test private keys is documented but mildly tedious, and per-run local-Anvil gas variation is expected and distinguished from benchmark aggregates. No benchmark, methodology, architecture, payment, security, or documentation defect remained.
- Human Delivery Approval: `GRANTED` explicitly for C09 controlled Git delivery only. Controlled Git Delivery: `COMPLETE` on `main`; C09 Status: `COMPLETE`. No protected C02–C08 implementation, existing test, or C08 benchmark evidence was changed; `CLAUDE.md` was excluded. No future Card was started or authorized. The immutable delivery SHA is reported in the final Git delivery output, not embedded in this commit.

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
| UI | Minimal TypeScript web UI | ADOPT | Demo clarity without frontend scope |
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
- C02 Phase 1 implementation, initial independent audit failure, remediation, independent re-audit and Exit Gate PASS, implementation delivery (`20098e9c4782d38137fb047711314c2b738de373`), completion evidence/state (`cf4977b9e4364bd5dfef7b788fba7cd363b3affa`), and final delivery/completion record are recorded in the C02 section above.
- C03 Phase 1 implementation, PostgreSQL integration and controlled rollback evidence, independent spec-based audit and Exit Gate PASS, human delivery approval, implementation delivery (`e626bc10eab7a33c5a03042e41a706d989168548`), completion evidence/state (`6a8d33173187a01a5bda28d39fe35e392c2476c3`), and corrective evidence-label documentation (`19bccd9f1a60930a472c694136f0c7fb74eed3f1`) are recorded in the C03 section above.
- Benchmark evidence: `NONE YET`.

Planned evidence requirements remain defined in advance. Live execution state is owned by `PROJECT_CONTROL.md`; this Evidence Map intentionally does not duplicate mutable global fields such as Active Card, authorization, blocker, or Next Allowed Card.
