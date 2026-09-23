# UPI-Inspired Payment Experiment

A small, test-user payment experiment built to answer an engineering question—not to move real money. One QR-initiated payment flow runs through a shared FastAPI and `PaymentService` boundary, with interchangeable PostgreSQL and local-Anvil ledger implementations. The repository includes a minimal TypeScript demo UI and a controlled, sequential comparison of the two paths.

> Does a blockchain-based ledger provide meaningful advantages over a conventional transactional ledger for a small UPI-inspired instant-payment network?

## The implemented payment

The deterministic demo starts with customer `C001` at **1000.00 SEK** and merchant `M001` at **0.00 SEK**. Paying **100.00 SEK** to `M001` returns `SUCCESS`, leaving **900.00 SEK** and **100.00 SEK**, respectively. Both `ConventionalLedger` and `BlockchainLedger` execute this same logical scenario. Amounts are represented internally as integer öre.

```text
TypeScript UI → FastAPI → PaymentService → LedgerInterface
                                          ├─ ConventionalLedger → PostgreSQL
                                          └─ BlockchainLedger → web3.py → local Anvil / PaymentLedger.sol
                                               └──────────────→ PostgreSQL operation journal
```

The UI displays the merchant QR and sends a payment request; correctness, idempotency, persistence, and ledger execution remain backend responsibilities. The QR identifies the merchant; the user enters the amount separately. See [Architecture and Decisions](ARCHITECTURE_AND_DECISIONS.md) for the design record.

## Stack and prerequisites

Python 3 with `venv`/`pip`, PostgreSQL via Docker Compose, Node.js/npm for the TypeScript build, and Foundry's `anvil` and `forge` for the local contract are needed for the full two-ledger demo. The Python package uses FastAPI, psycopg, web3.py, and pytest; the contract uses Solidity. Commands below run from the repository root in a POSIX-compatible shell. Ensure Foundry's binaries are on `PATH` (for example, add `$HOME/.foundry/bin`). The blockchain keys used below are **Anvil-generated local test keys only**; never substitute production keys or commit them.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
npm ci
npm run build
forge build
```

`npm run build` compiles the framework-free TypeScript UI into the FastAPI static directory. `forge build` produces `out/PaymentLedger.sol/PaymentLedger.json`, the artifact used by the existing blockchain bootstrap. No separate frontend server is needed.

If your machine's existing npm cache is not writable, use `npm ci --cache /tmp/upi-payment-npm-cache` instead of `npm ci`; this fallback was verified without changing tracked files.

## Prepare both demo ledgers

Start the repository's PostgreSQL service, then explicitly select its local test database. The bootstrap **resets demo tables**; do not point it at data you need to retain. The database/bootstrap safety guard requires the `upi_payment_test` database on an approved local host; avoid libpq target overrides such as `PGHOST`, `PGHOSTADDR`, `PGSERVICE`, or `PGSERVICEFILE`.

```sh
docker compose up -d postgres
export UPI_DATABASE_DSN='postgresql://upi@127.0.0.1:55432/upi_payment_test'
.venv/bin/upi-demo-bootstrap
```

In a separate terminal, start a fresh local Anvil chain (chain ID `31337`) and leave it running:

```sh
anvil --host 127.0.0.1 --port 8545 --chain-id 31337
```

Anvil prints funded local accounts and their test private keys. In the application terminal, set **three distinct keys** from that output: account 0 as the deployment admin, account 1 as `C001`, and account 2 as `M001`. Keep these values out of tracked files and shell history where practical.

```sh
export UPI_ANVIL_RPC_URL='http://127.0.0.1:8545'
export UPI_ANVIL_ADMIN_PRIVATE_KEY='<Anvil account 0 private key>'
export UPI_ANVIL_C001_PRIVATE_KEY='<Anvil account 1 private key>'
export UPI_ANVIL_M001_PRIVATE_KEY='<Anvil account 2 private key>'
.venv/bin/upi-blockchain-bootstrap
```

The command initializes the local PostgreSQL operation journal, deploys a fresh `PaymentLedger` contract, registers the two fixture participants, seeds their balances, and prints `C07 local PaymentLedger ready: 0x…`. Set the exact printed address in the same application terminal:

```sh
export UPI_PAYMENT_LEDGER_ADDRESS='<address printed by upi-blockchain-bootstrap>'
.venv/bin/uvicorn upi_payment_experiment.demo_app:create_demo_app --factory
```

Uvicorn's default address is <http://127.0.0.1:8000/>. The factory configures the conventional ledger from `UPI_DATABASE_DSN` and adds the blockchain ledger when `UPI_PAYMENT_LEDGER_ADDRESS` is set. Run the commands from the repository root so the default contract-artifact path resolves. To repeat a pristine demo, stop the server, rerun `upi-demo-bootstrap`, run `upi-blockchain-bootstrap` against a fresh Anvil chain or fresh deployment, update the address, and restart the server. These reset commands are for the local test fixture only.

## Use the demo

Open <http://127.0.0.1:8000/>. The page starts on **Conventional** and shows `C001`/`M001` balances, the `M001` merchant QR, a prefilled `100.00` SEK amount, and transaction history. Select **Pay** to show `SUCCESS`, the new balances, a transaction ID, and local API request time. Select **Blockchain** to view its independently initialized equivalent fixture and make the same 100 SEK logical payment. Its transaction ID is the local Anvil transaction hash; the UI shows the hash, history, balances, and local API request time, but does **not** display receipt status or gas. With Foundry's `cast`, the receipt can be inspected separately using `cast receipt --rpc-url http://127.0.0.1:8545 '<transaction hash shown by UI>'`.

