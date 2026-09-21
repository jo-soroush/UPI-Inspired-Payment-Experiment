"""Runtime composition for the local C06 same-origin interview demo."""

from fastapi import FastAPI

from .api import create_app
from .conventional_ledger import ConventionalLedger
from .payment_service import PaymentService


def create_demo_app() -> FastAPI:
    """Compose the delivered conventional ledger without resetting demo state."""

    ledger = ConventionalLedger.from_environment()
    return create_app(PaymentService(ledger))
