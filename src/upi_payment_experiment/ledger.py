"""Ledger-neutral interface shared by payment application services."""

from hashlib import sha256
import json
from typing import Protocol

from .domain import LedgerResult, Payment, Transaction


def canonical_payment_fingerprint(payment: Payment) -> str:
    """Hash exactly the immutable C04 canonical payment payload."""

    payload = {
        "amount": payment.amount,
        "currency": payment.currency,
        "merchant_id": payment.merchant_id,
        "payer_id": payment.payer_id,
        "payment_id": payment.payment_id,
    }
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_json.encode("utf-8")).hexdigest()


class LedgerInterface(Protocol):
    """Technology-neutral operations required by the payment flow."""

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        """Return an owner's balance in integer minor units."""

    def execute_payment(
        self, payment: Payment, *, request_fingerprint: str
    ) -> LedgerResult:
        """Execute and persist one payment."""

    def get_payment(self, payment_id: str) -> Payment | None:
        """Return a persisted payment when it exists."""

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Return a persisted ledger transaction when it exists."""

    def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
        """Return transaction history, optionally for one payment."""
