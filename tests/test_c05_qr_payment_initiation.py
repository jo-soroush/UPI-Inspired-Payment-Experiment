from __future__ import annotations

import ast
from datetime import datetime, timezone
import inspect
import os

import httpx
import psycopg
import pytest
import zxingcpp

from upi_payment_experiment import qr as qr_module
from upi_payment_experiment.api import create_app
from upi_payment_experiment.conventional_ledger import ConventionalLedger
from upi_payment_experiment.payment_service import PaymentService
from upi_payment_experiment.qr import (
    InvalidQrPayloadError,
    QrDecodingError,
    build_merchant_qr_payload,
    decode_merchant_qr,
    generate_merchant_qr,
    parse_merchant_qr_payload,
)


TEST_DSN = os.environ.get(
    "UPI_TEST_DATABASE_DSN",
    "postgresql://upi@127.0.0.1:55432/upi_payment_test",
)
PAYMENT_TIME = datetime(2026, 1, 3, 12, 0, tzinfo=timezone.utc)
CANONICAL_PAYLOAD = "upi-demo://pay?merchant_id=M001"


@pytest.fixture
def payment_ledger() -> ConventionalLedger:
    ledger = ConventionalLedger(
        TEST_DSN,
        transaction_id_factory=lambda: "TX-C05-001",
        clock=lambda: PAYMENT_TIME,
    )
    ledger.initialize_schema()
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
    return ledger


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


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


def payment_payload(merchant_id: str) -> dict[str, object]:
    return {
        "payment_id": "PAY-C05-001",
        "payer_id": "C001",
        "merchant_id": merchant_id,
        "amount": 10000,
        "currency": "SEK",
        "idempotency_key": "IDEM-C05-001",
    }


def test_real_qr_generation_and_decode_round_trip_uses_zxingcpp() -> None:
    image = generate_merchant_qr("M001")
    image_view = memoryview(image)

    assert image_view.ndim == 2
    assert image_view.nbytes > 0

    decoded_barcode = zxingcpp.read_barcode(
        image,
        formats=zxingcpp.BarcodeFormat.QRCode,
        is_pure=True,
    )
    assert decoded_barcode is not None
    assert decoded_barcode.format == zxingcpp.BarcodeFormat.QRCode
    assert decoded_barcode.text == CANONICAL_PAYLOAD
    assert decode_merchant_qr(image) == "M001"


def test_canonical_payload_contains_only_merchant_identity() -> None:
    payload = build_merchant_qr_payload("M001")

    assert payload == CANONICAL_PAYLOAD
    for excluded_field in (
        "amount",
        "payer_id",
        "payment_id",
        "idempotency_key",
        "status",
        "transaction_id",
        "ledger",
        "persistence",
    ):
        assert excluded_field not in payload


@pytest.mark.parametrize(
    "payload",
    (
        "not-a-uri",
        "https://pay?merchant_id=M001",
        "UPI-DEMO://pay?merchant_id=M001",
        "upi-demo://merchant?merchant_id=M001",
        "upi-demo://pay/path?merchant_id=M001",
        "upi-demo://pay",
        "upi-demo://pay?merchant_id=",
        "upi-demo://pay?merchant_id=%20",
        "upi-demo://pay?merchant_id=M001&merchant_id=M002",
        "upi-demo://pay?merchant_id=M001&amount=10000",
        "upi-demo://pay?merchant_id=M001#fragment",
        "upi-demo://pay?merchant_id=%ZZ",
        '{"merchant_id":"M001"}',
    ),
)
def test_noncanonical_payloads_are_rejected(payload: str) -> None:
    with pytest.raises(InvalidQrPayloadError) as error:
        parse_merchant_qr_payload(payload)

    assert error.value.code == "INVALID_QR_PAYLOAD"


@pytest.mark.parametrize(
    "payload",
    (
        "upi-demo://pa\ty?merchant_id=M001",
        "upi-demo://pa\ny?merchant_id=M001",
        "upi-demo://pa\ry?merchant_id=M001",
        "upi\t-demo://pay?merchant_id=M001",
        "upi-demo://pay?merchant\t_id=M001",
        "upi-demo://pay?merchant_id=M0\t01",
    ),
)
def test_raw_ascii_control_characters_are_rejected_before_uri_normalization(
    payload: str,
) -> None:
    with pytest.raises(InvalidQrPayloadError) as error:
        parse_merchant_qr_payload(payload)

    assert error.value.code == "INVALID_QR_PAYLOAD"


def test_empty_fragment_delimiter_is_rejected_before_uri_parsing() -> None:
    with pytest.raises(InvalidQrPayloadError) as error:
        parse_merchant_qr_payload("upi-demo://pay?merchant_id=M001#")

    assert error.value.code == "INVALID_QR_PAYLOAD"


@pytest.mark.parametrize(
    "payload",
    (
        "upi-demo://pay?merchant_id=M001#abc",
        "upi-demo://pay?merchant_id=M001#fragment",
    ),
)
def test_nonempty_fragment_is_rejected(payload: str) -> None:
    with pytest.raises(InvalidQrPayloadError) as error:
        parse_merchant_qr_payload(payload)

    assert error.value.code == "INVALID_QR_PAYLOAD"


