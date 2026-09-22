# C08 Qualitative Comparison

## Evidence boundary

This analysis describes the two implementations in this repository and the
local experiment recorded beside this file. It does not assign numeric scores.
Measured local results are in each ledger's `benchmark_results.json`,
`benchmark_results.csv`, and `per_transaction_results.jsonl`. Normalized
logical comparison is in `differential_results.json`.

No monetary or infrastructure cost was estimated in C08. Gas is retained only
as measured local execution data. Local Anvil latency, throughput, receipts,
and gas are not evidence about Ethereum mainnet, a public network, validator
finality, public gas prices, or production blockchain operations.

## Architecture complexity and dependencies

The conventional path uses `PaymentService`, `ConventionalLedger`, and one
PostgreSQL transaction that owns balance locks, balance changes, payment and
transaction persistence, idempotency persistence, and commit/rollback.

The blockchain path reuses the same `PaymentService` and domain interface, but
adds a Solidity contract, compilation artifact, local Anvil RPC process,
Web3 integration, participant signing identities, signed transaction
submission, receipt handling, and a PostgreSQL operation journal. The journal
coordinates request identity and recovery; the contract remains balance
authority. This creates more runtime components and more cross-system states
to inspect than the conventional path.

## Trust model and central authority

The conventional experiment trusts the PostgreSQL service and the application
process allowed to update it. Database constraints, row locking, and one ACID
transaction enforce the transfer boundary.

The blockchain experiment trusts the locally deployed contract code, the
configured Anvil process, RPC responses, the deployment owner used to register
and seed participants, and the private signer mapped to each payer. The
contract owner is a central authority for participant setup in this prototype.
Anvil is a single local development process, not decentralized infrastructure.

## Key management and attack surface

The conventional path requires database connection security and application
authorization. It does not require per-payer blockchain signing keys.

The blockchain path adds backend-only test private keys, address-to-identity
mapping, transaction nonces, RPC availability, contract deployment, and signed
raw transaction handling. Those are additional failure and attack surfaces.
The benchmark creates ephemeral test identities at runtime and does not store
or claim production-safe custody. The database journal remains an additional
protected dependency even though balances are on-chain.

## Auditability and immutability/correction model

Both implementations expose linked payment and transaction history through
the shared interface. PostgreSQL history is directly queryable and governed by
database/application permissions. It is mutable by an administrator with
sufficient database authority; corrections can use normal controlled database
or application procedures.

The blockchain contract emits payment events and retains processed-payment and
balance state. Successful transactions have receipt and gas evidence. Applied
contract state is not edited like a database row; correction or reversal would
require an explicit new contract operation or a replacement/migration design,
none of which C08 adds. The off-chain recovery journal is still mutable
PostgreSQL state and must not be mistaken for the on-chain ledger itself.

## Privacy

The conventional data is held in the configured database and can be restricted
to application/database operators. The local contract exposes participant
hashes, balances through known identifiers, payment hashes, transfers, and
events to anyone with access to that chain/RPC. Hashing fixture identifiers is
not an anonymity guarantee. Neither implementation contains real customer or
financial data in this experiment.

## Operational maintenance

The conventional path requires PostgreSQL schema, backups, monitoring,
connection management, and application/database recovery procedures.

The blockchain path additionally requires contract build/deployment,
chain/RPC operation, signer and nonce management, receipt reconciliation, and
coordination between journal and chain. The journal and chain do not share one
ACID transaction, so unresolved provider outcomes require reconciliation.

## Scalability considerations

The measured primary workload is sequential, local, and single-host. It does
not test concurrency, contention, distributed failure, public-chain congestion,
multi-node consensus, or horizontal scaling. Within that deliberately narrow
scope, the machine-readable evidence reports the observed PostgreSQL commit
and local-Anvil receipt completion boundaries separately. Those boundaries are
useful for this experiment but do not represent equivalent durability,
settlement, decentralization, or production fault-tolerance guarantees.

## Correction against over-interpretation

The normalized differential comparison checks shared business outcomes only:
status, balance deltas, history linkage, replay result and balance stability,
and value conservation. It intentionally excludes transaction hashes, gas,
timing, and receipt/event identity. Passing that comparison demonstrates
equivalent outcomes for this controlled dataset and sequence; it does not make
the two operational models equivalent.
