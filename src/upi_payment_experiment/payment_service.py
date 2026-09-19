"""Shared application service for ledger-independent payment execution."""

from .domain import LedgerResult, Payment
from .ledger import LedgerInterface


class PaymentService:
    """Coordinate the application flow without depending on ledger technology."""

    def __init__(self, ledger: LedgerInterface) -> None:
        self._ledger = ledger

    def execute_payment(self, payment: Payment) -> LedgerResult:
        """Delegate a validated domain payment to the configured ledger."""

        return self._ledger.execute_payment(payment)
