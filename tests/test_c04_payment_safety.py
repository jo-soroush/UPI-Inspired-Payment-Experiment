from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from threading import Event
import time
from types import SimpleNamespace

import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from upi_payment_experiment.api import create_app
from upi_payment_experiment.conventional_ledger import ConventionalLedger
from upi_payment_experiment.domain import Payment, PaymentStatus
from upi_payment_experiment.errors import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    PaymentConflictError,
)
from upi_payment_experiment.payment_service import (
    PaymentService,
    canonical_payment_fingerprint,
)


TEST_DSN = os.environ.get(
    "UPI_TEST_DATABASE_DSN",
    "postgresql://upi@127.0.0.1:55432/upi_payment_test",
)
PAYMENT_TIME = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
TRANSACTION_TIME = datetime(2026, 1, 2, 12, 0, 1, tzinfo=timezone.utc)


class ControlledPersistenceError(RuntimeError):
    """Deterministic failure after Payment persistence but before completion."""


class PersistenceFailureLedger(ConventionalLedger):
    def _after_payment_persisted(self) -> None:
        raise ControlledPersistenceError("controlled failure after Payment insert")


class TransferCountingLedger(ConventionalLedger):
    """Observe whether a request reaches the transfer path."""

    transfer_attempts = 0

    def _after_payer_debit(self) -> None:
        self.transfer_attempts += 1


class PausingIdentityLockLedger(ConventionalLedger):
    """Pause after PostgreSQL request locks are held."""

    def __init__(self, dsn: str, entered: Event, release: Event) -> None:
        super().__init__(
            dsn,
            transaction_id_factory=lambda: "TX-C04-CONCURRENT",
            clock=lambda: TRANSACTION_TIME,
        )
        self._entered = entered
        self._release = release

    def _after_request_identity_locks(self) -> None:
        self._entered.set()
        if not self._release.wait(timeout=5):
            raise RuntimeError("timed out waiting to release request locks")


@pytest.fixture(scope="module")
def ledger() -> ConventionalLedger:
    conventional_ledger = ConventionalLedger(TEST_DSN)
    conventional_ledger.initialize_schema()
    return conventional_ledger


@pytest.fixture(autouse=True)
def reset_database(ledger: ConventionalLedger) -> None:
    with psycopg.connect(TEST_DSN) as connection:
        connection.execute(
            "TRUNCATE idempotency_records, transactions, payments, accounts"
        )
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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def payment(
    *,
    payment_id: str = "PAY-C04-001",
    payer_id: str = "C001",
    merchant_id: str = "M001",
    amount: int = 10000,
    idempotency_key: str = "IDEM-C04-001",
    created_at: datetime = PAYMENT_TIME,
) -> Payment:
    return Payment(
        payment_id=payment_id,
        payer_id=payer_id,
        merchant_id=merchant_id,
        amount=amount,
        currency="SEK",
        idempotency_key=idempotency_key,
        status=PaymentStatus.PENDING,
        created_at=created_at,
    )


def service(*, transaction_id: str = "TX-C04-001") -> PaymentService:
    return PaymentService(
        ConventionalLedger(
            TEST_DSN,
            transaction_id_factory=lambda: transaction_id,
            clock=lambda: TRANSACTION_TIME,
        )
    )


def counting_service() -> tuple[PaymentService, TransferCountingLedger]:
    ledger = TransferCountingLedger(
        TEST_DSN,
        transaction_id_factory=lambda: "TX-C04-COUNTED",
        clock=lambda: TRANSACTION_TIME,
    )
    return PaymentService(ledger), ledger


def database_state() -> tuple[int, int, int, int, int]:
    with psycopg.connect(TEST_DSN) as connection:
        payer = connection.execute(
            "SELECT balance FROM accounts WHERE owner_id = 'C001'"
        ).fetchone()[0]
        merchant = connection.execute(
            "SELECT balance FROM accounts WHERE owner_id = 'M001'"
        ).fetchone()[0]
        payments = connection.execute("SELECT count(*) FROM payments").fetchone()[0]
        transactions = connection.execute(
            "SELECT count(*) FROM transactions"
        ).fetchone()[0]
        idempotency = connection.execute(
            "SELECT count(*) FROM idempotency_records"
        ).fetchone()[0]
    return payer, merchant, payments, transactions, idempotency


def api_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "payment_id": "PAY-C04-API",
        "payer_id": "C001",
        "merchant_id": "M001",
        "amount": 10000,
        "currency": "SEK",
        "idempotency_key": "IDEM-C04-API",
    }
    payload.update(overrides)
    return payload