def test_percent_encoded_hash_is_merchant_data_not_a_raw_fragment_delimiter() -> None:
    assert parse_merchant_qr_payload(
        "upi-demo://pay?merchant_id=M%23001"
    ) == "M#001"


def test_empty_fragment_regression_would_resolve_without_raw_delimiter_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qr_module, "_has_raw_fragment_delimiter", lambda _: False)

    assert parse_merchant_qr_payload("upi-demo://pay?merchant_id=M001#") == "M001"


@pytest.mark.parametrize(
    "payload",
    (
        "upi-demo://pay?merchant_id=%C3%28",
        "upi-demo://pay?merchant_id=%C3",
        "upi-demo://pay?merchant_id=%",
        "upi-demo://pay?merchant_id=%0",
        "upi-demo://pay?merchant_id=%GG",
        "upi-demo://pay?merchant_id=%00",
        "upi-demo://pay?merchant_id=%09",
        "upi-demo://pay?merchant_id=%0A",
        "upi-demo://pay?merchant_id=%0D",
        "upi-demo://pay?merchant_id=%1F",
        "upi-demo://pay?merchant_id=%7F",
        "upi-demo://pay?merchant%00_id=M001",
    ),
)
def test_malformed_or_control_character_percent_decoding_is_rejected(
    payload: str,
) -> None:
    with pytest.raises(InvalidQrPayloadError) as error:
        parse_merchant_qr_payload(payload)

    assert error.value.code == "INVALID_QR_PAYLOAD"


def test_canonical_and_valid_utf8_percent_encoded_merchant_ids_are_accepted() -> None:
    assert parse_merchant_qr_payload(CANONICAL_PAYLOAD) == "M001"
    assert parse_merchant_qr_payload(
        "upi-demo://pay?merchant_id=M%C3%A5l"
    ) == "Mål"


def test_invalid_utf8_regression_would_fail_with_replacement_decoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strict_parse_qsl = qr_module.parse_qsl

    def replacement_parse_qsl(*args: object, **kwargs: object) -> list[tuple[str, str]]:
        kwargs["errors"] = "replace"
        return strict_parse_qsl(*args, **kwargs)

    monkeypatch.setattr(qr_module, "parse_qsl", replacement_parse_qsl)

    assert parse_merchant_qr_payload(
        "upi-demo://pay?merchant_id=%C3%28"
    ) == "�("


def test_decoded_control_regression_would_fail_without_decoded_control_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qr_module, "_has_ascii_control_character", lambda _: False)

    assert parse_merchant_qr_payload("upi-demo://pay?merchant_id=%00") == "\x00"


def test_malformed_percent_regression_would_fail_without_percent_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qr_module, "_has_invalid_percent_encoding", lambda _: False)

    assert parse_merchant_qr_payload("upi-demo://pay?merchant_id=%GG") == "%GG"


@pytest.mark.parametrize("merchant_id", ("", "   "))
def test_empty_merchant_id_cannot_be_encoded(merchant_id: str) -> None:
    with pytest.raises(InvalidQrPayloadError):
        build_merchant_qr_payload(merchant_id)


def test_decoder_failure_is_exposed_as_controlled_qr_error() -> None:
    with pytest.raises(QrDecodingError) as error:
        decode_merchant_qr(object())

    assert error.value.code == "QR_DECODING_FAILED"


@pytest.mark.anyio
async def test_unknown_decoded_merchant_uses_existing_c04_rejection(
    payment_ledger: ConventionalLedger,
) -> None:
    merchant_id = decode_merchant_qr(generate_merchant_qr("M404"))
    transport = httpx.ASGITransport(
        app=create_app(PaymentService(payment_ledger), clock=lambda: PAYMENT_TIME)
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/payments",
            json=payment_payload(merchant_id),
        )

    assert merchant_id == "M404"
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"
    assert database_state() == (100000, 0, 0, 0, 0)


@pytest.mark.anyio
async def test_valid_decoded_merchant_uses_existing_safe_payment_path(
    payment_ledger: ConventionalLedger,
) -> None:
    merchant_id = decode_merchant_qr(generate_merchant_qr("M001"))
    transport = httpx.ASGITransport(
        app=create_app(PaymentService(payment_ledger), clock=lambda: PAYMENT_TIME)
    )
    request = payment_payload(merchant_id)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        original = await client.post("/payments", json=request)
        replay = await client.post("/payments", json=request)

    assert merchant_id == "M001"
    assert original.status_code == 200
    assert original.json() == {
        "payment_id": "PAY-C05-001",
        "transaction_id": "TX-C05-001",
        "status": "SUCCESS",
    }
    assert replay.status_code == 200
    assert replay.json() == original.json()
    assert database_state() == (90000, 10000, 1, 1, 1)


def test_qr_module_is_isolated_from_payment_and_persistence_logic() -> None:
    source = inspect.getsource(qr_module)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots == {"urllib", "zxingcpp"}
    assert "create_barcode" in source
    assert "write_barcode(" not in source
    for forbidden in (
        "PaymentService",
        "ConventionalLedger",
        "psycopg",
        "payment_id",
        "idempotency_key",
        "request_fingerprint",
        "execute_payment",
    ):
        assert forbidden not in source
