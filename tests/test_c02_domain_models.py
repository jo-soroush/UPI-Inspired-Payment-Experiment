from datetime import datetime, timezone
from pathlib import Path

import pytest

from upi_payment_experiment.domain import (
    Account,
    Customer,
    LedgerResult,
    Merchant,
    Payment,
    PaymentStatus,
    Transaction,
)


TIMESTAMP = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_valid_domain_objects_can_be_created() -> None:
    customer = Customer("C001", "Customer One", "customer:C001")
    merchant = Merchant("M001", "Merchant One", "merchant:M001")
    account = Account("A001", customer.customer_id, 100000, "SEK")
    payment = Payment(
        "PAY-001",
        customer.customer_id,
        merchant.merchant_id,
        10000,
        "SEK",
        "REQ-001",
        PaymentStatus.PENDING,
        TIMESTAMP,
    )
    transaction = Transaction(
        "TX-001", payment.payment_id, "ConventionalLedger", PaymentStatus.PENDING, TIMESTAMP
    )
    result = LedgerResult(payment.payment_id, transaction.transaction_id, PaymentStatus.PENDING)

    assert customer.customer_id == "C001"
    assert merchant.merchant_id == "M001"
    assert account.balance == 100000
    assert payment.created_at == TIMESTAMP
    assert transaction.timestamp == TIMESTAMP
    assert result.payment_id == payment.payment_id


def test_payment_status_vocabulary_is_exact() -> None:
    assert {status.value for status in PaymentStatus} == {
        "PENDING",
        "SUCCESS",
        "FAILED",
        "UNKNOWN",
    }


@pytest.mark.parametrize("amount", [0, -1, 1.5, True])
def test_payment_amount_requires_positive_integer_minor_units(amount: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Payment("PAY-001", "C001", "M001", amount, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)


def test_account_balance_requires_non_negative_integer_minor_units() -> None:
    with pytest.raises((TypeError, ValueError)):
        Account("A001", "C001", -1, "SEK")
    with pytest.raises(TypeError):
        Account("A001", "C001", 100.5, "SEK")
    with pytest.raises(TypeError):
        Account("A001", "C001", True, "SEK")


def test_supported_currency_is_required() -> None:
    Account("A001", "C001", 100000, "SEK")

    with pytest.raises(ValueError):
        Account("A001", "C001", 100000, "EUR")


def test_payment_currency_is_validated_directly() -> None:
    Payment("PAY-001", "C001", "M001", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)

    with pytest.raises(ValueError):
        Payment("PAY-001", "C001", "M001", 10000, "EUR", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)


def test_required_identifiers_are_non_empty() -> None:
    with pytest.raises(ValueError):
        Customer("", "Customer One", "customer:C001")
    with pytest.raises(ValueError):
        Customer("C001", "Customer One", "")
    with pytest.raises(ValueError):
        Merchant("", "Merchant One", "merchant:M001")
    with pytest.raises(ValueError):
        Merchant("M001", "Merchant One", "")
    with pytest.raises(ValueError):
        Account("", "C001", 100000, "SEK")
    with pytest.raises(ValueError):
        Account("A001", "", 100000, "SEK")
    with pytest.raises(ValueError):
        Payment("", "C001", "M001", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Payment("PAY-001", "", "M001", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Payment("PAY-001", "C001", "", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Payment("PAY-001", "C001", "M001", 10000, "SEK", "", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Transaction("", "PAY-001", "ConventionalLedger", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Transaction("TX-001", "", "ConventionalLedger", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        Transaction("TX-001", "PAY-001", "", PaymentStatus.PENDING, TIMESTAMP)
    with pytest.raises(ValueError):
        LedgerResult("", "TX-001", PaymentStatus.PENDING)
    with pytest.raises(ValueError):
        LedgerResult("PAY-001", "", PaymentStatus.PENDING)


def test_payment_status_is_validated_for_each_status_bearing_model() -> None:
    with pytest.raises(TypeError):
        Payment("PAY-001", "C001", "M001", 10000, "SEK", "REQ-001", "PENDING", TIMESTAMP)
    with pytest.raises(TypeError):
        Transaction("TX-001", "PAY-001", "ConventionalLedger", "SUCCESS", TIMESTAMP)
    with pytest.raises(TypeError):
        LedgerResult("PAY-001", "TX-001", "FAILED")


def test_timestamps_require_explicit_datetime_values() -> None:
    with pytest.raises(TypeError):
        Payment("PAY-001", "C001", "M001", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, "now")
    with pytest.raises(TypeError):
        Transaction("TX-001", "PAY-001", "ConventionalLedger", PaymentStatus.PENDING, "now")


def test_payment_and_transaction_identifiers_remain_distinct() -> None:
    payment = Payment("PAY-001", "C001", "M001", 10000, "SEK", "REQ-001", PaymentStatus.PENDING, TIMESTAMP)
    transaction = Transaction("TX-001", payment.payment_id, "BlockchainLedger", PaymentStatus.SUCCESS, TIMESTAMP)

    assert payment.payment_id != transaction.transaction_id
    assert payment.payment_id == transaction.payment_id
    assert payment.idempotency_key == "REQ-001"


def test_unknown_ledger_result_can_lack_execution_identity() -> None:
    result = LedgerResult("PAY-002", None, PaymentStatus.UNKNOWN)

    assert result.payment_id == "PAY-002"
    assert result.transaction_id is None


def test_status_requires_payment_status_enum() -> None:
    with pytest.raises(TypeError):
        Payment("PAY-001", "C001", "M001", 10000, "SEK", "REQ-001", "SUCCESS", TIMESTAMP)


def test_domain_module_has_no_ledger_or_framework_coupling() -> None:
    source = Path("src/upi_payment_experiment/domain.py").read_text()
    forbidden = ("sqlalchemy", "postgresql", "web3", "solidity", "anvil", "fastapi", "HTTPException")

    assert not any(term in source.lower() for term in forbidden)
