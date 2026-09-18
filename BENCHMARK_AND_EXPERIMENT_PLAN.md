# BENCHMARK_AND_EXPERIMENT_PLAN.md
## UPI-Inspired Payment Experiment — Controlled Comparison Plan

This file defines how the conventional and blockchain ledger implementations will be compared.

The goal is to produce evidence, not impressions.

---

# 1. Research Question

**Does a blockchain-based ledger provide meaningful advantages over a conventional transactional ledger for a small UPI-inspired instant-payment network?**

---

# 2. Experimental Units

Two implementations:

```text
A. ConventionalLedger
   PostgreSQL

B. BlockchainLedger
   Anvil + Solidity
```

Both are called through the same:

```text
FastAPI
PaymentService
LedgerInterface
```

---

# 3. Fixed Payment Scenario

Primary logical payment:

```text
Customer C001 starts with 1000 SEK
Merchant M001 starts with 0 SEK

Customer C001 pays Merchant M001 100 SEK

Expected:

Customer C001 = 900 SEK
Merchant M001 = 100 SEK
Transaction = SUCCESS
```

Internally:

```text
1000 SEK = 100000 öre
100 SEK = 10000 öre
```

---

# 4. Fixed Test Dataset

Initial deterministic dataset:

```text
20 customers
5 merchants
```

Each customer starts with:

```text
1000 SEK
```

Each merchant starts with:

```text
0 SEK
```

Data generation must be deterministic.

---

# 5. Fairness Rules

Both implementations must use the same:

```text
Docker Compose environment where practical
host machine where practical
application version
PaymentService
domain models
test dataset
payment amounts
workload sizes
benchmark script
number of repetitions
state reset rule
```

Do not compare different workloads.

---

# 6. Completion Definitions

## Conventional

Operational completion boundary:

```text
PostgreSQL transaction COMMIT succeeds
```

## Blockchain

Operational completion boundary:

```text
transaction is submitted
→ included by Anvil
→ successful transaction receipt returned
```

This distinction must remain explicit in every benchmark report.

---

# 7. Benchmark Workloads

Initial workloads:

```text
10 payments
100 payments
500 payments
1000 payments
```

If 1000 becomes disproportionately slow or unstable for the blockchain implementation:

1. record the problem
2. reduce the maximum workload
3. rerun both ledgers with the same reduced workload
4. document the change

---

# 8. Warm-up

Before measured runs:

```text
perform a small warm-up
discard warm-up measurements
```

Purpose:

- reduce startup effects
- initialize connections
- initialize runtime paths
- reduce one-time setup bias

---

# 9. Repetitions

Initial baseline:

```text
5 measured runs per workload per ledger
```

This is sufficient for the interview prototype.

It is not intended to support publication-level statistical claims.

---

# 10. State Reset

Before every measured run:

```text
reset ledger state
restore deterministic balances
clear benchmark-only transaction state where appropriate
verify initial balances
```

Both implementations must begin from equivalent conditions. State reset and reset verification occur outside the measured benchmark interval.

---

# 11. Concurrency

Primary experiment:

```text
sequential payments
```

Reason:

- simpler interpretation
- clearer correctness validation
- lower benchmark ambiguity

Concurrency is **OUT OF SCOPE** for the current benchmark. It may be added only through an explicitly approved future scope change.

---

# 12. Quantitative Metrics

Measure:

```text
total run duration
average ledger-only latency
median ledger-only latency
p95 ledger-only latency
throughput
success count
failure count
final balance correctness
duplicate-payment correctness
gas used where applicable
```

Primary latency statistics are:

```text
average ledger-only latency
median ledger-only latency
p95 ledger-only latency
```

Secondary API timing is reported separately as:

```text
average API end-to-end latency
median API end-to-end latency
p95 API end-to-end latency
```

Throughput is reported in payments per second:

```text
throughput = completed payment attempts / measured run duration in seconds
```

Warm-up, state reset, reset verification, and setup/bootstrap time are excluded. Only the measured run interval is used. The current benchmark remains sequential.

Where possible, preserve raw per-transaction timings.

---

# 13. Blockchain-Specific Measurements

Where available:

```text
submission latency
confirmation latency
gas used
transaction status
receipt status
```

Report gas for successful transactions separately from gas for failed or reverted transactions, where gas data is available. Do not silently combine successful and failed/reverted transaction populations.

Do not convert local Anvil gas into claimed real-world cost unless assumptions are explicitly stated.

---

# 14. Qualitative Evaluation

# 14A. Timing and Cost Boundaries

For ledger-only measurements:

```text
Blockchain:
T0 = start of ledger execution / submission path
T_submit_ack = transaction hash/acceptance returned
T_receipt = successful receipt returned
submission latency = T_submit_ack - T0
confirmation latency = T_receipt - T_submit_ack
blockchain ledger-only latency = T_receipt - T0

PostgreSQL:
T0 = start of ledger execution
T_commit = successful DB COMMIT
conventional ledger-only latency = T_commit - T0
```

