# UPI-Inspired Payment Experiment

A small experimental payment system inspired by UPI-style instant payments.

The project explores one core question:

> Does a blockchain-based ledger provide meaningful advantages over a conventional transactional ledger for a small instant-payment network?

## Planned Demo

```text
Customer C001: 1000 SEK
        ↓
Merchant M001: 0 SEK
        ↓
Merchant QR
        ↓
Pay 100 SEK
        ↓
Customer C001: 900 SEK
Merchant M001: 100 SEK
        ↓
Transaction: SUCCESS
```

The same payment flow will run against:

```text
ConventionalLedger → PostgreSQL
BlockchainLedger   → Anvil + Solidity
```

## Planned Stack

```text
Python
FastAPI
PostgreSQL
Anvil
Solidity
web3.py
pytest
Docker Compose
Minimal web UI
```

## Project Documents

```text
AGENTS.md
PROJECT_CONTROL.md
UPI_PAYMENT_INTERVIEW_ROADMAP.md
PAYMENT_CARD_EVIDENCE_MAP.md
ARCHITECTURE_AND_DECISIONS.md
BENCHMARK_AND_EXPERIMENT_PLAN.md
```

## Current Status

```text
Implementation: IN_PROGRESS
Active Card: NONE
Next Allowed Card: C02
Execution Authorization: NOT_GRANTED
Baseline Readiness: COMPLETE
Benchmark Evidence: NONE YET
```

Each Card requires explicit human approval before execution. Next Allowed Card indicates sequence eligibility only.

## Important Boundary

This is an experimental interview prototype.

It does not use:

```text
real money
real bank accounts
real customer financial data
production private keys
public blockchain infrastructure
production KYC/AML
```

Blockchain experiments use local Anvil only.

Measured results will be reported separately from qualitative architectural analysis.
