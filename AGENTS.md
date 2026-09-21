# AGENTS.md
## UPI-Inspired Payment Experiment — Minimal Engineering Harness

This file defines the operating rules for AI-assisted work on this repository.

The goal is to keep the project disciplined without importing unnecessary governance from larger projects.

---

# 1. Primary Rule

Work on **one Card at a time**.

Do not begin a new Card until the current Card has:

```text
implementation complete
tests complete
evidence recorded
review complete
exit gate PASS
delivery approved
```

If any required gate fails:

```text
STOP
```

Do not continue into later Cards.

---

# 2. Evidence-First Rule

Do not make implementation decisions from assumptions when repository evidence can answer the question.

Before changing architecture, dependencies, interfaces, tests, or scope, inspect the relevant:

```text
roadmap
PAYMENT_CARD_EVIDENCE_MAP.md
current code
tests
git state
existing configuration
```

Never invent:

```text
project state
test results
benchmark results
files
dependencies
completion status
performance numbers
```

Measured results must come from real execution.

`PAYMENT_CARD_EVIDENCE_MAP.md` must be updated during each Card as actual evidence is produced. Observed or executed fields may only be populated from real work; they must not be reconstructed later from memory. Planned fields may exist before implementation, but must remain clearly labeled as planned.

Before implementing a Card, verify its Card ID, title, goal, scope, dependencies, and exit gate against all applicable canonical project documents. If a prompt, assistant description, Card wording, implementation instruction, or local interpretation conflicts with any applicable canonical source:

```text
STOP
```

Do not implement from the prompt alone. Resolve the conflict using repository evidence first.

Applicable canonical sources include, depending on the Card or topic:

```text
AGENTS.md
PROJECT_CONTROL.md
UPI_PAYMENT_INTERVIEW_ROADMAP.md
PAYMENT_CARD_EVIDENCE_MAP.md
ARCHITECTURE_AND_DECISIONS.md
BENCHMARK_AND_EXPERIMENT_PLAN.md
```

Use the source relevant to the conflict:

- execution or process conflict → `AGENTS.md` / `PROJECT_CONTROL.md`
- Card scope, dependency, or exit-gate conflict → `UPI_PAYMENT_INTERVIEW_ROADMAP.md`
- Card rationale or planned-versus-observed evidence conflict → `PAYMENT_CARD_EVIDENCE_MAP.md`
- architecture, interface, or technology conflict → `ARCHITECTURE_AND_DECISIONS.md`
- benchmark, timing, or evidence-format conflict → `BENCHMARK_AND_EXPERIMENT_PLAN.md`

Applicability depends on the Card and topic. Do not duplicate the contents of these canonical documents here.

---

# 3. Scope Rule

The interview prototype is:

```text
one payment flow
two ledger implementations
one controlled comparison
```

Core path:

```text
Customer
→ QR payment initiation
→ FastAPI
→ PaymentService
→ LedgerInterface
→ ConventionalLedger or BlockchainLedger
→ result + evidence
```

Do not expand the project into:

```text
real banking
BankID
production KYC/AML
real money
public blockchain
complex wallet system
mobile application
complex frontend
DeFi
token product
real NFC hardware
production cloud platform
```

unless the roadmap is explicitly changed first.

---

# 4. Architecture Guardrail

Payment logic must remain independent from ledger technology.

Target boundary:

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

Do not duplicate the application for each ledger.

Do not leak PostgreSQL-specific or blockchain-specific details into shared domain models unless technically unavoidable and documented.

---

# 5. Payment Correctness Rule

Correctness comes before performance.

The system must protect against:

```text
partial transfer
negative amount
zero amount
insufficient balance
invalid payer
invalid merchant
duplicate payment
replayed idempotency key
corrupted final balance
```

A benchmark is invalid if correctness tests are failing.

Money must use integer minor units:

```text
100 SEK = 10000 öre
```

Do not use binary floating-point values for ledger balances.

---

# 6. Fair Comparison Rule

Conventional and blockchain implementations must use the same, where applicable:

```text
payment semantics
domain model
PaymentService
test dataset
payment amount
workload size
benchmark script
number of measured runs
Docker Compose environment where practical
host machine for paired comparison where practical
```

