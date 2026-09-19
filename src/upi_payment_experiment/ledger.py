"""Ledger-neutral interface shared by payment application services."""

from typing import Protocol

from .domain import LedgerResult, Payment, Transaction


class LedgerInterface(Protocol):
    """Technology-neutral operations required by the payment flow."""

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        """Return an owner's balance in integer minor units."""

    def execute_payment(self, payment: Payment) -> LedgerResult:
        """Execute and persist one payment."""

    def get_payment(self, payment_id: str) -> Payment | None:
        """Return a persisted payment when it exists."""

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Return a persisted ledger transaction when it exists."""

    def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
        """Return transaction history, optionally for one payment."""
