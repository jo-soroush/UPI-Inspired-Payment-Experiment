"""Runtime composition for the local same-origin interview demo."""

import os

from fastapi import FastAPI

from .api import create_app
from .blockchain_ledger import BlockchainLedger
from .conventional_ledger import ConventionalLedger
from .payment_service import PaymentService


def create_demo_app() -> FastAPI:
    """Compose configured ledgers without resetting either ledger state."""

    ledger = ConventionalLedger.from_environment()
    services = {"conventional": PaymentService(ledger)}
    if os.environ.get("UPI_PAYMENT_LEDGER_ADDRESS"):
        blockchain = BlockchainLedger.from_environment()
        services["blockchain"] = PaymentService(blockchain)
    return create_app(services["conventional"], services=services)
