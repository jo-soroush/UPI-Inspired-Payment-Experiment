"""C08 reproducible local benchmark and differential-comparison harness.

The harness deliberately uses the existing FastAPI -> PaymentService -> ledger
path.  Reset, verification, warm-up, and correctness checks are outside every
measured interval.  It accepts only the dedicated local PostgreSQL test
database and a verified local Anvil process.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import socket
import statistics
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit

from eth_account import Account as EthereumAccount
import httpx
import psycopg
from psycopg.conninfo import conninfo_to_dict
from web3 import HTTPProvider, Web3

from .api import create_app
from .blockchain_bootstrap import (
    LOCAL_ANVIL_CHAIN_ID,
    _send_and_wait,
    _transaction_parameters,
    _validated_local_anvil_connection,
    _validated_local_anvil_rpc_url,
)
from .blockchain_ledger import BlockchainLedger, SigningIdentity
from .conventional_ledger import ConventionalLedger
from .demo_bootstrap import (
    IMPLICIT_TARGET_ENVIRONMENT,
    _validated_demo_dsn,
    _without_implicit_target_environment,
)
from .domain import LedgerResult, Payment, PaymentStatus, Transaction
from .ledger import LedgerInterface
from .payment_service import PaymentService


CUSTOMERS = tuple(f"C{index:03d}" for index in range(1, 21))
MERCHANTS = tuple(f"M{index:03d}" for index in range(1, 6))
INITIAL_CUSTOMER_BALANCE = 100_000
INITIAL_MERCHANT_BALANCE = 0
PAYMENT_AMOUNT = 1_000
WORKLOADS = (10, 100, 500, 1_000)
MEASURED_RUNS = 5
WARM_UP_PAYMENTS = 3
BENCHMARK_DATABASE_NAME = "upi_payment_test"
BENCHMARK_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
ARTIFACT_PATH = Path("out/PaymentLedger.sol/PaymentLedger.json")


@dataclass(frozen=True)
class LogicalPayment:
    index: int
    payer_id: str
    merchant_id: str
    amount: int = PAYMENT_AMOUNT
    currency: str = "SEK"


@dataclass(frozen=True)
class ExecutionPayment:
    logical: LogicalPayment
    payment_id: str
    idempotency_key: str


@dataclass(frozen=True)
class Measurement:
    ledger_type: str
    workload_size: int
    run_number: int
    logical_index: int
    timestamp: str
    payment_id: str
    idempotency_key: str
    payer_id: str
    merchant_id: str
    amount: int
    currency: str
    ledger_latency_ms: float
    api_end_to_end_latency_ms: float
    status: str
    transaction_id: str | None
    submission_latency_ms: float | None = None
    confirmation_latency_ms: float | None = None
    successful_gas_used_if_applicable: int | None = None
    failed_or_reverted_gas_used_if_applicable: int | None = None
    failure_reason: str | None = None

    def evidence_dict(self) -> dict[str, Any]:
        """Return a JSON record, omitting only genuinely inapplicable fields."""

        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None
        }


@dataclass(frozen=True)
class NormalizedRun:
    workload_size: int
    run_number: int
    statuses: tuple[str, ...]
    payer_balance_deltas: tuple[tuple[str, int], ...]
    merchant_balance_deltas: tuple[tuple[str, int], ...]
    transaction_payment_indices: tuple[int, ...]
    replay_same_result: bool
    replay_balance_unchanged: bool
    no_partial_transfer: bool


class TimedLedger:
    """Measure only the existing ledger call while preserving its interface."""

    def __init__(
        self,
        ledger: LedgerInterface,
        *,
        clock_ns: Callable[[], int] = time.perf_counter_ns,
    ) -> None:
        self._ledger = ledger
        self._clock_ns = clock_ns
        self._latencies_ms: dict[str, float] = {}

    def execute_payment(
        self, payment: Payment, *, request_fingerprint: str
    ) -> LedgerResult:
        started = self._clock_ns()
        try:
            return self._ledger.execute_payment(
                payment, request_fingerprint=request_fingerprint
            )
        finally:
            self._latencies_ms[payment.payment_id] = (
                self._clock_ns() - started
            ) / 1_000_000

    def take_latency_ms(self, payment_id: str) -> float:
        return self._latencies_ms.pop(payment_id)

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        return self._ledger.get_balance(owner_id, currency)

    def get_payment(self, payment_id: str) -> Payment | None:
        return self._ledger.get_payment(payment_id)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        return self._ledger.get_transaction(transaction_id)

    def list_transactions(
        self, payment_id: str | None = None
    ) -> list[Transaction]:
        return self._ledger.list_transactions(payment_id)


def logical_workload(size: int) -> tuple[LogicalPayment, ...]:
    """Generate the canonical deterministic logical sequence."""

    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("workload size must be a positive integer")
    return tuple(
        LogicalPayment(
            index=index,
            payer_id=CUSTOMERS[(index - 1) % len(CUSTOMERS)],
            merchant_id=MERCHANTS[(index - 1) % len(MERCHANTS)],
        )
        for index in range(1, size + 1)
    )


def execution_workload(
    ledger_name: str, workload_size: int, run_number: int
) -> tuple[ExecutionPayment, ...]:
    """Scope execution identity without changing the logical workload."""

    scope = ledger_name.upper()
    return tuple(
        ExecutionPayment(
            logical=item,
            payment_id=(
                f"C08-{scope}-W{workload_size:04d}-R{run_number:02d}-"
                f"P{item.index:04d}"
            ),
            idempotency_key=(
                f"C08-IDEM-{scope}-W{workload_size:04d}-R{run_number:02d}-"
                f"P{item.index:04d}"
            ),
        )
        for item in logical_workload(workload_size)
    )


def benchmark_accounts() -> tuple[tuple[str, str, str, int], ...]:
    return tuple(
        (f"ACC-{owner_id}", owner_id, "SEK", INITIAL_CUSTOMER_BALANCE)
        for owner_id in CUSTOMERS
    ) + tuple(
        (f"ACC-{owner_id}", owner_id, "SEK", INITIAL_MERCHANT_BALANCE)
        for owner_id in MERCHANTS
    )


def expected_balances(
    workload: Sequence[LogicalPayment],
) -> dict[str, int]:
    balances = {
        **{owner: INITIAL_CUSTOMER_BALANCE for owner in CUSTOMERS},
        **{owner: INITIAL_MERCHANT_BALANCE for owner in MERCHANTS},
    }
    for item in workload:
        balances[item.payer_id] -= item.amount
        balances[item.merchant_id] += item.amount
    if any(balance < 0 for balance in balances.values()):
        raise ValueError("workload exceeds deterministic fixture balances")
    return balances


def validated_benchmark_dsn(raw_dsn: str) -> str:
    """Fail closed before any connection or destructive database operation."""

    if any(os.environ.get(name) for name in IMPLICIT_TARGET_ENVIRONMENT):
        raise ValueError(
            "C08 does not allow implicit libpq database target environment"
        )
    if not isinstance(raw_dsn, str) or not raw_dsn.strip():
        raise ValueError("C08 database DSN must be a non-empty PostgreSQL URI")
    parsed = urlsplit(raw_dsn)
    if parsed.scheme != "postgresql" or parsed.hostname not in BENCHMARK_LOCAL_HOSTS:
        raise ValueError("C08 requires an explicit PostgreSQL loopback host")
    parameters = conninfo_to_dict(raw_dsn)
    if (
        parameters.get("host") not in BENCHMARK_LOCAL_HOSTS
        or parameters.get("hostaddr") not in (None, "")
        or parameters.get("service") not in (None, "")
        or parameters.get("dbname") != BENCHMARK_DATABASE_NAME
    ):
        raise ValueError(
            "C08 is restricted to the explicit local upi_payment_test database"
        )
    return _validated_demo_dsn(raw_dsn)


def reset_benchmark_database(raw_dsn: str) -> None:
    """Restore exactly the deterministic 25-account fixture."""

    validated_dsn = validated_benchmark_dsn(raw_dsn)
    _reset_benchmark_database(validated_dsn)


def _reset_benchmark_database(validated_dsn: str) -> None:
    with _without_implicit_target_environment():
        ConventionalLedger(validated_dsn).initialize_schema()
        with psycopg.connect(validated_dsn) as connection:
            connection.execute(
                "TRUNCATE blockchain_idempotency_records, blockchain_operations, "
                "idempotency_records, transactions, payments, accounts"
            )
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO accounts (account_id, owner_id, currency, balance)
                    VALUES (%s, %s, %s, %s)
                    """,
                    benchmark_accounts(),
                )