The primary comparison is ledger-only latency. Secondary measurement is full API end-to-end latency, from HTTP request received to final HTTP response returned. Both implementations use the same logical timing boundaries where comparable.

Operational completion at PostgreSQL COMMIT and Anvil receipt are useful timing boundaries, but they are not equivalent guarantees of settlement, durability, decentralization, consensus finality, or production fault tolerance.

Cost evidence is separated into three categories:

- **Measured local execution:** gas used for blockchain transactions and other directly measured local observations.
- **Estimated monetary/infrastructure cost:** public-chain cost may use transparent assumptions such as `gas_used × assumed_gas_price × assumed_ETH_price`; conventional cost may use stated hosting cost divided by assumed transaction volume. No concrete monetary values are assumed before measurement or modeling.
- **Qualitative operational cost:** database/server requirements, node operation, key management, deployment, and maintenance.

Measured, estimated, and qualitative cost evidence must never be mixed.

# 14B. Deterministic Payment Sequence

Use fixed fixtures and a predefined payment sequence. Customers are `C001`–`C020`, merchants are `M001`–`M005`, and both ledger implementations receive the identical logical sequence. If pseudo-random generation is introduced later, record a fixed seed.

Evaluate separately:

```text
architecture complexity
operational dependencies
trust assumptions
central authority requirements
key management
attack surface
auditability
immutability characteristics
correction/reversal behavior
privacy implications
maintenance burden
scalability characteristics
```

Do not convert qualitative judgments into arbitrary numeric scores.

---

# 15. Evidence Storage

Store benchmark evidence under:

```text
evidence/benchmarks/
  conventional/
  blockchain/
```

Required summary formats:

```text
benchmark_results.json
benchmark_results.csv
```

Preferred raw format:

```text
per_transaction_results.jsonl
```

Each record should include applicable fields:

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

`ledger_latency_ms` is the primary timing field. `api_end_to_end_latency_ms` is secondary. Blockchain-only submission, confirmation, and gas fields are omitted where they do not apply.

---

# 16. Result Integrity Rules

Never:

```text
invent results
hide failed runs
remove outliers without explanation
change workload for only one ledger
change completion definition after results are known
generalize Anvil results to Ethereum mainnet
present estimates as measured facts
```

If a run is invalid, keep a record explaining why it was excluded.

---

# 17. Analysis Plan

For each workload and ledger report:

```text
run count
success count
failure count
average ledger-only latency
median ledger-only latency
p95 ledger-only latency
average API end-to-end latency
median API end-to-end latency
p95 API end-to-end latency
throughput
balance correctness
```

For blockchain also report:

```text
Successful blockchain transactions:
average gas used
median gas used

Failed/reverted blockchain transactions, where gas data is available:
average gas used
median gas used
```

Do not silently combine successful and failed/reverted transaction populations.

Then compare:

```text
Conventional vs Blockchain
```

---

# 18. Interpretation Rule

The final conclusion must distinguish:

```text
Measured result
Architectural interpretation
Limitation
```

Example:

```text
Measured:
Local PostgreSQL had lower ledger-only latency in this experiment.

Interpretation:
The local conventional ledger required less execution overhead for this scenario.

Limitation:
Anvil is a local development chain and does not represent public Ethereum behavior.
```

---

# 19. Success Criteria

The benchmark is valid only if:

```text
[ ] both ledgers pass correctness tests
[ ] both use the same dataset
[ ] both use the same workload
[ ] state resets are verified
[ ] measured runs are reproducible
[ ] raw evidence is stored
[ ] failed runs are documented
[ ] completion semantics are explicit
[ ] no unsupported generalization is made
```

---

# 20. Final Comparison Output

Final report should contain:

| Criterion | Conventional | Blockchain | Evidence Type |
|---|---|---|---|
| Payment correctness | measured | measured | quantitative |
| Avg ledger-only latency | measured | measured | quantitative |
| Median ledger-only latency | measured | measured | quantitative |
| p95 ledger-only latency | measured | measured | quantitative |
| Avg API end-to-end latency | measured | measured | quantitative |
| Median API end-to-end latency | measured | measured | quantitative |
| p95 API end-to-end latency | measured | measured | quantitative |
| Throughput | measured | measured | quantitative |
| Failure rate | measured | measured | quantitative |
| Successful transaction gas usage | n/a | measured | quantitative |
| Failed/reverted transaction gas usage | n/a | measured where available | quantitative |
| Complexity | evaluated | evaluated | qualitative |
| Trust model | evaluated | evaluated | qualitative |
| Auditability | evaluated | evaluated | qualitative |
| Reversal behavior | evaluated | evaluated | qualitative |
| Operational burden | evaluated | evaluated | qualitative |

No result values should appear in this table until real benchmark execution occurs.