def test_canonical_fingerprint_uses_only_approved_immutable_payload() -> None:
    original = payment()
    original_fingerprint = canonical_payment_fingerprint(original)
    currency_fields = original.__dict__.copy()
    currency_fields["currency"] = "NOK"
    included_variants = {
        "payment_id": payment(payment_id="PAY-C04-OTHER"),
        "payer_id": payment(payer_id="C002"),
        "merchant_id": payment(merchant_id="M002"),
        "amount": payment(amount=10001),
        "currency": SimpleNamespace(**currency_fields),
    }
    for field_name, variant in included_variants.items():
        assert canonical_payment_fingerprint(variant) != original_fingerprint, field_name

    excluded_variants = {
        "idempotency_key": payment(idempotency_key="A-DIFFERENT-REQUEST-KEY"),
        "timestamp": payment(created_at=PAYMENT_TIME + timedelta(days=1)),
        "status": Payment(
            payment_id=original.payment_id,
            payer_id=original.payer_id,
            merchant_id=original.merchant_id,
            amount=original.amount,
            currency=original.currency,
            idempotency_key=original.idempotency_key,
            status=PaymentStatus.SUCCESS,
            created_at=original.created_at,
        ),
        "transport_metadata": SimpleNamespace(
            **original.__dict__,
            transaction_id="TX-NOT-CANONICAL",
            http_metadata={"request_id": "HTTP-NOT-CANONICAL"},
        ),
    }
    for field_name, variant in excluded_variants.items():
        assert canonical_payment_fingerprint(variant) == original_fingerprint, field_name


def test_successful_c03_flow_still_commits_one_consistent_payment() -> None:
    result = service().execute_payment(payment())

    assert result.payment_id == "PAY-C04-001"
    assert result.transaction_id == "TX-C04-001"
    assert result.status is PaymentStatus.SUCCESS
    assert database_state() == (90000, 10000, 1, 1, 1)
    stored_payment = ConventionalLedger(TEST_DSN).get_payment(result.payment_id)
    history = ConventionalLedger(TEST_DSN).list_transactions(result.payment_id)
    assert stored_payment is not None
    assert stored_payment.status is PaymentStatus.SUCCESS
    assert len(history) == 1
    assert history[0].transaction_id == result.transaction_id
    assert history[0].status is PaymentStatus.SUCCESS


