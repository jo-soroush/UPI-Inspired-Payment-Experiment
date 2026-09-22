from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import asyncio

import psycopg
import pytest
from web3 import HTTPProvider, Web3

from upi_payment_experiment.benchmark import (
    CUSTOMERS,
    INITIAL_CUSTOMER_BALANCE,
    INITIAL_MERCHANT_BALANCE,
    MERCHANTS,
    BlockchainEnvironment,
    LocalAnvil,
    Measurement,
    NormalizedRun,
    TimedLedger,
    benchmark_accounts,
    differential_result,
    apply_run_validity,
    execute_measured_run,
    execute_warm_up,
    execution_workload,
    expected_balances,
    logical_workload,
    normalize_run,
    reset_benchmark_database,
    summarize_run,
    validated_benchmark_dsn,
    verify_initial_state,
    write_ledger_evidence,
)
from upi_payment_experiment.domain import LedgerResult, Payment, PaymentStatus, Transaction


RAW_TEST_DSN = os.environ.get(
    "UPI_TEST_DATABASE_DSN",
    "postgresql://upi@127.0.0.1:55432/upi_payment_test",
)
TEST_DSN = validated_benchmark_dsn(RAW_TEST_DSN)
NOW = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)


class FakeLedger:
    ledger_type = "FakeLedger"

    def __init__(self) -> None:
        self.balances = {
            **{owner: INITIAL_CUSTOMER_BALANCE for owner in CUSTOMERS},
            **{owner: INITIAL_MERCHANT_BALANCE for owner in MERCHANTS},
        }
        self.results: dict[str, LedgerResult] = {}
        self.transactions: list[Transaction] = []
        self.active = 0
        self.maximum_active = 0
        self.executions = 0

    def execute_payment(
        self, payment: Payment, *, request_fingerprint: str
    ) -> LedgerResult:
        assert request_fingerprint
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        try:
            existing = self.results.get(payment.payment_id)
            if existing is not None:
                return existing
            self.executions += 1
            self.balances[payment.payer_id] -= payment.amount
            self.balances[payment.merchant_id] += payment.amount
            result = LedgerResult(
                payment.payment_id,
                f"TX-{payment.payment_id}",
                PaymentStatus.SUCCESS,
            )
            self.results[payment.payment_id] = result
            self.transactions.append(
                Transaction(
                    result.transaction_id,
                    payment.payment_id,
                    self.ledger_type,
                    PaymentStatus.SUCCESS,
                    NOW,
                )
            )
            return result
        finally:
            self.active -= 1

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        assert currency == "SEK"
        return self.balances[owner_id]

    def get_payment(self, payment_id: str) -> Payment | None:
        return None

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        return next(
            (item for item in self.transactions if item.transaction_id == transaction_id),
            None,
        )

    def list_transactions(
        self, payment_id: str | None = None
    ) -> list[Transaction]:
        if payment_id is None:
            return list(self.transactions)
        return [item for item in self.transactions if item.payment_id == payment_id]


class IncrementingClock:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self) -> int:
        self.value += 1_000_000
        return self.value


def measurement(
    *,
    ledger: str = "conventional",
    index: int = 1,
    status: str = "SUCCESS",
    success_gas: int | None = None,
    failed_gas: int | None = None,
) -> Measurement:
    return Measurement(
        ledger_type=ledger,
        workload_size=1,
        run_number=1,
        logical_index=index,
        timestamp=NOW.isoformat(),
        payment_id=f"PAY-{ledger}-{index}",
        idempotency_key=f"IDEM-{ledger}-{index}",
        payer_id="C001",
        merchant_id="M001",
        amount=1_000,
        currency="SEK",
        ledger_latency_ms=2.0,
        api_end_to_end_latency_ms=3.0,
        status=status,
        transaction_id=f"TX-{ledger}-{index}",
        successful_gas_used_if_applicable=success_gas,
        failed_or_reverted_gas_used_if_applicable=failed_gas,
    )


