"""Shared application service for ledger-independent payment execution."""

from .domain import LedgerResult, Payment
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