Primary completion points:

```text
Conventional:
successful database COMMIT

Blockchain:
successful transaction receipt
```

These are comparison timing boundaries only. They must not be interpreted as equivalent guarantees of:

```text
settlement
durability
decentralization
consensus finality
production fault tolerance
```

Do not change benchmark methodology after seeing results unless the reason is documented, the change is explicitly approved, and both ledger implementations are rerun under the same revised methodology.

`BENCHMARK_AND_EXPERIMENT_PLAN.md` is the canonical source for detailed timing definitions, benchmark methodology, environment rules, evidence paths, and output formats. Do not duplicate the detailed benchmark plan inside this file.

---

# 7. Blockchain Boundary

Planned technical baseline:

```text
Anvil
Solidity
web3.py
minimal PaymentLedger contract
```

The blockchain implementation exists only to test the research question.

Do not turn the project into blockchain infrastructure work.

Anvil results must never be presented as representative of:

```text
Ethereum mainnet latency
public network congestion
real gas prices
real validator finality
production blockchain operations
```

---

# 8. Minimal UI Rule

The UI exists only to make the experiment demonstrable.

For C06, use a minimal TypeScript web UI as the presentation/initiation layer calling the existing FastAPI boundary. React is optional and not selected by default; choose the smallest frontend structure that satisfies the demo. Do not add a larger frontend framework unless a concrete C06 requirement justifies it and explicit human approval is recorded.

The UI must not own payment correctness, balance rules, merchant validation, idempotency, payment fingerprinting, persistence, ledger execution, rollback, or blockchain semantics.

Visual polish must never block:

```text
correctness
blockchain comparison
benchmarking
evidence
```

---

# 9. Card Workflow

For every Card use this bounded workflow:

## Verification Harness — C03 onward

From C03 onward, use this incremental verification path within the existing Card workflow:

```text
Canonical Card Specification
→ Derived Acceptance Contract
→ Applicable Critical Invariants
→ Implementation
→ Applicable Unit / Integration Tests
→ Deterministic Invariant Tests
→ Generated Property Tests only when justified
→ Targeted Mutation Testing only when valuable
→ Independent Spec-Based Audit
→ Traceable Evidence
→ Human Approval
→ Controlled Delivery
```

The canonical specification remains in the applicable roadmap, architecture, benchmark, and governance documents. The Acceptance Contract is a concise derivation from those sources and must reference them; it must not become a competing specification.

Before implementation, identify the Card's critical invariants where applicable and record the planned verification strategy in `PAYMENT_CARD_EVIDENCE_MAP.md`. Deterministic invariant tests are required where meaningful. Generated property testing and mutation testing are conditional and require a concrete benefit. A technique marked `NOT_APPLICABLE` must include a short reason. No technique is mandatory merely for ceremony.

Traceability must connect each applicable requirement or invariant to implementation evidence, test or other verification evidence, and the observed result. Before execution, result fields must remain `NOT YET EXECUTED`.

The independent audit must compare the completed Card against:

```text
canonical specification
derived Acceptance Contract
critical invariants
requirement-to-test traceability
executed evidence
false-green risk
```

Card-specific acceptance criteria remain in their canonical sources and must not be copied into this section.

## Phase 1 — Implement + Self-Audit

Perform the full Card implementation.

Then self-check:

```text
scope
architecture
tests
security
data correctness
evidence requirements
unrelated changes
```

Do not split one Card into many unnecessary micro-prompts or micro-tasks.

---

## Phase 2 — Independent Audit

Audit the completed Card against:

```text
Card goal
exit gate
roadmap
AGENTS.md
PAYMENT_CARD_EVIDENCE_MAP.md
tests
git diff
```

The audit must look for:

```text
false-green tests
missing edge cases
scope drift
architecture leakage
weak evidence
security mistakes
benchmark bias
unrelated changes
```

---

## Phase 3 — Consolidated Remediation

Only if the audit finds real issues.

Fix all confirmed findings in one bounded remediation pass where practical.

Do not create endless audit/remediation loops.

After remediation, rerun the required validation.

---