def test_workload_is_deterministic_reproducible_and_balance_feasible() -> None:
    first = logical_workload(1_000)
    second = logical_workload(1_000)

    assert first == second
    assert len(first) == 1_000
    assert first[0].payer_id == "C001"
    assert first[19].payer_id == "C020"
    assert first[20].payer_id == "C001"
    balances = expected_balances(first)
    assert all(balances[owner] == 50_000 for owner in CUSTOMERS)
    assert all(balances[owner] == 200_000 for owner in MERCHANTS)
    assert sum(balances.values()) == 2_000_000


def test_execution_identifiers_are_unique_scoped_and_logically_equivalent() -> None:
    conventional = execution_workload("conventional", 1_000, 3)
    blockchain = execution_workload("blockchain", 1_000, 3)

    assert [item.logical for item in conventional] == [
        item.logical for item in blockchain
    ]
    identifiers = {
        item.payment_id for item in (*conventional, *blockchain)
    } | {item.idempotency_key for item in (*conventional, *blockchain)}
    assert len(identifiers) == 4_000
    assert conventional[0].payment_id == "C08-CONVENTIONAL-W1000-R03-P0001"
    assert blockchain[0].payment_id == "C08-BLOCKCHAIN-W1000-R03-P0001"


def test_fixture_has_exactly_twenty_customers_and_five_merchants() -> None:
    accounts = benchmark_accounts()
    assert len(accounts) == 25
    assert accounts[:20] == tuple(
        (f"ACC-{owner}", owner, "SEK", 100_000) for owner in CUSTOMERS
    )
    assert accounts[20:] == tuple(
        (f"ACC-{owner}", owner, "SEK", 0) for owner in MERCHANTS
    )


def test_benchmark_dsn_rejects_unsafe_targets_before_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        monkeypatch.delenv(name, raising=False)
    unsafe = (
        "postgresql://upi@db.example.com:5432/upi_payment_test",
        "postgresql://upi@127.0.0.1:55432/production",
        "postgresql://upi@127.0.0.1:55432/upi_payment_test?hostaddr=8.8.8.8",
        "postgresql://upi@127.0.0.1:55432/upi_payment_test?service=remote",
        "postgresql:///upi_payment_test",
    )
    for dsn in unsafe:
        with pytest.raises(ValueError):
            validated_benchmark_dsn(dsn)
    connection_calls = 0

    def unexpected_connect(*_args: object, **_kwargs: object) -> None:
        nonlocal connection_calls
        connection_calls += 1

    monkeypatch.setattr(
        "upi_payment_experiment.benchmark.psycopg.connect", unexpected_connect
    )
    with pytest.raises(ValueError):
        reset_benchmark_database(unsafe[0])
    assert connection_calls == 0
    monkeypatch.setenv("PGHOST", "db.example.com")
    with pytest.raises(ValueError):
        validated_benchmark_dsn(RAW_TEST_DSN)


def test_blockchain_environment_rejects_non_loopback_provider_before_rpc() -> None:
    remote = Web3(HTTPProvider("https://rpc.example.com"))
    with pytest.raises(ValueError, match="loopback"):
        BlockchainEnvironment(RAW_TEST_DSN, remote, "unused", {})


def test_conventional_reset_restores_exact_fixture() -> None:
    reset_benchmark_database(RAW_TEST_DSN)
    with psycopg.connect(TEST_DSN) as connection:
        rows = connection.execute(
            "SELECT owner_id, balance FROM accounts ORDER BY owner_id"
        ).fetchall()
        counts = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "payments",
                "transactions",
                "idempotency_records",
                "blockchain_operations",
                "blockchain_idempotency_records",
            )
        )
    assert rows == sorted(
        [(owner, 100_000) for owner in CUSTOMERS]
        + [(owner, 0) for owner in MERCHANTS]
    )
    assert counts == (0, 0, 0, 0, 0)


