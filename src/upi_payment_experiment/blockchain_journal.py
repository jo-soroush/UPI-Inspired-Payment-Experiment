"""Durable PostgreSQL coordination for blockchain payment operations."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from .domain import Payment
from .errors import IdempotencyConflictError, PaymentConflictError


BLOCKCHAIN_NAMESPACE = "blockchain"


@dataclass(frozen=True)
class PreparedTransaction:
    transaction_hash: str
    sender_address: str
    nonce: int
    signed_raw_transaction: bytes


@dataclass(frozen=True)
class BlockchainOperation:
    ledger_type: str
    payment_id: str
    request_fingerprint: str
    original_idempotency_key: str
    payer_id: str
    merchant_id: str
    amount: int
    currency: str
    transaction_hash: str
    sender_address: str
    nonce: int
    signed_raw_transaction: bytes
    status: str
    prepared_at: datetime
    submitted_at: datetime | None
    confirmed_at: datetime | None
    receipt_status: int | None
    gas_used: int | None


class BlockchainOperationJournal:
    """Coordinate request identity without becoming blockchain balance authority."""

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("journal DSN must be a non-empty string")
        self._dsn = dsn

    def prepare(
        self,
        payment: Payment,
        request_fingerprint: str,
        prepared_at: datetime,
        build: Callable[[int], PreparedTransaction],
    ) -> tuple[BlockchainOperation, bool]:
        """Return an existing operation or durably prepare exactly one new one."""

        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            self._lock_request_identities(connection, payment)
            by_key = self._select_by_idempotency_key(connection, payment.idempotency_key)
            if by_key is not None:
                if by_key.request_fingerprint != request_fingerprint:
                    raise IdempotencyConflictError(
                        "idempotency key was reused with a different payment request"
                    )
                return by_key, False

            by_payment = self._select_by_payment_id(connection, payment.payment_id)
            if by_payment is not None:
                if by_payment.request_fingerprint != request_fingerprint:
                    raise PaymentConflictError(
                        "payment ID was reused with a different payment request"
                    )
                self._insert_idempotency_binding(
                    connection,
                    payment.idempotency_key,
                    request_fingerprint,
                    payment.payment_id,
                )
                return by_payment, False

            row = connection.execute(
                """
                SELECT COALESCE(MAX(nonce) + 1, 0) AS next_nonce
                FROM blockchain_operations
                WHERE ledger_type = %s AND payer_id = %s
                """,
                (BLOCKCHAIN_NAMESPACE, payment.payer_id),
            ).fetchone()
            reserved_nonce = int(row["next_nonce"])
            prepared = build(reserved_nonce)
            connection.execute(
                """
                INSERT INTO blockchain_operations (
                    ledger_type, payment_id, request_fingerprint,
                    original_idempotency_key, payer_id, merchant_id, amount,
                    currency, transaction_hash, sender_address, nonce,
                    signed_raw_transaction, status, prepared_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'PREPARED', %s)
                """,
                (
                    BLOCKCHAIN_NAMESPACE,
                    payment.payment_id,
                    request_fingerprint,
                    payment.idempotency_key,
                    payment.payer_id,
                    payment.merchant_id,
                    payment.amount,
                    payment.currency,
                    prepared.transaction_hash,
                    prepared.sender_address,
                    prepared.nonce,
                    prepared.signed_raw_transaction,
                    prepared_at,
                ),
            )
            self._insert_idempotency_binding(
                connection,
                payment.idempotency_key,
                request_fingerprint,
                payment.payment_id,
            )
            operation = self._select_by_payment_id(connection, payment.payment_id)
            if operation is None:  # pragma: no cover - database invariant guard
                raise RuntimeError("prepared blockchain operation was not persisted")
            return operation, True

    def get_by_payment_id(self, payment_id: str) -> BlockchainOperation | None:
        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            return self._select_by_payment_id(connection, payment_id)

    def get_by_transaction_hash(
        self, transaction_hash: str
    ) -> BlockchainOperation | None:
        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            row = connection.execute(
                """
                SELECT * FROM blockchain_operations
                WHERE ledger_type = %s AND transaction_hash = %s
                """,
                (BLOCKCHAIN_NAMESPACE, transaction_hash),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def list_operations(
        self, payment_id: str | None = None
    ) -> list[BlockchainOperation]:
        query = "SELECT * FROM blockchain_operations WHERE ledger_type = %s"
        parameters: list[object] = [BLOCKCHAIN_NAMESPACE]
        if payment_id is not None:
            query += " AND payment_id = %s"
            parameters.append(payment_id)
        query += (
            " ORDER BY COALESCE(confirmed_at, submitted_at, prepared_at),"
            " transaction_hash"
        )
        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def update_status(
        self,
        payment_id: str,
        status: str,
        *,
        observed_at: datetime,
        receipt_status: int | None = None,
        gas_used: int | None = None,
    ) -> BlockchainOperation:
        submitted_at = observed_at if status == "SUBMITTED" else None
        confirmed_at = observed_at if status in {"SUCCESS", "FAILED"} else None
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                UPDATE blockchain_operations
                SET status = %s,
                    submitted_at = COALESCE(submitted_at, %s),
                    confirmed_at = COALESCE(confirmed_at, %s),
                    receipt_status = COALESCE(%s, receipt_status),
                    gas_used = COALESCE(%s, gas_used)
                WHERE ledger_type = %s
                  AND payment_id = %s
                  AND status NOT IN ('SUCCESS', 'FAILED')
                RETURNING *
                """,
                (
                    status,
                    submitted_at,
                    confirmed_at,
                    receipt_status,
                    gas_used,
                    BLOCKCHAIN_NAMESPACE,
                    payment_id,
                ),
            ).fetchone()
            if row is None:
                current = self._select_by_payment_id(connection, payment_id)
                if current is None:
                    raise LookupError(f"blockchain operation not found: {payment_id}")
                return current
        if row is None:
            raise LookupError(f"blockchain operation not found: {payment_id}")
        return self._from_row(row)

    @staticmethod
    def _lock_request_identities(
        connection: psycopg.Connection, payment: Payment
    ) -> None:
        for lock_name in sorted(
            (
                f"blockchain:idempotency:{payment.idempotency_key}",
                f"blockchain:payment:{payment.payment_id}",
                f"blockchain:sender:{payment.payer_id}",
            )
        ):
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (lock_name,),
            )

    @staticmethod
    def _insert_idempotency_binding(
        connection: psycopg.Connection,
        idempotency_key: str,
        request_fingerprint: str,
        payment_id: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO blockchain_idempotency_records (
                ledger_type, idempotency_key, request_fingerprint, payment_id
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                BLOCKCHAIN_NAMESPACE,
                idempotency_key,
                request_fingerprint,
                payment_id,
            ),
        )

    @staticmethod
    def _select_by_idempotency_key(
        connection: psycopg.Connection, idempotency_key: str
    ) -> BlockchainOperation | None:
        row = connection.execute(
            """
            SELECT operation.*
            FROM blockchain_idempotency_records AS binding
            JOIN blockchain_operations AS operation
              ON operation.ledger_type = binding.ledger_type
             AND operation.payment_id = binding.payment_id
            WHERE binding.ledger_type = %s AND binding.idempotency_key = %s
            """,
            (BLOCKCHAIN_NAMESPACE, idempotency_key),
        ).fetchone()
        return BlockchainOperationJournal._from_row(row) if row is not None else None

    @staticmethod
    def _select_by_payment_id(
        connection: psycopg.Connection, payment_id: str
    ) -> BlockchainOperation | None:
        row = connection.execute(
            """
            SELECT * FROM blockchain_operations
            WHERE ledger_type = %s AND payment_id = %s
            """,
            (BLOCKCHAIN_NAMESPACE, payment_id),
        ).fetchone()
        return BlockchainOperationJournal._from_row(row) if row is not None else None

    @staticmethod
    def _from_row(row: dict[str, object]) -> BlockchainOperation:
        return BlockchainOperation(
            ledger_type=str(row["ledger_type"]),
            payment_id=str(row["payment_id"]),
            request_fingerprint=str(row["request_fingerprint"]),
            original_idempotency_key=str(row["original_idempotency_key"]),
            payer_id=str(row["payer_id"]),
            merchant_id=str(row["merchant_id"]),
            amount=int(row["amount"]),
            currency=str(row["currency"]),
            transaction_hash=str(row["transaction_hash"]),
            sender_address=str(row["sender_address"]),
            nonce=int(row["nonce"]),
            signed_raw_transaction=bytes(row["signed_raw_transaction"]),
            status=str(row["status"]),
            prepared_at=row["prepared_at"],  # type: ignore[arg-type]
            submitted_at=row["submitted_at"],  # type: ignore[arg-type]
            confirmed_at=row["confirmed_at"],  # type: ignore[arg-type]
            receipt_status=(
                int(row["receipt_status"])
                if row["receipt_status"] is not None
                else None
            ),
            gas_used=int(row["gas_used"]) if row["gas_used"] is not None else None,
        )
