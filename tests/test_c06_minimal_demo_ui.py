from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import struct
from urllib.parse import urlsplit
import zlib

import httpx
import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from upi_payment_experiment.api import create_app
from upi_payment_experiment.conventional_ledger import ConventionalLedger
from upi_payment_experiment import demo_bootstrap
from upi_payment_experiment.demo_bootstrap import (
    IMPLICIT_TARGET_ENVIRONMENT,
    _require_local_demo_target,
    _validated_demo_dsn,
    bootstrap_demo,
)
from upi_payment_experiment.domain import Payment, PaymentStatus
from upi_payment_experiment.payment_service import PaymentService
from upi_payment_experiment.qr import decode_merchant_qr


_C06_TEST_DATABASE_NAME = "upi_payment_test"
_C06_TEST_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def _validated_c06_test_dsn(raw_dsn: str) -> str:
    """Require one explicit loopback test target before this module uses PostgreSQL."""

    if any(os.environ.get(name) for name in IMPLICIT_TARGET_ENVIRONMENT):
        raise ValueError(
            "C06 tests do not allow implicit libpq database target environment"
        )
    if not isinstance(raw_dsn, str) or not raw_dsn.strip():
        raise ValueError("C06 test database DSN must be a non-empty PostgreSQL URI")

    parsed = urlsplit(raw_dsn)
    if parsed.scheme != "postgresql" or parsed.hostname not in _C06_TEST_LOCAL_HOSTS:
        raise ValueError(
            "C06 tests require an explicit postgresql loopback database host"
        )
    parameters = conninfo_to_dict(raw_dsn)
    if (
        parameters.get("host") not in _C06_TEST_LOCAL_HOSTS
        or parameters.get("hostaddr") not in (None, "")
    ):
        raise ValueError(
            "C06 tests are restricted to the explicit local upi_payment_test database"
        )
    validated_dsn = _validated_demo_dsn(raw_dsn)
    if conninfo_to_dict(validated_dsn).get("dbname") != _C06_TEST_DATABASE_NAME:
        raise ValueError(
            "C06 tests are restricted to the explicit local upi_payment_test database"
        )
    return validated_dsn


TEST_DSN = _validated_c06_test_dsn(
    os.environ.get(
        "UPI_TEST_DATABASE_DSN",
        "postgresql://upi@127.0.0.1:55432/upi_payment_test",
    )
)
PAYMENT_TIME = datetime(2026, 1, 4, 12, 0, tzinfo=timezone.utc)
TRANSACTION_TIME = datetime(2026, 1, 4, 12, 0, 1, tzinfo=timezone.utc)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="module")
def ledger() -> ConventionalLedger:
    return ConventionalLedger(
        TEST_DSN,
        transaction_id_factory=lambda: "TX-C06-001",
        clock=lambda: TRANSACTION_TIME,
    )


@pytest.fixture(autouse=True)
def reset_demo(ledger: ConventionalLedger) -> None:
    bootstrap_demo(TEST_DSN)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def app(ledger: ConventionalLedger):
    return create_app(PaymentService(ledger), clock=lambda: PAYMENT_TIME)


def payment_payload() -> dict[str, object]:
    return {
        "payment_id": "PAY-C06-001",
        "payer_id": "C001",
        "merchant_id": "M001",
        "amount": 10000,
        "currency": "SEK",
        "idempotency_key": "IDEM-C06-001",
    }


def _decode_grayscale_png(png: bytes) -> memoryview:
    assert png.startswith(PNG_SIGNATURE)
    offset = len(PNG_SIGNATURE)
    width = height = 0
    compressed = bytearray()
    while offset < len(png):
        length = struct.unpack(">I", png[offset : offset + 4])[0]
        chunk_type = png[offset + 4 : offset + 8]
        chunk_data = png[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", chunk_data)
            )
            assert (depth, color, compression, filtering, interlace) == (
                8,
                0,
                0,
                0,
                0,
            )
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    decoded = zlib.decompress(compressed)
    stride = width + 1
    assert len(decoded) == stride * height
    rows = []
    for start in range(0, len(decoded), stride):
        assert decoded[start] == 0
        rows.append(decoded[start + 1 : start + stride])
    return memoryview(b"".join(rows)).cast("B", shape=[height, width])


def test_demo_bootstrap_recreates_only_the_canonical_fixture() -> None:
    stale_service = PaymentService(
        ConventionalLedger(
            TEST_DSN,
            transaction_id_factory=lambda: "TX-STALE",
            clock=lambda: TRANSACTION_TIME,
        )
    )
    stale_service.execute_payment(
        Payment(
            payment_id="PAY-STALE",
            payer_id="C001",
            merchant_id="M001",
            amount=1,
            currency="SEK",
            idempotency_key="IDEM-STALE",
            status=PaymentStatus.PENDING,
            created_at=PAYMENT_TIME,
        )
    )

    bootstrap_demo(TEST_DSN)

    with psycopg.connect(TEST_DSN) as connection:
        accounts = connection.execute(
            "SELECT owner_id, balance FROM accounts ORDER BY owner_id"
        ).fetchall()
        counts = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("payments", "transactions", "idempotency_records")
        )
    assert accounts == [("C001", 100000), ("M001", 0)]
    assert counts == (0, 0, 0)