def verify_initial_state(ledger: LedgerInterface) -> None:
    """Verify all fixture balances outside the benchmark interval."""

    expected = {
        **{owner: INITIAL_CUSTOMER_BALANCE for owner in CUSTOMERS},
        **{owner: INITIAL_MERCHANT_BALANCE for owner in MERCHANTS},
    }
    observed = {owner: ledger.get_balance(owner) for owner in expected}
    if observed != expected or ledger.list_transactions():
        raise RuntimeError("benchmark reset verification failed")


def _deploy_benchmark_contract(
    web3: Web3,
    artifact_path: Path,
    admin_private_key: str,
    participant_private_keys: Mapping[str, str],
):
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    admin = web3.eth.account.from_key(admin_private_key)
    factory = web3.eth.contract(
        abi=artifact["abi"], bytecode=artifact["bytecode"]["object"]
    )
    receipt = _send_and_wait(
        web3,
        admin,
        factory.constructor(admin.address).build_transaction(
            _transaction_parameters(web3, admin.address, gas=2_500_000)
        ),
    )
    contract = web3.eth.contract(
        address=receipt["contractAddress"], abi=artifact["abi"]
    )
    starting_balances = {
        **{owner: INITIAL_CUSTOMER_BALANCE for owner in CUSTOMERS},
        **{owner: INITIAL_MERCHANT_BALANCE for owner in MERCHANTS},
    }
    for owner_id in (*CUSTOMERS, *MERCHANTS):
        participant = web3.eth.account.from_key(participant_private_keys[owner_id])
        _send_and_wait(
            web3,
            admin,
            contract.functions.registerParticipant(
                Web3.keccak(text=owner_id), participant.address
            ).build_transaction(_transaction_parameters(web3, admin.address)),
        )
        _send_and_wait(
            web3,
            admin,
            contract.functions.seedBalance(
                Web3.keccak(text=owner_id), starting_balances[owner_id]
            ).build_transaction(_transaction_parameters(web3, admin.address)),
        )
    return contract


