from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

import psycopg
import pytest

from upi_payment_experiment.conventional_ledger import ConventionalLedger
from upi_payment_experiment.domain import Payment, PaymentStatus
from upi_payment_experiment.payment_service import PaymentService


TEST_DSN = os.environ.get(
    "UPI_TEST_DATABASE_DSN",
    "postgresql://upi@127.0.0.1:55432/upi_payment_test",
)
PAYMENT_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
TRANSACTION_TIME = datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc)


class ControlledRollbackError(RuntimeError):
    """Deterministic failure used only for the C03 rollback proof."""


class RollbackProofLedger(ConventionalLedger):
    def _after_payer_debit(self) -> None:
        raise ControlledRollbackError("controlled failure after payer debit")


@pytest.fixture(scope="module")
def ledger() -> ConventionalLedger:
    conventional_ledger = ConventionalLedger(TEST_DSN)
    conventional_ledger.initialize_schema()
    return conventional_ledger


@pytest.fixture(autouse=True)
def reset_database(ledger: ConventionalLedger) -> None:
    with psycopg.connect(TEST_DSN) as connection:
        connection.execute("TRUNCATE transactions, payments, accounts")
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO accounts (account_id, owner_id, currency, balance)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    ("ACC-C001", "C001", "SEK", 100000),
                    ("ACC-M001", "M001", "SEK", 0),
                ),
            )


def payment() -> Payment:
    return Payment(
        payment_id="PAY-C03-001",
        payer_id="C001",
        merchant_id="M001",
        amount=10000,
        currency="SEK",
        idempotency_key="OPAQUE-C03-001",
        status=PaymentStatus.PENDING,
        created_at=PAYMENT_TIME,
    )


def persisted_counts(payment_id: str) -> tuple[int, int]:
    with psycopg.connect(TEST_DSN) as connection:
        payment_count = connection.execute(
            "SELECT count(*) FROM payments WHERE payment_id = %s",
            (payment_id,),
        ).fetchone()[0]
        transaction_count = connection.execute(
            "SELECT count(*) FROM transactions WHERE payment_id = %s",
            (payment_id,),
        ).fetchone()[0]
    return payment_count, transaction_count


def test_successful_atomic_transfer_persists_and_is_retrievable(
    ledger: ConventionalLedger,
) -> None:
    service = PaymentService(
        ConventionalLedger(
            TEST_DSN,
            transaction_id_factory=lambda: "TX-C03-001",
            clock=lambda: TRANSACTION_TIME,
        )
    )
    initial_payer = ledger.get_balance("C001")
    initial_merchant = ledger.get_balance("M001")

    result = service.execute_payment(payment())

    final_payer = ledger.get_balance("C001")
    final_merchant = ledger.get_balance("M001")
    stored_payment = ledger.get_payment("PAY-C03-001")
    stored_transaction = ledger.get_transaction("TX-C03-001")
    history = ledger.list_transactions(payment_id="PAY-C03-001")

    assert (initial_payer, initial_merchant) == (100000, 0)
    assert (final_payer, final_merchant) == (90000, 10000)
    assert final_payer - initial_payer == -10000
    assert final_merchant - initial_merchant == 10000
    assert initial_payer + initial_merchant == final_payer + final_merchant
    assert result.payment_id == "PAY-C03-001"
    assert result.transaction_id == "TX-C03-001"
    assert result.status is PaymentStatus.SUCCESS
    assert stored_payment is not None
    assert stored_payment.status is PaymentStatus.SUCCESS
    assert stored_payment.amount == 10000
    assert stored_payment.idempotency_key == "OPAQUE-C03-001"
    assert stored_transaction is not None
    assert stored_transaction.status is PaymentStatus.SUCCESS
    assert stored_transaction.payment_id == stored_payment.payment_id
    assert history == [stored_transaction]
    assert persisted_counts("PAY-C03-001") == (1, 1)


def test_controlled_failure_rolls_back_all_state() -> None:
    failing_ledger = RollbackProofLedger(
        TEST_DSN,
        transaction_id_factory=lambda: "TX-C03-ROLLBACK",
        clock=lambda: TRANSACTION_TIME,
    )

    with pytest.raises(ControlledRollbackError):
        PaymentService(failing_ledger).execute_payment(payment())

    fresh_ledger = ConventionalLedger(TEST_DSN)
    assert fresh_ledger.get_balance("C001") == 100000
    assert fresh_ledger.get_balance("M001") == 0
    assert fresh_ledger.get_payment("PAY-C03-001") is None
    assert fresh_ledger.get_transaction("TX-C03-ROLLBACK") is None
    assert fresh_ledger.list_transactions(payment_id="PAY-C03-001") == []
    assert persisted_counts("PAY-C03-001") == (0, 0)


def test_postgresql_details_are_confined_to_the_adapter() -> None:
    root = Path(__file__).resolve().parents[1]
    ledger_interface = (root / "src/upi_payment_experiment/ledger.py").read_text()
    payment_service = (
        root / "src/upi_payment_experiment/payment_service.py"
    ).read_text()
    conventional_adapter = (
        root / "src/upi_payment_experiment/conventional_ledger.py"
    ).read_text()

    assert "psycopg" not in ledger_interface.lower()
    assert "postgres" not in ledger_interface.lower()
    assert "psycopg" not in payment_service.lower()
    assert "postgres" not in payment_service.lower()
    assert "psycopg" in conventional_adapter.lower()
    assert "postgres" in conventional_adapter.lower()