The UI is a presentation layer, not a QR scanner or wallet. It displays a real generated merchant QR; entering the amount and submitting in the browser simulates initiation. See the [2–3 minute demo runbook](DEMO_RUNBOOK.md) for a timed walkthrough and reset procedure.

## Controlled comparison

C08 ran the same deterministic 20-customer/5-merchant dataset, sequential logical payment sequence, and reset rule against both ledgers: workloads of 10, 100, 500, and 1000 payments, each repeated five times. There were **8050 measured successful payments per ledger**, **zero payment failures**, **zero invalid runs**, and **zero normalized differential mismatches** across 20 paired runs. The 1000-payment workload's average ledger-only latency was **6.399 ms** for PostgreSQL commit and **97.084 ms** for local-Anvil receipt; average run throughput was **130.429** and **9.725 payments/s**, respectively. These are observed local results, not a universal performance ranking.

Machine-readable aggregates, per-transaction records, differential results, and qualitative analysis are under [evidence/benchmarks/](evidence/benchmarks/). The [Engineering Report](ENGINEERING_REPORT.md) explains methodology, full comparison, and interpretation; [Benchmark and Experiment Plan](BENCHMARK_AND_EXPERIMENT_PLAN.md) defines the timing and fairness rules.

## Interpretation limits

This is a controlled local experiment using synthetic identities and no real money. Anvil is not Ethereum mainnet: these measurements do not establish public-chain latency, fees, consensus finality, decentralization benefits, or production scalability. PostgreSQL commit and Anvil receipt are distinct operational completion boundaries, not equivalent settlement or durability guarantees. Real banking, BankID, production KYC/AML, public-chain deployment, and production key custody are outside scope.

## Repository documents

- [Demo Runbook](DEMO_RUNBOOK.md) — setup, reset, and live interview sequence
- [Engineering Report](ENGINEERING_REPORT.md) — reasoning, results, trade-offs, and evidence
- [Architecture and Decisions](ARCHITECTURE_AND_DECISIONS.md) — technical architecture and decision record
- [Benchmark and Experiment Plan](BENCHMARK_AND_EXPERIMENT_PLAN.md) — canonical measurement rules
- [Benchmark Evidence](evidence/benchmarks/) — measured data and qualitative comparison
- [Project Control](PROJECT_CONTROL.md), [Card Evidence Map](PAYMENT_CARD_EVIDENCE_MAP.md), and [Roadmap](UPI_PAYMENT_INTERVIEW_ROADMAP.md) — execution state and traceability
