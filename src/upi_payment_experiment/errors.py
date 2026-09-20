"""Ledger-neutral payment errors used by services and transport adapters."""


class PaymentError(Exception):
    """Base class for expected payment-processing errors."""

    code = "PAYMENT_ERROR"


class AccountNotFoundError(PaymentError, LookupError):
    """A required payer or merchant account does not exist."""

    code = "ACCOUNT_NOT_FOUND"


class InsufficientFundsError(PaymentError, ValueError):
    """The payer cannot fund the requested transfer."""

    code = "INSUFFICIENT_FUNDS"


class InvalidPaymentError(PaymentError, ValueError):
    """A payment request violates a ledger-neutral business rule."""

    code = "INVALID_PAYMENT_REQUEST"


class PaymentConflictError(PaymentError):
    """A payment ID was reused for a different immutable request."""

    code = "PAYMENT_ID_REUSED_WITH_DIFFERENT_REQUEST"


class IdempotencyConflictError(PaymentError):
    """An idempotency key was reused for a different immutable request."""

    code = "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"
