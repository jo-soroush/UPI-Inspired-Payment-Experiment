"""Shared application service for ledger-independent payment operations."""

from .domain import LedgerResult, Payment, Transaction
from .errors import InvalidPaymentError
from .ledger import LedgerInterface, canonical_payment_fingerprint


class PaymentService:
    """Coordinate the application flow without depending on ledger technology."""

    def __init__(self, ledger: LedgerInterface) -> None:
        self._ledger = ledger

    def execute_payment(self, payment: Payment) -> LedgerResult:
        """Execute a request using its immutable canonical payment identity."""

        if payment.payer_id == payment.merchant_id:
            raise InvalidPaymentError("payer and merchant must be different")
        return self._ledger.execute_payment(
            payment,
            request_fingerprint=canonical_payment_fingerprint(payment),
        )

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        """Return a balance through the ledger-neutral application boundary."""

        return self._ledger.get_balance(owner_id, currency)

    def list_transactions(self) -> list[Transaction]:
        """Return the small demo's deterministic transaction history."""

        return self._ledger.list_transactions()