def test_blockchain_reset_redeploys_full_on_chain_state() -> None:
    with LocalAnvil() as node:
        keys = {
            owner: node.accounts[index + 1].key.hex()
            for index, owner in enumerate((*CUSTOMERS, *MERCHANTS))
        }
        environment = BlockchainEnvironment(
            RAW_TEST_DSN, node.web3, node.accounts[0].key.hex(), keys
        )
        first = environment.reset(10, 1)
        first_address = first._contract.address
        verify_initial_state(first)
        candidate = execution_workload("blockchain", 10, 1)[0]
        payment = Payment(
            candidate.payment_id,
            candidate.logical.payer_id,
            candidate.logical.merchant_id,
            candidate.logical.amount,
            candidate.logical.currency,
            candidate.idempotency_key,
            PaymentStatus.PENDING,
            NOW,
        )
        from upi_payment_experiment.payment_service import PaymentService

        PaymentService(first).execute_payment(payment)
        assert first.get_balance("C001") == 99_000
        second = environment.reset(10, 2)
        assert second._contract.address != first_address
        verify_initial_state(second)
        assert not second._contract.functions.isProcessed(
            Web3.keccak(text=candidate.payment_id)
        ).call()
        with psycopg.connect(TEST_DSN) as connection:
            assert connection.execute(
                "SELECT count(*) FROM blockchain_operations"
            ).fetchone() == (0,)


def test_measured_run_is_sequential_replay_safe_and_balance_correct() -> None:
    ledger = FakeLedger()
    records, summary, _ = asyncio.run(
        execute_measured_run(
            "conventional",
            ledger,
            100,
            1,
            metadata=lambda _payment_id: {},
        )
    )

    assert len(records) == 100
    assert ledger.executions == 100
    assert ledger.maximum_active == 1
    assert summary["valid"] is True
    assert summary["balances_correct"] is True
    assert summary["replay_correct"] is True
    assert summary["transaction_linkage_correct"] is True
    assert ledger.balances == expected_balances(logical_workload(100))


def test_warm_up_is_discarded_and_timing_excludes_prior_setup() -> None:
    ledger = FakeLedger()
    asyncio.run(execute_warm_up("conventional", ledger, 10))
    assert ledger.executions == 3

    measured_ledger = FakeLedger()
    clock = IncrementingClock()
    records, summary, _ = asyncio.run(
        execute_measured_run(
            "conventional",
            measured_ledger,
            10,
            1,
            metadata=lambda _payment_id: {},
            clock_ns=clock,
        )
    )
    assert len(records) == 10
    assert summary["attempt_count"] == 10
    assert summary["measured_duration_seconds"] == pytest.approx(0.041)
    assert all(record.ledger_latency_ms == 1.0 for record in records)
    assert all(record.api_end_to_end_latency_ms == 3.0 for record in records)


def test_timed_ledger_boundary_wraps_only_ledger_execution() -> None:
    ledger = FakeLedger()
    timed = TimedLedger(ledger, clock_ns=IncrementingClock())
    candidate = execution_workload("conventional", 1, 1)[0]
    payment = Payment(
        candidate.payment_id,
        candidate.logical.payer_id,
        candidate.logical.merchant_id,
        candidate.logical.amount,
        candidate.logical.currency,
        candidate.idempotency_key,
        PaymentStatus.PENDING,
        NOW,
    )
    timed.execute_payment(payment, request_fingerprint="fingerprint")
    assert timed.take_latency_ms(candidate.payment_id) == 1.0


def test_successful_and_failed_gas_populations_stay_separate() -> None:
    records = [
        measurement(ledger="blockchain", index=1, success_gas=40_000),
        measurement(
            ledger="blockchain", index=2, status="FAILED", failed_gas=31_000
        ),
    ]
    summary = summarize_run(
        records,
        1.0,
        balances_correct=False,
        replay_correct=False,
        transaction_linkage_correct=True,
        no_partial_transfer=True,
        valid=False,
        exclusion_reason="controlled failure",
    )
    assert summary["successful_gas_count"] == 1
    assert summary["successful_gas_used"]["average"] == 40_000
    assert summary["failed_or_reverted_gas_count"] == 1
    assert summary["failed_or_reverted_gas_used"]["average"] == 31_000