def test_c06_test_dsn_guard_accepts_only_the_explicit_loopback_target() -> None:
    parameters = conninfo_to_dict(
        _validated_c06_test_dsn(
            "postgresql://upi@127.0.0.1:55432/upi_payment_test"
        )
    )

    assert parameters["host"] == "127.0.0.1"
    assert parameters["dbname"] == "upi_payment_test"
    assert parameters.get("hostaddr") in (None, "")
    assert parameters.get("service") in (None, "")


@pytest.mark.parametrize(
    "dsn",
    (
        "postgresql://upi@example.com:55432/upi_payment_test",
        "postgresql://upi@203.0.113.10:55432/upi_payment_test",
        "postgresql://upi@localhost:55432/upi_payment_test?hostaddr=127.0.0.1",
        "postgresql://upi@localhost:55432/upi_payment_test?service=remote",
        "postgresql://upi@127.0.0.1:55432/other_database",
        "postgresql:///upi_payment_test",
    ),
)
def test_c06_test_dsn_guard_rejects_unsafe_targets_before_database_activity(
    monkeypatch: pytest.MonkeyPatch, dsn: str
) -> None:
    connection_attempts = 0

    def forbid_connection(*args: object, **kwargs: object) -> None:
        nonlocal connection_attempts
        connection_attempts += 1
        raise AssertionError("test DSN validation must run before database activity")

    monkeypatch.setattr(psycopg, "connect", forbid_connection)

    with pytest.raises(ValueError):
        _validated_c06_test_dsn(dsn)

    assert connection_attempts == 0


@pytest.mark.parametrize(
    ("environment_name", "value"),
    (
        ("PGHOST", "203.0.113.10"),
        ("PGHOSTADDR", "203.0.113.10"),
        ("PGSERVICE", "remote-service"),
        ("PGSERVICEFILE", "/tmp/remote-service.conf"),
    ),
)
def test_c06_test_dsn_guard_rejects_implicit_target_environment(
    monkeypatch: pytest.MonkeyPatch, environment_name: str, value: str
) -> None:
    monkeypatch.setenv(environment_name, value)

    with pytest.raises(ValueError, match="implicit libpq"):
        _validated_c06_test_dsn(
            "postgresql://upi@127.0.0.1:55432/upi_payment_test"
        )


@pytest.mark.parametrize(
    "dsn",
    (
        "dbname=upi_payment_test host=localhost hostaddr=203.0.113.10",
        "dbname=upi_payment_test hostaddr=203.0.113.10",
        "postgresql://upi@example.com/upi_payment_test",
        "dbname=production host=localhost",
        "service=myservice dbname=upi_payment_test",
        "service=myservice dbname=upi_payment_test host=localhost",
    ),
)
def test_demo_bootstrap_guard_rejects_remote_or_non_demo_targets(dsn: str) -> None:
    with pytest.raises(ValueError, match="restricted"):
        _require_local_demo_target(dsn)


@pytest.mark.parametrize(
    "dsn",
    (
        "dbname=upi_payment_test host=localhost",
        "dbname=upi_payment_test host=127.0.0.1",
        "dbname=upi_payment_test hostaddr=127.0.0.1",
        "dbname=upi_payment_test hostaddr=::1",
        "dbname=upi_payment_test host=postgres",
    ),
)
def test_demo_bootstrap_guard_allows_approved_local_targets(dsn: str) -> None:
    _require_local_demo_target(dsn)


def test_bootstrap_uses_an_explicit_local_target_without_libpq_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_dsns: list[str] = []

    class FakeCursor:
        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def executemany(self, *_: object) -> None:
            return None

    class FakeConnection:
        def __enter__(self) -> FakeConnection:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, *_: object) -> None:
            return None

        def cursor(self) -> FakeCursor:
            return FakeCursor()

    class FakeLedger:
        def __init__(self, dsn: str) -> None:
            assert os.environ.get("PGHOST") is None
            assert os.environ.get("PGHOSTADDR") is None
            assert os.environ.get("PGSERVICE") is None
            assert os.environ.get("PGSERVICEFILE") is None
            captured_dsns.append(dsn)

        def initialize_schema(self) -> None:
            return None

    def record_clear(dsn: str) -> None:
        assert os.environ.get("PGHOST") is None
        assert os.environ.get("PGHOSTADDR") is None
        assert os.environ.get("PGSERVICE") is None
        assert os.environ.get("PGSERVICEFILE") is None
        captured_dsns.append(dsn)

    def record_connect(dsn: str) -> FakeConnection:
        assert os.environ.get("PGHOST") is None
        assert os.environ.get("PGHOSTADDR") is None
        assert os.environ.get("PGSERVICE") is None
        assert os.environ.get("PGSERVICEFILE") is None
        captured_dsns.append(dsn)
        return FakeConnection()

    monkeypatch.setenv("PGHOST", "203.0.113.10")
    monkeypatch.setenv("PGHOSTADDR", "203.0.113.10")
    monkeypatch.setenv("PGSERVICE", "remote-service")
    monkeypatch.setenv("PGSERVICEFILE", "/tmp/remote-service.conf")
    monkeypatch.setattr(demo_bootstrap, "_clear_existing_demo_state", record_clear)
    monkeypatch.setattr(demo_bootstrap, "ConventionalLedger", FakeLedger)
    monkeypatch.setattr(demo_bootstrap.psycopg, "connect", record_connect)

    bootstrap_demo("dbname=upi_payment_test user=upi")

    assert len(captured_dsns) == 3
    for connection_dsn in captured_dsns:
        parameters = conninfo_to_dict(connection_dsn)
        assert parameters["dbname"] == "upi_payment_test"
        assert parameters["host"] == "localhost"
        assert "hostaddr" not in parameters
        assert "service" not in parameters
    assert conninfo_to_dict(_validated_demo_dsn("dbname=upi_payment_test"))["host"] == "localhost"
    assert os.environ["PGHOST"] == "203.0.113.10"
    assert os.environ["PGHOSTADDR"] == "203.0.113.10"
    assert os.environ["PGSERVICE"] == "remote-service"
    assert os.environ["PGSERVICEFILE"] == "/tmp/remote-service.conf"