@pytest.mark.parametrize(
    ("attempt", "error_type"),
    (
        (payment(amount=100001), InsufficientFundsError),
        (payment(payer_id="C404"), AccountNotFoundError),
        (payment(merchant_id="M404"), AccountNotFoundError),
    ),
)
def test_rejected_ledger_requests_leave_no_state(
    attempt: Payment,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        service().execute_payment(attempt)

    assert database_state() == (100000, 0, 0, 0, 0)


@pytest.mark.parametrize("amount", (0, -1))
@pytest.mark.anyio
async def test_zero_and_negative_amounts_are_rejected_before_ledger_execution(
    amount: int,
) -> None:
    transport = httpx.ASGITransport(
        app=create_app(service(), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post("/payments", json=api_payload(amount=amount))

    assert response.status_code == 422
    assert database_state() == (100000, 0, 0, 0, 0)


@pytest.mark.anyio
async def test_malformed_api_request_is_rejected_without_persistence() -> None:
    malformed = api_payload()
    del malformed["merchant_id"]
    transport = httpx.ASGITransport(
        app=create_app(service(), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post("/payments", json=malformed)

    assert response.status_code == 422
    assert database_state() == (100000, 0, 0, 0, 0)


def test_same_idempotency_key_and_payload_returns_original_result() -> None:
    payment_service, counting_ledger = counting_service()
    original = payment_service.execute_payment(payment())
    replay = payment_service.execute_payment(
        payment(created_at=PAYMENT_TIME + timedelta(seconds=10))
    )

    assert replay == original
    assert counting_ledger.transfer_attempts == 1
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_same_idempotency_key_with_different_payload_conflicts() -> None:
    payment_service, counting_ledger = counting_service()
    payment_service.execute_payment(payment())

    with pytest.raises(IdempotencyConflictError) as error:
        payment_service.execute_payment(payment(payment_id="PAY-C04-OTHER"))

    assert error.value.code == "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"
    assert counting_ledger.transfer_attempts == 1
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_duplicate_payment_id_with_same_payload_returns_original_result() -> None:
    payment_service, counting_ledger = counting_service()
    original = payment_service.execute_payment(payment())
    replay = payment_service.execute_payment(
        payment(
            idempotency_key="IDEM-C04-ALIAS",
            created_at=PAYMENT_TIME + timedelta(seconds=10),
        )
    )

    assert replay == original
    assert counting_ledger.transfer_attempts == 1
    assert database_state() == (90000, 10000, 1, 1, 2)


def test_duplicate_payment_id_with_different_payload_conflicts() -> None:
    payment_service, counting_ledger = counting_service()
    payment_service.execute_payment(payment())

    with pytest.raises(PaymentConflictError) as error:
        payment_service.execute_payment(
            payment(amount=5000, idempotency_key="IDEM-C04-OTHER")
        )

    assert error.value.code == "PAYMENT_ID_REUSED_WITH_DIFFERENT_REQUEST"
    assert counting_ledger.transfer_attempts == 1
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_already_completed_payment_returns_committed_result() -> None:
    payment_service = service()
    original = payment_service.execute_payment(payment())
    assert ConventionalLedger(TEST_DSN).get_payment(original.payment_id).status is (
        PaymentStatus.SUCCESS
    )

    completed_replay = payment_service.execute_payment(payment())

    assert completed_replay == original
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_controlled_persistence_failure_rolls_back_and_allows_retry() -> None:
    failing_service = PaymentService(
        PersistenceFailureLedger(
            TEST_DSN,
            transaction_id_factory=lambda: "TX-C04-FAILED",
            clock=lambda: TRANSACTION_TIME,
        )
    )

    with pytest.raises(ControlledPersistenceError):
        failing_service.execute_payment(payment())

    assert database_state() == (100000, 0, 0, 0, 0)
    retry = service(transaction_id="TX-C04-RETRY").execute_payment(payment())
    assert retry.transaction_id == "TX-C04-RETRY"
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_concurrent_same_key_requests_create_one_execution() -> None:
    first_holds_locks = Event()
    release_first = Event()
    second_started = Event()
    application_name = "c04-deterministic-concurrency"
    second_dsn = make_conninfo(TEST_DSN, application_name=application_name)
    first_service = PaymentService(
        PausingIdentityLockLedger(TEST_DSN, first_holds_locks, release_first)
    )
    second_service = PaymentService(
        ConventionalLedger(
            second_dsn,
            transaction_id_factory=lambda: "TX-C04-SECOND",
            clock=lambda: TRANSACTION_TIME,
        )
    )

    def execute_second() -> object:
        second_started.set()
        return second_service.execute_payment(payment())

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(first_service.execute_payment, payment())
        assert first_holds_locks.wait(timeout=5)
        second_future = executor.submit(execute_second)
        assert second_started.wait(timeout=5)

        deadline = time.monotonic() + 5
        second_is_waiting_on_lock = False
        while time.monotonic() < deadline:
            with psycopg.connect(TEST_DSN) as connection:
                second_is_waiting_on_lock = connection.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_stat_activity
                        WHERE application_name = %s
                          AND state = 'active'
                          AND wait_event_type = 'Lock'
                    )
                    """,
                    (application_name,),
                ).fetchone()[0]
            if second_is_waiting_on_lock:
                break
            time.sleep(0.01)

        assert second_is_waiting_on_lock
        assert not second_future.done()
        release_first.set()
        results = [first_future.result(timeout=5), second_future.result(timeout=5)]

    assert results[0] == results[1]
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_c03_completed_payment_is_migrated_idempotently() -> None:
    schema_name = "c04_legacy_migration_test"
    with psycopg.connect(TEST_DSN, autocommit=True) as admin:
        admin.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                sql.Identifier(schema_name)
            )
        )
        admin.execute(
            sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
        )

    legacy_dsn = make_conninfo(
        TEST_DSN,
        options=f"-c search_path={schema_name}",
    )
    try:
        with psycopg.connect(legacy_dsn) as connection:
            connection.execute(
                """
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    currency TEXT NOT NULL CHECK (currency = 'SEK'),
                    balance BIGINT NOT NULL CHECK (balance >= 0),
                    UNIQUE (owner_id, currency)
                );
                CREATE TABLE payments (
                    payment_id TEXT PRIMARY KEY,
                    payer_account_id TEXT NOT NULL REFERENCES accounts(account_id),
                    merchant_account_id TEXT NOT NULL REFERENCES accounts(account_id),
                    amount BIGINT NOT NULL CHECK (amount > 0),
                    currency TEXT NOT NULL CHECK (currency = 'SEK'),
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    payment_id TEXT NOT NULL UNIQUE REFERENCES payments(payment_id),
                    ledger_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO accounts VALUES
                    ('ACC-C001', 'C001', 'SEK', 90000),
                    ('ACC-M001', 'M001', 'SEK', 10000)
                """
            )
            connection.execute(
                """
                INSERT INTO payments VALUES (
                    'PAY-C03-LEGACY',
                    'ACC-C001',
                    'ACC-M001',
                    10000,
                    'SEK',
                    'IDEM-C03-LEGACY',
                    'SUCCESS',
                    %s
                )
                """,
                (PAYMENT_TIME,),
            )
            connection.execute(
                """
                INSERT INTO transactions VALUES (
                    'TX-C03-LEGACY',
                    'PAY-C03-LEGACY',
                    'ConventionalLedger',
                    'SUCCESS',
                    %s
                )
                """,
                (TRANSACTION_TIME,),
            )

        legacy_ledger = ConventionalLedger(legacy_dsn)
        legacy_ledger.initialize_schema()
        legacy_ledger.initialize_schema()
        legacy_payment = payment(
            payment_id="PAY-C03-LEGACY",
            idempotency_key="IDEM-C03-LEGACY",
        )
        replay = PaymentService(legacy_ledger).execute_payment(legacy_payment)
        assert replay.payment_id == "PAY-C03-LEGACY"
        assert replay.transaction_id == "TX-C03-LEGACY"
        assert replay.status is PaymentStatus.SUCCESS

        with pytest.raises(IdempotencyConflictError):
            PaymentService(legacy_ledger).execute_payment(
                payment(
                    payment_id="PAY-C04-DIFFERENT",
                    amount=5000,
                    idempotency_key="IDEM-C03-LEGACY",
                )
            )

        with psycopg.connect(legacy_dsn) as connection:
            assert connection.execute(
                "SELECT balance FROM accounts WHERE owner_id = 'C001'"
            ).fetchone()[0] == 90000
            assert connection.execute(
                "SELECT balance FROM accounts WHERE owner_id = 'M001'"
            ).fetchone()[0] == 10000
            assert connection.execute("SELECT count(*) FROM payments").fetchone()[0] == 1
            assert connection.execute(
                "SELECT count(*) FROM transactions"
            ).fetchone()[0] == 1
            assert connection.execute(
                "SELECT count(*) FROM idempotency_records"
            ).fetchone()[0] == 1
            migrated = connection.execute(
                """
                SELECT p.request_fingerprint, i.request_fingerprint, i.payment_id
                FROM payments AS p
                JOIN idempotency_records AS i
                    ON i.idempotency_key = p.idempotency_key
                WHERE p.payment_id = 'PAY-C03-LEGACY'
                """
            ).fetchone()
            assert migrated[0] is not None
            assert migrated == (
                canonical_payment_fingerprint(legacy_payment),
                canonical_payment_fingerprint(legacy_payment),
                "PAY-C03-LEGACY",
            )
    finally:
        with psycopg.connect(TEST_DSN, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema_name)
                )
            )


@pytest.mark.anyio
async def test_api_success_replay_and_idempotency_conflict_mapping() -> None:
    transport = httpx.ASGITransport(
        app=create_app(service(), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        original = await client.post("/payments", json=api_payload())
        replay = await client.post("/payments", json=api_payload())
        conflict = await client.post(
            "/payments", json=api_payload(payment_id="PAY-C04-API-OTHER")
        )

    assert original.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == original.json()
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == (
        "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"
    )
    assert database_state() == (90000, 10000, 1, 1, 1)


@pytest.mark.anyio
async def test_api_payment_id_conflict_mapping() -> None:
    transport = httpx.ASGITransport(
        app=create_app(service(), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        assert (await client.post("/payments", json=api_payload())).status_code == 200
        conflict = await client.post(
            "/payments",
            json=api_payload(amount=5000, idempotency_key="IDEM-C04-API-OTHER"),
        )

    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == (
        "PAYMENT_ID_REUSED_WITH_DIFFERENT_REQUEST"
    )
    assert database_state() == (90000, 10000, 1, 1, 1)


@pytest.mark.anyio
async def test_api_self_transfer_is_rejected_without_state_change() -> None:
    transport = httpx.ASGITransport(
        app=create_app(service(), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/payments",
            json=api_payload(merchant_id="C001"),
        )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_PAYMENT_REQUEST"
    assert database_state() == (100000, 0, 0, 0, 0)
