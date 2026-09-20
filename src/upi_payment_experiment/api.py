"""Minimal FastAPI transport for the C04 payment boundary."""

from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .domain import Payment, PaymentStatus
from .errors import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidPaymentError,
    PaymentConflictError,
)
from .payment_service import PaymentService


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


def create_app(
    service: PaymentService,
    *,
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    """Create the small transport adapter around an injected payment service."""

    request_clock = clock or (lambda: datetime.now(timezone.utc))
    app = FastAPI()

    @app.post("/payments", response_model=PaymentResponse)
    def create_payment(request: PaymentRequest) -> PaymentResponse:
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
            result = service.execute_payment(payment)
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
        return PaymentResponse(
            payment_id=result.payment_id,
            transaction_id=result.transaction_id,
            status=result.status,
        )

    return app