class ConventionalEnvironment:
    ledger_name = "conventional"

    def __init__(self, raw_dsn: str) -> None:
        self._dsn = validated_benchmark_dsn(raw_dsn)

    def reset(self, workload_size: int, run_number: int) -> ConventionalLedger:
        _reset_benchmark_database(self._dsn)
        transaction_numbers = iter(range(1, workload_size + 2))
        return ConventionalLedger(
            self._dsn,
            transaction_id_factory=lambda: (
                f"TX-C08-CONVENTIONAL-W{workload_size:04d}-R{run_number:02d}-"
                f"P{next(transaction_numbers):04d}"
            ),
        )

    @staticmethod
    def metadata(_payment_id: str) -> dict[str, float | int | None]:
        return {}


class BlockchainEnvironment:
    ledger_name = "blockchain"

    def __init__(
        self,
        raw_dsn: str,
        web3: Web3,
        admin_private_key: str,
        participant_private_keys: Mapping[str, str],
        artifact_path: Path = ARTIFACT_PATH,
    ) -> None:
        self._dsn = validated_benchmark_dsn(raw_dsn)
        endpoint_uri = getattr(web3.provider, "endpoint_uri", None)
        _validated_local_anvil_rpc_url(str(endpoint_uri or ""))
        _validated_local_anvil_connection(web3)
        self._web3 = web3
        self._admin_private_key = admin_private_key
        self._participant_private_keys = dict(participant_private_keys)
        self._artifact_path = artifact_path
        self._ledger: BlockchainLedger | None = None

    def reset(self, workload_size: int, run_number: int) -> BlockchainLedger:
        del workload_size, run_number
        _reset_benchmark_database(self._dsn)
        contract = _deploy_benchmark_contract(
            self._web3,
            self._artifact_path,
            self._admin_private_key,
            self._participant_private_keys,
        )
        identities = {
            owner_id: SigningIdentity(
                self._web3.eth.account.from_key(private_key).address,
                private_key,
            )
            for owner_id, private_key in self._participant_private_keys.items()
        }
        self._ledger = BlockchainLedger(
            self._web3,
            contract,
            self._dsn,
            identities,
            receipt_timeout=10,
        )
        return self._ledger

    def metadata(self, payment_id: str) -> dict[str, float | int | None]:
        if self._ledger is None:
            raise RuntimeError("blockchain environment has not been reset")
        operation = self._ledger._journal.get_by_payment_id(payment_id)
        if operation is None:
            return {}
        submission = None
        confirmation = None
        if operation.submitted_at is not None:
            submission = (
                operation.submitted_at - operation.prepared_at
            ).total_seconds() * 1_000
        if operation.submitted_at is not None and operation.confirmed_at is not None:
            confirmation = (
                operation.confirmed_at - operation.submitted_at
            ).total_seconds() * 1_000
        successful_gas = operation.gas_used if operation.status == "SUCCESS" else None
        failed_gas = operation.gas_used if operation.status == "FAILED" else None
        return {
            "submission_latency_ms": submission,
            "confirmation_latency_ms": confirmation,
            "successful_gas_used_if_applicable": successful_gas,
            "failed_or_reverted_gas_used_if_applicable": failed_gas,
        }