@pytest.mark.anyio
async def test_balance_history_qr_and_static_routes(
    ledger: ConventionalLedger,
) -> None:
    transport = httpx.ASGITransport(app=app(ledger))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        customer = await client.get("/accounts/C001/balance")
        merchant = await client.get("/accounts/M001/balance")
        history = await client.get("/transactions")
        qr = await client.get("/merchants/M001/qr")
        root = await client.get("/")
        script = await client.get("/static/app.js")
        stylesheet = await client.get("/static/styles.css")

    assert customer.json() == {
        "owner_id": "C001",
        "currency": "SEK",
        "balance_ore": 100000,
    }
    assert merchant.json() == {
        "owner_id": "M001",
        "currency": "SEK",
        "balance_ore": 0,
    }
    assert history.json() == {"transactions": []}
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert decode_merchant_qr(_decode_grayscale_png(qr.content)) == "M001"
    assert root.status_code == 200
    assert "UPI-Inspired Payment Prototype" in root.text
    assert 'id="ledger-blockchain"' in root.text
    assert "Local API request time" in root.text
    assert script.status_code == 200
    assert "crypto.randomUUID" in script.text
    assert stylesheet.status_code == 200


@pytest.mark.anyio
async def test_read_routes_preserve_backend_account_validation(
    ledger: ConventionalLedger,
) -> None:
    transport = httpx.ASGITransport(app=app(ledger))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        balance = await client.get("/accounts/C404/balance")
        qr = await client.get("/merchants/M404/qr")

    assert balance.status_code == 404
    assert balance.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"
    assert qr.status_code == 404
    assert qr.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"


@pytest.mark.anyio
async def test_conventional_demo_flow_uses_existing_payment_boundary(
    ledger: ConventionalLedger,
) -> None:
    transport = httpx.ASGITransport(app=app(ledger))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        before_customer = await client.get("/accounts/C001/balance")
        before_merchant = await client.get("/accounts/M001/balance")
        qr = await client.get("/merchants/M001/qr")
        payment = await client.post("/payments", json=payment_payload())
        replay = await client.post("/payments", json=payment_payload())
        after_customer = await client.get("/accounts/C001/balance")
        after_merchant = await client.get("/accounts/M001/balance")
        history = await client.get("/transactions")

    assert before_customer.json()["balance_ore"] == 100000
    assert before_merchant.json()["balance_ore"] == 0
    assert decode_merchant_qr(_decode_grayscale_png(qr.content)) == "M001"
    assert payment.json() == {
        "payment_id": "PAY-C06-001",
        "transaction_id": "TX-C06-001",
        "status": "SUCCESS",
    }
    assert replay.json() == payment.json()
    assert after_customer.json()["balance_ore"] == 90000
    assert after_merchant.json()["balance_ore"] == 10000
    assert history.json() == {
        "transactions": [
            {
                "transaction_id": "TX-C06-001",
                "payment_id": "PAY-C06-001",
                "ledger_type": "ConventionalLedger",
                "status": "SUCCESS",
                "timestamp": "2026-01-04T12:00:01Z",
            }
        ]
    }


def test_c06_frontend_keeps_payment_and_qr_authority_in_backend() -> None:
    root = Path(__file__).resolve().parents[1]
    app_source = (root / "frontend/app.ts").read_text(encoding="utf-8")
    html = (
        root / "src/upi_payment_experiment/static/index.html"
    ).read_text(encoding="utf-8")

    assert "/payments?${ledgerQuery(ledger)}" in app_source
    assert "request_fingerprint" not in app_source
    assert "canonical" not in app_source.lower()
    assert "generate_merchant_qr" not in app_source
    assert "ledger: selectedLedger()" not in app_source
    assert 'id="merchant-qr"' in html
    assert 'id="ledger-conventional"' in html
    assert 'id="ledger-blockchain"' in html
    for forbidden in ("web3", "solidity", "private_key", "wallet"):
        assert forbidden not in app_source.lower()