def test_evidence_schema_writers_and_failed_run_preservation(tmp_path: Path) -> None:
    record = measurement()
    summary = summarize_run(
        [record],
        0.1,
        balances_correct=False,
        replay_correct=True,
        transaction_linkage_correct=True,
        no_partial_transfer=True,
        valid=False,
        exclusion_reason="final balance mismatch",
    )
    write_ledger_evidence(tmp_path, "conventional", [record], [summary])

    document = json.loads(
        (tmp_path / "conventional/benchmark_results.json").read_text()
    )
    raw = json.loads(
        (tmp_path / "conventional/per_transaction_results.jsonl").read_text()
    )
    csv_text = (tmp_path / "conventional/benchmark_results.csv").read_text()
    required = {
        "ledger_type",
        "workload_size",
        "run_number",
        "timestamp",
        "payment_id",
        "ledger_latency_ms",
        "api_end_to_end_latency_ms",
        "status",
    }
    assert required <= raw.keys()
    assert document["runs"][0]["valid"] is False
    assert document["runs"][0]["exclusion_reason"] == "final balance mismatch"
    assert document["aggregates"][0]["invalid_run_count"] == 1
    assert "final balance mismatch" in csv_text


def test_normalization_excludes_implementation_identity_timing_and_gas() -> None:
    conventional_record = measurement(ledger="conventional")
    blockchain_record = replace(
        conventional_record,
        ledger_type="blockchain",
        payment_id="PAY-blockchain-1",
        idempotency_key="IDEM-blockchain-1",
        transaction_id="0xabc",
        ledger_latency_ms=999.0,
        api_end_to_end_latency_ms=1_000.0,
        successful_gas_used_if_applicable=42_000,
    )
    balances = expected_balances(logical_workload(1))
    left = normalize_run(
        [conventional_record],
        balances,
        {conventional_record.payment_id},
        True,
        True,
        True,
    )
    right = normalize_run(
        [blockchain_record],
        balances,
        {blockchain_record.payment_id},
        True,
        True,
        True,
    )
    assert left == right
    assert "transaction_id" not in left.__dataclass_fields__
    assert "ledger_latency_ms" not in left.__dataclass_fields__
    assert "gas" not in left.__dataclass_fields__


def test_differential_mismatch_is_retained_and_fails_comparison() -> None:
    valid = NormalizedRun(
        1,
        1,
        ("SUCCESS",),
        (("C001", -1_000),),
        (("M001", 1_000),),
        (1,),
        True,
        True,
        True,
    )
    mismatch = replace(valid, statuses=("FAILED",))
    conventional_record = measurement(ledger="conventional")
    blockchain_record = measurement(ledger="blockchain")
    result = differential_result(
        {(1, 1): valid},
        {(1, 1): mismatch},
        conventional_records=[conventional_record],
        blockchain_records=[blockchain_record],
    )
    assert result["comparison"] == "FAIL"
    assert result["mismatch_count"] == 1
    assert result["mismatches"][0]["logical_workload"]
    assert result["mismatches"][0]["conventional_normalized"]["statuses"] == (
        "SUCCESS",
    )
    assert result["mismatches"][0]["conventional_raw_outcomes"][0][
        "payment_id"
    ] == conventional_record.payment_id
    assert result["mismatches"][0]["blockchain_raw_outcomes"][0][
        "payment_id"
    ] == blockchain_record.payment_id


def test_differential_invariants_pass_for_equivalent_normalized_runs() -> None:
    run = NormalizedRun(
        10,
        1,
        ("SUCCESS",) * 10,
        tuple((owner, -1_000 if int(owner[1:]) <= 10 else 0) for owner in CUSTOMERS),
        tuple((owner, 2_000) for owner in MERCHANTS),
        tuple(range(1, 11)),
        True,
        True,
        True,
    )
    result = differential_result({(10, 1): run}, {(10, 1): run})
    assert result["comparison"] == "PASS"
    assert result["mismatch_count"] == 0


def test_equal_invalid_runs_cannot_produce_an_overall_false_pass() -> None:
    comparison = {
        "comparison": "PASS",
        "compared_run_count": 1,
        "mismatch_count": 0,
        "mismatches": [],
    }
    invalid = {
        "workload_size": 10,
        "run_number": 1,
        "valid": False,
        "exclusion_reason": "equal controlled failure",
    }
    result = apply_run_validity(comparison, [invalid], [invalid])
    assert result["comparison"] == "FAIL"
    assert result["invalid_run_count"] == 2
    assert {item["ledger_type"] for item in result["invalid_runs"]} == {
        "conventional",
        "blockchain",
    }