async def execute_measured_run(
    ledger_name: str,
    ledger: LedgerInterface,
    workload_size: int,
    run_number: int,
    *,
    metadata: Callable[[str], Mapping[str, Any]],
    clock_ns: Callable[[], int] = time.perf_counter_ns,
) -> tuple[list[Measurement], dict[str, Any], NormalizedRun]:
    """Execute one sequential API workload and then verify it outside timing."""

    timed_ledger = TimedLedger(ledger, clock_ns=clock_ns)
    service = PaymentService(timed_ledger)
    app = create_app(service, services={ledger_name: service})
    transport = httpx.ASGITransport(app=app)
    executions = execution_workload(ledger_name, workload_size, run_number)
    records: list[Measurement] = []
    run_started = clock_ns()
    async with httpx.AsyncClient(transport=transport, base_url="http://c08.local") as client:
        for execution in executions:
            payload = {
                "payment_id": execution.payment_id,
                "payer_id": execution.logical.payer_id,
                "merchant_id": execution.logical.merchant_id,
                "amount": execution.logical.amount,
                "currency": execution.logical.currency,
                "idempotency_key": execution.idempotency_key,
            }
            api_started = clock_ns()
            response = await client.post(
                "/payments", params={"ledger": ledger_name}, json=payload
            )
            api_latency_ms = (clock_ns() - api_started) / 1_000_000
            body = response.json()
            status = body.get("status", f"HTTP_{response.status_code}")
            failure_reason = None if response.status_code == 200 else json.dumps(body)
            ledger_latency = timed_ledger.take_latency_ms(execution.payment_id)
            blockchain_metadata = dict(metadata(execution.payment_id))
            records.append(
                Measurement(
                    ledger_type=ledger_name,
                    workload_size=workload_size,
                    run_number=run_number,
                    logical_index=execution.logical.index,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    payment_id=execution.payment_id,
                    idempotency_key=execution.idempotency_key,
                    payer_id=execution.logical.payer_id,
                    merchant_id=execution.logical.merchant_id,
                    amount=execution.logical.amount,
                    currency=execution.logical.currency,
                    ledger_latency_ms=ledger_latency,
                    api_end_to_end_latency_ms=api_latency_ms,
                    status=status,
                    transaction_id=body.get("transaction_id"),
                    failure_reason=failure_reason,
                    **blockchain_metadata,
                )
            )
        measured_duration_seconds = (clock_ns() - run_started) / 1_000_000_000

        # Correctness/replay verification is deliberately after the timed interval.
        balances_before_replay = {
            owner: service.get_balance(owner) for owner in (*CUSTOMERS, *MERCHANTS)
        }
        replay = await client.post(
            "/payments",
            params={"ledger": ledger_name},
            json={
                "payment_id": executions[-1].payment_id,
                "payer_id": executions[-1].logical.payer_id,
                "merchant_id": executions[-1].logical.merchant_id,
                "amount": executions[-1].logical.amount,
                "currency": executions[-1].logical.currency,
                "idempotency_key": executions[-1].idempotency_key,
            },
        )
        balances_after_replay = {
            owner: service.get_balance(owner) for owner in (*CUSTOMERS, *MERCHANTS)
        }

    expected = expected_balances(logical_workload(workload_size))
    transactions = service.list_transactions()
    expected_ids = {execution.payment_id for execution in executions}
    transaction_ids = {transaction.payment_id for transaction in transactions}
    replay_body = replay.json()
    replay_same_result = (
        replay.status_code == 200
        and replay_body.get("transaction_id") == records[-1].transaction_id
        and replay_body.get("status") == records[-1].status
    )
    balances_correct = balances_after_replay == expected
    linkage_correct = transaction_ids == expected_ids and len(transactions) == workload_size
    all_success = all(record.status == "SUCCESS" for record in records)
    replay_balance_unchanged = balances_before_replay == balances_after_replay
    no_partial_transfer = sum(balances_after_replay.values()) == (
        len(CUSTOMERS) * INITIAL_CUSTOMER_BALANCE
    )
    valid = all(
        (
            all_success,
            balances_correct,
            linkage_correct,
            replay_same_result,
            replay_balance_unchanged,
            no_partial_transfer,
        )
    )
    exclusion_reason = None if valid else "; ".join(
        label
        for label, okay in (
            ("non-success payment", all_success),
            ("final balance mismatch", balances_correct),
            ("transaction linkage mismatch", linkage_correct),
            ("replay result mismatch", replay_same_result),
            ("replay changed balances", replay_balance_unchanged),
            ("value conservation failed", no_partial_transfer),
        )
        if not okay
    )
    summary = summarize_run(
        records,
        measured_duration_seconds,
        balances_correct=balances_correct,
        replay_correct=replay_same_result and replay_balance_unchanged,
        transaction_linkage_correct=linkage_correct,
        no_partial_transfer=no_partial_transfer,
        valid=valid,
        exclusion_reason=exclusion_reason,
    )
    normalized = normalize_run(
        records,
        balances_after_replay,
        transaction_ids,
        replay_same_result,
        replay_balance_unchanged,
        no_partial_transfer,
    )
    return records, summary, normalized


async def execute_warm_up(
    ledger_name: str,
    ledger: LedgerInterface,
    workload_size: int,
) -> None:
    """Exercise the same stack without returning or persisting timing evidence."""

    timed = TimedLedger(ledger)
    service = PaymentService(timed)
    app = create_app(service, services={ledger_name: service})
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://c08.local") as client:
        for execution in execution_workload(
            ledger_name, min(WARM_UP_PAYMENTS, workload_size), 0
        ):
            response = await client.post(
                "/payments",
                params={"ledger": ledger_name},
                json={
                    "payment_id": execution.payment_id,
                    "payer_id": execution.logical.payer_id,
                    "merchant_id": execution.logical.merchant_id,
                    "amount": execution.logical.amount,
                    "currency": execution.logical.currency,
                    "idempotency_key": execution.idempotency_key,
                },
            )
            if response.status_code != 200 or response.json().get("status") != "SUCCESS":
                raise RuntimeError("C08 warm-up payment failed")


