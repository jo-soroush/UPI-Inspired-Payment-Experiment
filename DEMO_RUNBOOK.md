# Interview demo runbook

The live walkthrough takes about **2–3 minutes after setup**. This is a local test-data demonstration, not a real payment. Run commands from the repository root. Detailed context is in the [README](README.md); the [Engineering Report](ENGINEERING_REPORT.md) holds the measured comparison.

## A. One-time / pre-demo setup

Prerequisites: Python 3 with `venv`/`pip`, Docker Compose, Node.js/npm, and Foundry (`anvil`, `forge`, and optionally `cast`) on `PATH`. These are the existing package/build/bootstrap commands; there is no additional launcher. The fixture reset affects only the local `upi_payment_test` database. Check that it contains no data to preserve. Do not set libpq target overrides (`PGHOST`, `PGHOSTADDR`, `PGSERVICE`, `PGSERVICEFILE`).

1. Install/build once, then prepare PostgreSQL and the conventional fixture:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -e '.[test]'
   npm ci
   npm run build
   forge build
   docker compose up -d postgres
   export UPI_DATABASE_DSN='postgresql://upi@127.0.0.1:55432/upi_payment_test'
   .venv/bin/upi-demo-bootstrap
   ```

   The bootstrap reports `C001=100000 öre, M001=0 öre`. `npm run build` places the TypeScript UI in the package static directory; `forge build` creates the contract artifact at `out/PaymentLedger.sol/PaymentLedger.json`.
   If the local npm cache is not writable, replace `npm ci` with the verified `npm ci --cache /tmp/upi-payment-npm-cache`.

2. Start a **fresh** local Anvil process in another terminal and leave it running:

   ```sh
   anvil --host 127.0.0.1 --port 8545 --chain-id 31337
   ```

   It prints local funded accounts and test private keys. These keys are deliberately insecure test fixtures—never use production keys or commit them. Copy three **distinct** keys from that output into the application terminal: account 0 (admin), account 1 (`C001`), account 2 (`M001`). Avoid saving them in tracked files.

3. Deploy and seed a new contract, then set the address printed by the bootstrap:

   ```sh
   export UPI_ANVIL_RPC_URL='http://127.0.0.1:8545'
   export UPI_ANVIL_ADMIN_PRIVATE_KEY='<Anvil account 0 private key>'
   export UPI_ANVIL_C001_PRIVATE_KEY='<Anvil account 1 private key>'
   export UPI_ANVIL_M001_PRIVATE_KEY='<Anvil account 2 private key>'
   .venv/bin/upi-blockchain-bootstrap
   export UPI_PAYMENT_LEDGER_ADDRESS='<address printed by upi-blockchain-bootstrap>'
   ```

   This command checks the local Anvil chain, initializes/resets the PostgreSQL blockchain operation journal, deploys `PaymentLedger`, registers `C001`/`M001`, and seeds **100000/0 öre**. The address must be from the currently running chain. The service needs the participant keys but not the admin key after deployment.

4. In that same configured application terminal, start the existing FastAPI factory:

   ```sh
   .venv/bin/uvicorn upi_payment_experiment.demo_app:create_demo_app --factory
   ```

   Open <http://127.0.0.1:8000/>. Confirm **Conventional** and **Blockchain** each initially show `C001 = 1000.00 SEK`, `M001 = 0.00 SEK`, and empty history. The `M001` QR should be visible. The page presents the QR; it does not scan it. The amount is entered in the form.

If rehearsing before the interview, restore the two fixtures before the final demo: stop the server, rerun `.venv/bin/upi-demo-bootstrap`, use a fresh Anvil process or redeploy with `.venv/bin/upi-blockchain-bootstrap`, set its **new** `UPI_PAYMENT_LEDGER_ADDRESS`, then restart Uvicorn. A new contract deployment is essential; resetting only PostgreSQL does not reset existing on-chain balances. Never reset while an ambiguous/pending payment is unresolved.

## B. Live demo: conventional (about 45 seconds)

1. Start on **Conventional**. Point out customer `C001` at **1000.00 SEK**, merchant `M001` at **0.00 SEK**, and the merchant-identifying QR.
2. Leave the prefilled amount at **100.00 SEK** and select **Pay** once. The browser sends one request through the shared API; do not retry an ambiguous outcome.
3. Show `SUCCESS`, then **900.00 / 100.00 SEK**. Show the transaction ID/history row and the UI's **local API request time**. This UI timer is not the C08 ledger-only benchmark metric.

## C. Live demo: blockchain (about 45 seconds)

The blockchain contract was independently seeded to the same **1000.00 / 0.00 SEK** fixture during pre-demo setup; switching ledgers does not reset either ledger.

1. Select **Blockchain**, verify **1000.00 / 0.00 SEK** and empty blockchain history, and use the same displayed `M001` QR and **100.00 SEK** amount.
2. Select **Pay** once. Show `SUCCESS`, **900.00 / 100.00 SEK**, and the blockchain history row. Its transaction ID is the local Anvil transaction hash. Show the local API request time.
3. If desired, copy the displayed hash and inspect its actual local receipt outside the UI:

   ```sh
   cast receipt --rpc-url http://127.0.0.1:8545 '<transaction hash shown by UI>'
   ```

   The Foundry output includes receipt status and gas used. **The UI itself does not show receipt fields or gas.** These are local-chain facts, not public-chain fee or finality claims.

## D. Comparison (about 30 seconds)

Open [C08 benchmark evidence](evidence/benchmarks/) or the [Engineering Report](ENGINEERING_REPORT.md). Both ledgers preserved the normalized logical payment outcomes: 20 paired comparisons, zero mismatches. In the 1000-payment sequential local workload, average ledger-only latency was **6.399 ms** at PostgreSQL commit versus **97.084 ms** at local-Anvil receipt; average run throughput was **130.429** versus **9.725 payments/s**. The blockchain path additionally exposes signed-transaction, receipt, and gas semantics, but has more operational and key-management components. This experiment does **not** establish Ethereum mainnet performance or a universal winner.

## E. Interview narrative

> I started from the payment problem rather than assuming blockchain was the answer.

Explain one shared payment flow; the conventional transactional baseline; correctness, idempotency, and failure handling; QR initiation as presentation rather than payment authority; a blockchain ledger behind the same interface; equivalent resets and workloads; measured local results; qualitative trust/operational trade-offs; and the limits of a synthetic, local, sequential experiment. Keep measured evidence distinct from architectural inference.