## Phase 4 — Delivery

Delivery is allowed only after:

```text
exit gate PASS
required tests PASS
evidence updated
audit PASS
human approval
```

Then:

```text
commit
push
PR
merge
```

No delivery before approval.

## No Automatic Card Advancement

Any approval to review, remediate, deliver, commit, push, create a PR, merge, or mark the current Card `COMPLETE` applies only to the current Card. It does not authorize implementation of the next Card.

Completing, auditing, delivering, merging, or marking a Card `COMPLETE` must end with:

```text
STOP
```

The next Card may begin only after all of these are true:

- the current Card is fully complete
- repository state is verified
- `PROJECT_CONTROL.md` identifies the next allowed Card
- the human explicitly approves starting that specific next Card

The Agent must never infer authorization for the next Card from:

- a previous “go”
- delivery approval
- merge approval
- Card completion
- roadmap order
- `Next Allowed Card`
- an assistant recommendation

`Next Allowed Card` means sequence eligibility only. It does not mean execution authorization.

---

# 10. Git Guardrail

Before implementation:

```text
confirm expected branch
confirm repository state
confirm current Card
confirm no unrelated dirty work
```

Before delivery:

```text
review git diff
verify only intended files changed
run required tests
run security checks if applicable
update evidence
```

Do not silently include unrelated files in a Card.

---

# 11. Evidence Map Rule

`PAYMENT_CARD_EVIDENCE_MAP.md` is mandatory.

For each completed Card record:

```text
what was built
why it was built
why this design was chosen
alternatives considered
actual implementation
files changed
problems encountered
root causes
fixes applied
tests executed
test results
evidence artifacts
known limitations
lessons learned
git branch
commit SHA
exit gate result
```

Security, data-correctness, performance, trade-off, pull-request, and reviewer fields are required only when materially relevant to the Card.

Do not reconstruct this information later from memory.

Update it while the Card is fresh.

## 11a. Live Project-State Ownership

`PROJECT_CONTROL.md` owns mutable live execution state. Other documents may record historical or per-Card evidence, but must not duplicate mutable global fields such as Active Card, authorization, blocker, or Next Allowed Card. When live status is needed elsewhere, reference `PROJECT_CONTROL.md`.

---

# 12. Benchmark Evidence Rule

Detailed benchmark methodology, timing definitions, evidence paths, and output formats are owned by `BENCHMARK_AND_EXPERIMENT_PLAN.md`.

Never write placeholder numbers as if they were measured. Keep measured facts separate from qualitative analysis.

---

# 13. Security Rule

This repository uses only simulated/test financial data.

Never add:

```text
real bank credentials
real private keys
real payment credentials
production secrets
real customer financial data
```

Secrets must not be committed.

Anvil test keys are test-only and must never be described as production-safe key management.

---

# 14. Change-Control Rule

The technical baseline may change when evidence justifies it.

For any meaningful architecture or technology change, record:

```text
previous decision
new decision
reason
evidence
Cards affected
risk introduced
expected benefit
```

Do not change technology merely because another tool is newer or more interesting.

Prefer the simplest solution that preserves the experiment.

---

# 15. Stop Conditions

Immediately stop implementation when any of the following is true:

```text
current Card is unclear
required source document is missing
repository state contradicts expectations
tests expose balance corruption
benchmark comparison is no longer fair
scope expands beyond the roadmap
real secrets or financial data appear
architecture requires an undocumented redesign
evidence cannot support a claimed result
```

Resolve the issue before proceeding.

---

# 16. Definition of Done for a Card

A Card is complete only when all applicable items are true:

```text
[ ] Card goal achieved
[ ] Scope respected
[ ] Architecture respected
[ ] Tests PASS
[ ] Failure cases tested
[ ] No false-green result identified
[ ] Evidence recorded
[ ] Known limitations recorded
[ ] Git diff reviewed
[ ] No unrelated changes included
[ ] Exit Gate PASS
[ ] Human review/approval complete
```

---

# 17. Working Principle

Use the minimum process that protects:

```text
correctness
comparability
evidence
scope
reproducibility
```

Do not add governance for its own sake.

This is a small interview experiment, not a large production program.