def _percentile_95(values: Sequence[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _statistics(values: Sequence[float | int]) -> dict[str, float | None]:
    if not values:
        return {"average": None, "median": None, "p95": None}
    numeric = [float(value) for value in values]
    return {
        "average": statistics.fmean(numeric),
        "median": statistics.median(numeric),
        "p95": _percentile_95(numeric),
    }


def summarize_run(
    records: Sequence[Measurement],
    duration_seconds: float,
    **correctness: Any,
) -> dict[str, Any]:
    successes = [record for record in records if record.status == "SUCCESS"]
    successful_gas = [
        record.successful_gas_used_if_applicable
        for record in records
        if record.successful_gas_used_if_applicable is not None
    ]
    failed_gas = [
        record.failed_or_reverted_gas_used_if_applicable
        for record in records
        if record.failed_or_reverted_gas_used_if_applicable is not None
    ]
    submission = [
        record.submission_latency_ms
        for record in records
        if record.submission_latency_ms is not None
    ]
    confirmation = [
        record.confirmation_latency_ms
        for record in records
        if record.confirmation_latency_ms is not None
    ]
    first = records[0]
    return {
        "ledger_type": first.ledger_type,
        "workload_size": first.workload_size,
        "run_number": first.run_number,
        "attempt_count": len(records),
        "success_count": len(successes),
        "failure_count": len(records) - len(successes),
        "ledger_latency_ms": _statistics(
            [record.ledger_latency_ms for record in records]
        ),
        "api_end_to_end_latency_ms": _statistics(
            [record.api_end_to_end_latency_ms for record in records]
        ),
        "submission_latency_ms": _statistics(submission),
        "confirmation_latency_ms": _statistics(confirmation),
        "throughput_payments_per_second": (
            len(records) / duration_seconds if duration_seconds > 0 else None
        ),
        "measured_duration_seconds": duration_seconds,
        "successful_gas_used": _statistics(successful_gas),
        "successful_gas_count": len(successful_gas),
        "failed_or_reverted_gas_used": _statistics(failed_gas),
        "failed_or_reverted_gas_count": len(failed_gas),
        **correctness,
    }


def normalize_run(
    records: Sequence[Measurement],
    balances: Mapping[str, int],
    transaction_payment_ids: set[str],
    replay_same_result: bool,
    replay_balance_unchanged: bool,
    no_partial_transfer: bool,
) -> NormalizedRun:
    """Normalize only business meaning; omit timing and implementation identity."""

    indices_by_id = {record.payment_id: record.logical_index for record in records}
    return NormalizedRun(
        workload_size=records[0].workload_size,
        run_number=records[0].run_number,
        statuses=tuple(record.status for record in records),
        payer_balance_deltas=tuple(
            (owner, balances[owner] - INITIAL_CUSTOMER_BALANCE)
            for owner in CUSTOMERS
        ),
        merchant_balance_deltas=tuple(
            (owner, balances[owner] - INITIAL_MERCHANT_BALANCE)
            for owner in MERCHANTS
        ),
        transaction_payment_indices=tuple(
            sorted(indices_by_id[payment_id] for payment_id in transaction_payment_ids)
        ),
        replay_same_result=replay_same_result,
        replay_balance_unchanged=replay_balance_unchanged,
        no_partial_transfer=no_partial_transfer,
    )


def differential_result(
    conventional: Mapping[tuple[int, int], NormalizedRun],
    blockchain: Mapping[tuple[int, int], NormalizedRun],
    *,
    conventional_records: Sequence[Measurement] = (),
    blockchain_records: Sequence[Measurement] = (),
) -> dict[str, Any]:
    keys = sorted(set(conventional) | set(blockchain))
    mismatches = []
    for key in keys:
        left = conventional.get(key)
        right = blockchain.get(key)
        if left != right:
            conventional_raw = [
                record.evidence_dict()
                for record in conventional_records
                if (record.workload_size, record.run_number) == key
            ]
            blockchain_raw = [
                record.evidence_dict()
                for record in blockchain_records
                if (record.workload_size, record.run_number) == key
            ]
            mismatches.append(
                {
                    "workload_size": key[0],
                    "run_number": key[1],
                    "logical_workload": [asdict(item) for item in logical_workload(key[0])],
                    "conventional_normalized": asdict(left) if left else None,
                    "blockchain_normalized": asdict(right) if right else None,
                    "conventional_raw_outcomes": conventional_raw,
                    "blockchain_raw_outcomes": blockchain_raw,
                }
            )
    return {
        "comparison": "PASS" if not mismatches and keys else "FAIL",
        "compared_run_count": len(keys),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "excluded_fields": [
            "transaction_id",
            "gas",
            "timing",
            "receipt_or_event_metadata",
        ],
    }


def apply_run_validity(
    comparison: Mapping[str, Any],
    conventional_summaries: Sequence[Mapping[str, Any]],
    blockchain_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Prevent equal failures in both ledgers from producing a false PASS."""

    invalid_runs = [
        {
            "ledger_type": ledger_name,
            "workload_size": summary["workload_size"],
            "run_number": summary["run_number"],
            "exclusion_reason": summary["exclusion_reason"],
        }
        for ledger_name, summaries in (
            ("conventional", conventional_summaries),
            ("blockchain", blockchain_summaries),
        )
        for summary in summaries
        if not summary["valid"]
    ]
    result = dict(comparison)
    result["invalid_run_count"] = len(invalid_runs)
    result["invalid_runs"] = invalid_runs
    if invalid_runs:
        result["comparison"] = "FAIL"
    return result


def aggregate_summaries(
    summaries: Sequence[Mapping[str, Any]], records: Sequence[Measurement]
) -> list[dict[str, Any]]:
    aggregates = []
    for workload_size in sorted({int(item["workload_size"]) for item in summaries}):
        selected = [item for item in summaries if item["workload_size"] == workload_size]
        valid = [item for item in selected if item["valid"]]
        valid_run_numbers = {int(item["run_number"]) for item in valid}
        selected_records = [
            record
            for record in records
            if record.workload_size == workload_size
            and record.run_number in valid_run_numbers
        ]
        successful_gas = [
            record.successful_gas_used_if_applicable
            for record in selected_records
            if record.successful_gas_used_if_applicable is not None
        ]
        failed_gas = [
            record.failed_or_reverted_gas_used_if_applicable
            for record in selected_records
            if record.failed_or_reverted_gas_used_if_applicable is not None
        ]
        submission = [
            record.submission_latency_ms
            for record in selected_records
            if record.submission_latency_ms is not None
        ]
        confirmation = [
            record.confirmation_latency_ms
            for record in selected_records
            if record.confirmation_latency_ms is not None
        ]
        aggregates.append(
            {
                "workload_size": workload_size,
                "measured_run_count": len(selected),
                "valid_run_count": len(valid),
                "invalid_run_count": len(selected) - len(valid),
                "success_count": sum(int(item["success_count"]) for item in selected),
                "failure_count": sum(int(item["failure_count"]) for item in selected),
                "ledger_latency_ms": _statistics(
                    [record.ledger_latency_ms for record in selected_records]
                ),
                "api_end_to_end_latency_ms": _statistics(
                    [record.api_end_to_end_latency_ms for record in selected_records]
                ),
                "submission_latency_ms": _statistics(submission),
                "confirmation_latency_ms": _statistics(confirmation),
                "throughput_payments_per_second": _statistics(
                    [item["throughput_payments_per_second"] for item in valid]
                ),
                "all_balances_correct": all(
                    bool(item["balances_correct"]) for item in selected
                ),
                "all_replays_correct": all(
                    bool(item["replay_correct"]) for item in selected
                ),
                "all_transaction_linkage_correct": all(
                    bool(item["transaction_linkage_correct"]) for item in selected
                ),
                "successful_gas_used": _statistics(successful_gas),
                "successful_gas_count": len(successful_gas),
                "failed_or_reverted_gas_used": _statistics(failed_gas),
                "failed_or_reverted_gas_count": len(failed_gas),
            }
        )
    return aggregates


CSV_FIELDS = (
    "row_type",
    "ledger_type",
    "workload_size",
    "run_number",
    "attempt_count",
    "success_count",
    "failure_count",
    "average_ledger_latency_ms",
    "median_ledger_latency_ms",
    "p95_ledger_latency_ms",
    "average_api_end_to_end_latency_ms",
    "median_api_end_to_end_latency_ms",
    "p95_api_end_to_end_latency_ms",
    "average_submission_latency_ms",
    "median_submission_latency_ms",
    "p95_submission_latency_ms",
    "average_confirmation_latency_ms",
    "median_confirmation_latency_ms",
    "p95_confirmation_latency_ms",
    "throughput_payments_per_second",
    "average_successful_gas_used",
    "median_successful_gas_used",
    "average_failed_or_reverted_gas_used",
    "median_failed_or_reverted_gas_used",
    "balances_correct",
    "replay_correct",
    "transaction_linkage_correct",
    "valid",
    "exclusion_reason",
)


def write_ledger_evidence(
    output_root: Path,
    ledger_name: str,
    records: Sequence[Measurement],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    directory = output_root / ledger_name
    directory.mkdir(parents=True, exist_ok=True)
    aggregates = aggregate_summaries(summaries, records)
    document = {
        "schema_version": 1,
        "ledger_type": ledger_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "dataset": "C001-C020=100000 öre; M001-M005=0 öre",
            "payment_amount_ore": PAYMENT_AMOUNT,
            "sequential": True,
            "warm_up_payments_per_workload": WARM_UP_PAYMENTS,
            "warm_up_excluded": True,
            "reset_and_verification_excluded": True,
            "ledger_completion_boundary": (
                "successful PostgreSQL COMMIT"
                if ledger_name == "conventional"
                else "successful local Anvil transaction receipt"
            ),
            "api_measurement": "in-process ASGI request/response around the same payment",
            "p95_method": "nearest-rank ceil(0.95*n)",
            "aggregation": (
                "latencies and gas pooled across valid transaction records; "
                "throughput summarized across valid measured runs"
            ),
        },
        "runs": list(summaries),
        "aggregates": aggregates,
    }
    (directory / "benchmark_results.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (directory / "per_transaction_results.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for record in records:
            handle.write(json.dumps(record.evidence_dict(), sort_keys=True) + "\n")
    with (directory / "benchmark_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "row_type": "measured_run",
                    "ledger_type": ledger_name,
                    "workload_size": summary["workload_size"],
                    "run_number": summary["run_number"],
                    "attempt_count": summary["attempt_count"],
                    "success_count": summary["success_count"],
                    "failure_count": summary["failure_count"],
                    "average_ledger_latency_ms": summary["ledger_latency_ms"]["average"],
                    "median_ledger_latency_ms": summary["ledger_latency_ms"]["median"],
                    "p95_ledger_latency_ms": summary["ledger_latency_ms"]["p95"],
                    "average_api_end_to_end_latency_ms": summary["api_end_to_end_latency_ms"]["average"],
                    "median_api_end_to_end_latency_ms": summary["api_end_to_end_latency_ms"]["median"],
                    "p95_api_end_to_end_latency_ms": summary["api_end_to_end_latency_ms"]["p95"],
                    "average_submission_latency_ms": summary["submission_latency_ms"]["average"],
                    "median_submission_latency_ms": summary["submission_latency_ms"]["median"],
                    "p95_submission_latency_ms": summary["submission_latency_ms"]["p95"],
                    "average_confirmation_latency_ms": summary["confirmation_latency_ms"]["average"],
                    "median_confirmation_latency_ms": summary["confirmation_latency_ms"]["median"],
                    "p95_confirmation_latency_ms": summary["confirmation_latency_ms"]["p95"],
                    "throughput_payments_per_second": summary["throughput_payments_per_second"],
                    "average_successful_gas_used": summary["successful_gas_used"]["average"],
                    "median_successful_gas_used": summary["successful_gas_used"]["median"],
                    "average_failed_or_reverted_gas_used": summary["failed_or_reverted_gas_used"]["average"],
                    "median_failed_or_reverted_gas_used": summary["failed_or_reverted_gas_used"]["median"],
                    "balances_correct": summary["balances_correct"],
                    "replay_correct": summary["replay_correct"],
                    "transaction_linkage_correct": summary["transaction_linkage_correct"],
                    "valid": summary["valid"],
                    "exclusion_reason": summary["exclusion_reason"],
                }
            )
        for aggregate in aggregates:
            writer.writerow(
                {
                    "row_type": "workload_aggregate",
                    "ledger_type": ledger_name,
                    "workload_size": aggregate["workload_size"],
                    "run_number": "ALL",
                    "attempt_count": sum(
                        int(item["attempt_count"])
                        for item in summaries
                        if item["workload_size"] == aggregate["workload_size"]
                    ),
                    "success_count": aggregate["success_count"],
                    "failure_count": aggregate["failure_count"],
                    "average_ledger_latency_ms": aggregate["ledger_latency_ms"]["average"],
                    "median_ledger_latency_ms": aggregate["ledger_latency_ms"]["median"],
                    "p95_ledger_latency_ms": aggregate["ledger_latency_ms"]["p95"],
                    "average_api_end_to_end_latency_ms": aggregate["api_end_to_end_latency_ms"]["average"],
                    "median_api_end_to_end_latency_ms": aggregate["api_end_to_end_latency_ms"]["median"],
                    "p95_api_end_to_end_latency_ms": aggregate["api_end_to_end_latency_ms"]["p95"],
                    "average_submission_latency_ms": aggregate["submission_latency_ms"]["average"],
                    "median_submission_latency_ms": aggregate["submission_latency_ms"]["median"],
                    "p95_submission_latency_ms": aggregate["submission_latency_ms"]["p95"],
                    "average_confirmation_latency_ms": aggregate["confirmation_latency_ms"]["average"],
                    "median_confirmation_latency_ms": aggregate["confirmation_latency_ms"]["median"],
                    "p95_confirmation_latency_ms": aggregate["confirmation_latency_ms"]["p95"],
                    "throughput_payments_per_second": aggregate["throughput_payments_per_second"]["average"],
                    "average_successful_gas_used": aggregate["successful_gas_used"]["average"],
                    "median_successful_gas_used": aggregate["successful_gas_used"]["median"],
                    "average_failed_or_reverted_gas_used": aggregate["failed_or_reverted_gas_used"]["average"],
                    "median_failed_or_reverted_gas_used": aggregate["failed_or_reverted_gas_used"]["median"],
                    "balances_correct": aggregate["all_balances_correct"],
                    "replay_correct": aggregate["all_replays_correct"],
                    "transaction_linkage_correct": aggregate["all_transaction_linkage_correct"],
                    "valid": aggregate["invalid_run_count"] == 0,
                    "exclusion_reason": "",
                }
            )


async def run_environment(
    environment: ConventionalEnvironment | BlockchainEnvironment,
    workloads: Sequence[int],
    measured_runs: int,
    *,
    checkpoint: Callable[
        [Sequence[Measurement], Sequence[Mapping[str, Any]]], None
    ] | None = None,
) -> tuple[list[Measurement], list[dict[str, Any]], dict[tuple[int, int], NormalizedRun]]:
    records: list[Measurement] = []
    summaries: list[dict[str, Any]] = []
    normalized: dict[tuple[int, int], NormalizedRun] = {}
    for workload_size in workloads:
        warm_up_ledger = environment.reset(workload_size, 0)
        verify_initial_state(warm_up_ledger)
        await execute_warm_up(environment.ledger_name, warm_up_ledger, workload_size)
        for run_number in range(1, measured_runs + 1):
            ledger = environment.reset(workload_size, run_number)
            verify_initial_state(ledger)
            try:
                run_records, summary, normalized_run = await execute_measured_run(
                    environment.ledger_name,
                    ledger,
                    workload_size,
                    run_number,
                    metadata=environment.metadata,
                )
            except Exception as error:
                # A measured-run failure remains visible and invalid; reset safety
                # failures above are intentionally not caught.
                run_records = []
                summary = {
                    "ledger_type": environment.ledger_name,
                    "workload_size": workload_size,
                    "run_number": run_number,
                    "attempt_count": 0,
                    "success_count": 0,
                    "failure_count": 1,
                    "ledger_latency_ms": _statistics([]),
                    "api_end_to_end_latency_ms": _statistics([]),
                    "submission_latency_ms": _statistics([]),
                    "confirmation_latency_ms": _statistics([]),
                    "throughput_payments_per_second": None,
                    "measured_duration_seconds": None,
                    "successful_gas_used": _statistics([]),
                    "successful_gas_count": 0,
                    "failed_or_reverted_gas_used": _statistics([]),
                    "failed_or_reverted_gas_count": 0,
                    "balances_correct": False,
                    "replay_correct": False,
                    "transaction_linkage_correct": False,
                    "no_partial_transfer": False,
                    "valid": False,
                    "exclusion_reason": (
                        f"measured run raised {type(error).__name__}: {error}"
                    ),
                }
            else:
                normalized[(workload_size, run_number)] = normalized_run
            records.extend(run_records)
            summaries.append(summary)
            if checkpoint is not None:
                checkpoint(records, summaries)
            print(
                f"C08 {environment.ledger_name} workload={workload_size} "
                f"run={run_number} valid={summary['valid']}",
                flush=True,
            )
    return records, summaries, normalized


class LocalAnvil:
    """Ephemeral verified local Anvil with runtime-only test identities."""

    def __enter__(self):
        EthereumAccount.enable_unaudited_hdwallet_features()
        _, mnemonic = EthereumAccount.create_with_mnemonic()
        self.accounts = tuple(
            EthereumAccount.from_mnemonic(
                mnemonic, account_path=f"m/44'/60'/0'/0/{index}"
            )
            for index in range(26)
        )
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        anvil = shutil.which("anvil") or str(Path.home() / ".foundry/bin/anvil")
        self.process = subprocess.Popen(
            [
                anvil,
                "--silent",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--chain-id",
                str(LOCAL_ANVIL_CHAIN_ID),
                "--mnemonic",
                mnemonic,
                "--accounts",
                "26",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            rpc_url = _validated_local_anvil_rpc_url(f"http://127.0.0.1:{port}")
            self.web3 = Web3(HTTPProvider(rpc_url))
            for _ in range(200):
                if self.web3.is_connected():
                    break
                if self.process.poll() is not None:
                    raise RuntimeError(
                        f"Anvil exited early: {self.process.stderr.read()}"
                    )
                time.sleep(0.05)
            else:
                raise RuntimeError("local Anvil did not become ready")
            _validated_local_anvil_connection(self.web3)
            return self
        except BaseException:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
            raise

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.process.terminate()
        self.process.wait(timeout=5)


async def run_benchmark(
    output_root: Path,
    workloads: Sequence[int] = WORKLOADS,
    measured_runs: int = MEASURED_RUNS,
) -> dict[str, Any]:
    raw_dsn = os.environ.get(
        "UPI_TEST_DATABASE_DSN",
        "postgresql://upi@127.0.0.1:55432/upi_payment_test",
    )
    validated_benchmark_dsn(raw_dsn)
    conventional = ConventionalEnvironment(raw_dsn)
    conventional_records, conventional_summaries, conventional_normalized = (
        await run_environment(
            conventional,
            workloads,
            measured_runs,
            checkpoint=lambda records, summaries: write_ledger_evidence(
                output_root, "conventional", records, summaries
            ),
        )
    )
    write_ledger_evidence(
        output_root,
        "conventional",
        conventional_records,
        conventional_summaries,
    )

    with LocalAnvil() as node:
        participant_keys = {
            owner: node.accounts[index + 1].key.hex()
            for index, owner in enumerate((*CUSTOMERS, *MERCHANTS))
        }
        blockchain = BlockchainEnvironment(
            raw_dsn,
            node.web3,
            node.accounts[0].key.hex(),
            participant_keys,
        )
        blockchain_records, blockchain_summaries, blockchain_normalized = (
            await run_environment(
                blockchain,
                workloads,
                measured_runs,
                checkpoint=lambda records, summaries: write_ledger_evidence(
                    output_root, "blockchain", records, summaries
                ),
            )
        )
    write_ledger_evidence(
        output_root,
        "blockchain",
        blockchain_records,
        blockchain_summaries,
    )
    comparison = apply_run_validity(
        differential_result(
            conventional_normalized,
            blockchain_normalized,
            conventional_records=conventional_records,
            blockchain_records=blockchain_records,
        ),
        conventional_summaries,
        blockchain_summaries,
    )
    (output_root / "differential_results.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local C08 benchmark")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/benchmarks"),
    )
    parser.add_argument(
        "--workloads",
        type=int,
        nargs="+",
        default=list(WORKLOADS),
    )
    parser.add_argument("--runs", type=int, default=MEASURED_RUNS)
    arguments = parser.parse_args()
    if arguments.runs <= 0 or any(size <= 0 for size in arguments.workloads):
        raise SystemExit("workloads and run count must be positive")
    comparison = asyncio.run(
        run_benchmark(arguments.output, arguments.workloads, arguments.runs)
    )
    if comparison["comparison"] != "PASS":
        raise SystemExit("C08 benchmark validation failed; evidence was retained")


if __name__ == "__main__":
    main()
