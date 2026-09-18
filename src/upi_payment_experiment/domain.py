"""Ledger-independent domain models for the C02 payment experiment."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Final


SUPPORTED_CURRENCIES: Final[frozenset[str]] = frozenset({"SEK"})


class PaymentStatus(str, Enum):
    """C02 status vocabulary; transition behavior belongs to later Cards."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_positive_minor_units(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer minor-unit amount")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_non_negative_minor_units(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer minor-unit amount")
    if value < 0:
        raise ValueError(f"{field_name} must not be negative")


def _require_currency(currency: str) -> None:
    _require_text(currency, "currency")
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"unsupported currency: {currency}")


def _require_status(status: PaymentStatus) -> None:
    if not isinstance(status, PaymentStatus):
        raise TypeError("status must be a PaymentStatus")


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    payment_identity: str

    def __post_init__(self) -> None:
        _require_text(self.customer_id, "customer_id")
        _require_text(self.name, "name")
        _require_text(self.payment_identity, "payment_identity")


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    name: str
    payment_identity: str

    def __post_init__(self) -> None:
        _require_text(self.merchant_id, "merchant_id")
        _require_text(self.name, "name")
        _require_text(self.payment_identity, "payment_identity")


@dataclass(frozen=True)
class Account:
    account_id: str
    owner_id: str
    balance: int
    currency: str

    def __post_init__(self) -> None:
        _require_text(self.account_id, "account_id")
        _require_text(self.owner_id, "owner_id")
        _require_non_negative_minor_units(self.balance, "balance")
        _require_currency(self.currency)


@dataclass(frozen=True)
class Payment:
    payment_id: str
    payer_id: str
    merchant_id: str
    amount: int
    currency: str
    idempotency_key: str
    status: PaymentStatus
    created_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.payment_id, "payment_id")
        _require_text(self.payer_id, "payer_id")
        _require_text(self.merchant_id, "merchant_id")
        _require_positive_minor_units(self.amount, "amount")
        _require_currency(self.currency)
        _require_text(self.idempotency_key, "idempotency_key")
        _require_status(self.status)
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    payment_id: str
    ledger_type: str
    status: PaymentStatus
    timestamp: datetime

    def __post_init__(self) -> None:
        _require_text(self.transaction_id, "transaction_id")
        _require_text(self.payment_id, "payment_id")
        _require_text(self.ledger_type, "ledger_type")
        _require_status(self.status)
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime")


@dataclass(frozen=True)
class LedgerResult:
    payment_id: str
    transaction_id: str | None
    status: PaymentStatus

    def __post_init__(self) -> None:
        _require_text(self.payment_id, "payment_id")
        if self.transaction_id is not None:
            _require_text(self.transaction_id, "transaction_id")
        _require_status(self.status)
