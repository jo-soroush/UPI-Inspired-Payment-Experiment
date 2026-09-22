"""FastAPI transport for the shared payment boundary and minimal C06 UI."""

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .domain import Payment, PaymentStatus
from .errors import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidPaymentError,
    PaymentInfrastructureError,
    PaymentConflictError,
)
from .payment_service import PaymentService
from .qr import QrGenerationError, generate_merchant_qr
from .qr_png import PngEncodingError, encode_grayscale_png


class PaymentRequest(BaseModel):
    """Validated HTTP request fields for one payment attempt."""

    model_config = ConfigDict(extra="forbid")

    payment_id: str = Field(min_length=1)
    payer_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    amount: int = Field(gt=0, strict=True)
    currency: str = Field(pattern="^SEK$")
    idempotency_key: str = Field(min_length=1)


class PaymentResponse(BaseModel):
    payment_id: str
    transaction_id: str | None
    status: PaymentStatus


class BalanceResponse(BaseModel):
    owner_id: str
    currency: str
    balance_ore: int


class TransactionResponse(BaseModel):
    transaction_id: str
    payment_id: str
    ledger_type: str
    status: PaymentStatus
    timestamp: datetime


class TransactionHistoryResponse(BaseModel):
    transactions: list[TransactionResponse]


def create_app(
    service: PaymentService,
    *,
    services: Mapping[str, PaymentService] | None = None,
    clock: Callable[[], datetime] | None = None,
    static_directory: str | Path | None = None,
) -> FastAPI:
    """Create the same-origin API and UI around ledger-selected services."""

    request_clock = clock or (lambda: datetime.now(timezone.utc))
    static_root = (
        Path(static_directory)
        if static_directory is not None
        else Path(__file__).with_name("static")
    )
    app = FastAPI()
    service_registry = {"conventional": service}
    if services is not None:
        service_registry.update(services)

    def selected_service(
        ledger: Literal["conventional", "blockchain"],
    ) -> PaymentService:
        selected = service_registry.get(ledger)
        if selected is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "LEDGER_UNAVAILABLE",
                    "message": f"ledger is not configured: {ledger}",
                },
            )
        return selected

    @app.post("/payments", response_model=PaymentResponse)
    def create_payment(
        request: PaymentRequest,
        ledger: Literal["conventional", "blockchain"] = "conventional",
    ) -> PaymentResponse:
        try:
            payment = Payment(
                payment_id=request.payment_id,
                payer_id=request.payer_id,
                merchant_id=request.merchant_id,
                amount=request.amount,
                currency=request.currency,
                idempotency_key=request.idempotency_key,
                status=PaymentStatus.PENDING,
                created_at=request_clock(),
            )
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_PAYMENT_REQUEST", "message": str(error)},
            ) from error
        try:
            result = selected_service(ledger).execute_payment(payment)
        except (IdempotencyConflictError, PaymentConflictError) as error:
            raise HTTPException(
                status_code=409,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except AccountNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except InsufficientFundsError as error:
            raise HTTPException(
                status_code=422,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except InvalidPaymentError as error:
            raise HTTPException(
                status_code=422,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except PaymentInfrastructureError as error:
            raise HTTPException(
                status_code=503,
                detail={"code": error.code, "message": str(error)},
            ) from error
        return PaymentResponse(
            payment_id=result.payment_id,
            transaction_id=result.transaction_id,
            status=result.status,
        )

    @app.get(
        "/accounts/{owner_id}/balance",
        response_model=BalanceResponse,
    )
    def get_balance(
        owner_id: str,
        ledger: Literal["conventional", "blockchain"] = "conventional",
    ) -> BalanceResponse:
        try:
            balance = selected_service(ledger).get_balance(owner_id, "SEK")
        except AccountNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except PaymentInfrastructureError as error:
            raise HTTPException(
                status_code=503,
                detail={"code": error.code, "message": str(error)},
            ) from error
        return BalanceResponse(
            owner_id=owner_id,
            currency="SEK",
            balance_ore=balance,
        )

    @app.get("/transactions", response_model=TransactionHistoryResponse)
    def get_transactions(
        ledger: Literal["conventional", "blockchain"] = "conventional",
    ) -> TransactionHistoryResponse:
        return TransactionHistoryResponse(
            transactions=[
                TransactionResponse(
                    transaction_id=transaction.transaction_id,
                    payment_id=transaction.payment_id,
                    ledger_type=transaction.ledger_type,
                    status=transaction.status,
                    timestamp=transaction.timestamp,
                )
                for transaction in selected_service(ledger).list_transactions()
            ]
        )

    @app.get("/merchants/{merchant_id}/qr")
    def get_merchant_qr(merchant_id: str) -> Response:
        try:
            service.get_balance(merchant_id, "SEK")
            image = generate_merchant_qr(merchant_id)
            png = encode_grayscale_png(image)
        except AccountNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail={"code": error.code, "message": str(error)},
            ) from error
        except (QrGenerationError, PngEncodingError) as error:
            raise HTTPException(
                status_code=500,
                detail={"code": "QR_IMAGE_FAILED", "message": str(error)},
            ) from error
        return Response(content=png, media_type="image/png")

    @app.get("/", include_in_schema=False)
    def get_ui() -> FileResponse:
        return FileResponse(static_root / "index.html", media_type="text/html")

    app.mount("/static", StaticFiles(directory=static_root), name="static")

    return app
