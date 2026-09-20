"""PostgreSQL implementation of the conventional payment ledger."""

from collections.abc import Callable
from datetime import datetime, timezone
from importlib.resources import files
import os
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from .domain import LedgerResult, Payment, PaymentStatus, Transaction
from .errors import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidPaymentError,
    PaymentConflictError,
)
from .ledger import canonical_payment_fingerprint


class ConventionalLedger:
    """Execute payments atomically in PostgreSQL."""

    ledger_type = "ConventionalLedger"

    def __init__(
        self,
        dsn: str,
        *,
        transaction_id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("dsn must be a non-empty string")
        self._dsn = dsn
        self._transaction_id_factory = transaction_id_factory or (
            lambda: f"TX-{uuid4()}"
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def from_environment(cls) -> "ConventionalLedger":
        """Build the ledger from non-secret environment configuration."""

        dsn = os.environ.get("UPI_DATABASE_DSN")
        if not dsn:
            raise RuntimeError("UPI_DATABASE_DSN must be configured")
        return cls(dsn)

    def initialize_schema(self) -> None:
        """Create the schema and migrate valid completed C03 payments."""

        schema = files("upi_payment_experiment").joinpath(
            "postgres_schema.sql"
        ).read_text(encoding="utf-8")
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute(schema)
            self._backfill_completed_c03_payments(connection)

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        """Return an account balance without exposing PostgreSQL row details."""

        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            row = connection.execute(
                """
                SELECT balance
                FROM accounts
                WHERE owner_id = %s AND currency = %s
                """,
                (owner_id, currency),
            ).fetchone()
        if row is None:
            raise AccountNotFoundError(f"account not found for owner {owner_id!r}")
        return row["balance"]

    def execute_payment(
        self, payment: Payment, *, request_fingerprint: str
    ) -> LedgerResult:
        """Atomically execute a new request or return its committed result."""

        if payment.payer_id == payment.merchant_id:
            raise InvalidPaymentError("payer and merchant must be different")
        if not isinstance(request_fingerprint, str) or not request_fingerprint:
            raise ValueError("request_fingerprint must be a non-empty string")

        connection = psycopg.connect(self._dsn, row_factory=dict_row)
        try:
            connection.execute(
                "SET TRANSACTION ISOLATION LEVEL READ COMMITTED"
            )
            self._lock_request_identities(connection, payment)
            self._after_request_identity_locks()

            idempotent_result = self._result_for_idempotency_key(
                connection, payment.idempotency_key, request_fingerprint
            )
            if idempotent_result is not None:
                connection.commit()
                return idempotent_result

            payment_result = self._result_for_payment_id(
                connection, payment.payment_id, request_fingerprint
            )
            if payment_result is not None:
                connection.execute(
                    """
                    INSERT INTO idempotency_records (
                        idempotency_key, request_fingerprint, payment_id
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        payment.idempotency_key,
                        request_fingerprint,
                        payment.payment_id,
                    ),
                )
                connection.commit()
                return payment_result

            accounts = connection.execute(
                """
                SELECT account_id, owner_id, balance, currency
                FROM accounts
                WHERE owner_id IN (%s, %s) AND currency = %s
                ORDER BY account_id
                FOR UPDATE
                """,
                (payment.payer_id, payment.merchant_id, payment.currency),
            ).fetchall()
            accounts_by_owner = {row["owner_id"]: row for row in accounts}
            expected_owners = {payment.payer_id, payment.merchant_id}
            if set(accounts_by_owner) != expected_owners:
                missing = sorted(expected_owners - set(accounts_by_owner))
                raise AccountNotFoundError(
                    f"account not found for owner(s): {', '.join(missing)}"
                )

            payer = accounts_by_owner[payment.payer_id]
            merchant = accounts_by_owner[payment.merchant_id]
            if payer["balance"] < payment.amount:
                raise InsufficientFundsError("payer has insufficient funds")

            connection.execute(
                "UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                (payment.amount, payer["account_id"]),
            )
            self._after_payer_debit()
            connection.execute(
                "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                (payment.amount, merchant["account_id"]),
            )

            transaction_id = self._transaction_id_factory()
            transaction_timestamp = self._clock()
            connection.execute(
                """
                INSERT INTO payments (
                    payment_id,
                    payer_account_id,
                    merchant_account_id,
                    amount,
                    currency,
                    idempotency_key,
                    request_fingerprint,
                    status,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payment.payment_id,
                    payer["account_id"],
                    merchant["account_id"],
                    payment.amount,
                    payment.currency,
                    payment.idempotency_key,
                    request_fingerprint,
                    PaymentStatus.SUCCESS.value,
                    payment.created_at,
                ),
            )
            self._after_payment_persisted()
            connection.execute(
                """
                INSERT INTO transactions (
                    transaction_id, payment_id, ledger_type, status, timestamp
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    transaction_id,
                    payment.payment_id,
                    self.ledger_type,
                    PaymentStatus.SUCCESS.value,
                    transaction_timestamp,
                ),
            )
            connection.execute(
                """
                INSERT INTO idempotency_records (
                    idempotency_key, request_fingerprint, payment_id
                )
                VALUES (%s, %s, %s)
                """,
                (
                    payment.idempotency_key,
                    request_fingerprint,
                    payment.payment_id,
                ),
            )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

        return LedgerResult(
            payment_id=payment.payment_id,
            transaction_id=transaction_id,
            status=PaymentStatus.SUCCESS,
        )

    def get_payment(self, payment_id: str) -> Payment | None:
        """Return one payment mapped back to the ledger-neutral domain model."""

        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            row = connection.execute(
                """
                SELECT
                    p.payment_id,
                    payer.owner_id AS payer_id,
                    merchant.owner_id AS merchant_id,
                    p.amount,
                    p.currency,
                    p.idempotency_key,
                    p.status,
                    p.created_at
                FROM payments AS p
                JOIN accounts AS payer
                    ON payer.account_id = p.payer_account_id
                JOIN accounts AS merchant
                    ON merchant.account_id = p.merchant_account_id
                WHERE p.payment_id = %s
                """,
                (payment_id,),
            ).fetchone()
        if row is None:
            return None
        return Payment(
            payment_id=row["payment_id"],
            payer_id=row["payer_id"],
            merchant_id=row["merchant_id"],
            amount=row["amount"],
            currency=row["currency"],
            idempotency_key=row["idempotency_key"],
            status=PaymentStatus(row["status"]),
            created_at=row["created_at"],
        )

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Return one persisted transaction."""

        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            row = connection.execute(
                """
                SELECT transaction_id, payment_id, ledger_type, status, timestamp
                FROM transactions
                WHERE transaction_id = %s
                """,
                (transaction_id,),
            ).fetchone()
        return self._transaction_from_row(row) if row is not None else None

    def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
        """Return deterministic committed transaction history."""

        query = """
            SELECT transaction_id, payment_id, ledger_type, status, timestamp
            FROM transactions
        """
        parameters: tuple[str, ...] = ()
        if payment_id is not None:
            query += " WHERE payment_id = %s"
            parameters = (payment_id,)
        query += " ORDER BY timestamp, transaction_id"

        with psycopg.connect(
            self._dsn, autocommit=True, row_factory=dict_row
        ) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._transaction_from_row(row) for row in rows]

    def _after_payer_debit(self) -> None:
        """Narrow test seam for the canonical controlled rollback proof."""

    def _after_payment_persisted(self) -> None:
        """Narrow test seam for C04 persistence-failure rollback proof."""

    def _after_request_identity_locks(self) -> None:
        """Narrow test seam for deterministic request-lock verification."""

    @staticmethod
    def _backfill_completed_c03_payments(
        connection: psycopg.Connection,
    ) -> None:
        """Derive C04 request identity for committed C03 payment history."""

        rows = connection.execute(
            """
            SELECT
                p.payment_id,
                payer.owner_id AS payer_id,
                merchant.owner_id AS merchant_id,
                p.amount,
                p.currency,
                p.idempotency_key,
                p.status,
                p.created_at,
                p.request_fingerprint,
                t.transaction_id
            FROM payments AS p
            JOIN accounts AS payer
                ON payer.account_id = p.payer_account_id
            JOIN accounts AS merchant
                ON merchant.account_id = p.merchant_account_id
            JOIN transactions AS t
                ON t.payment_id = p.payment_id
            WHERE p.status = %s AND t.status = %s
            ORDER BY p.payment_id
            """,
            (PaymentStatus.SUCCESS.value, PaymentStatus.SUCCESS.value),
        ).fetchall()

        for row in rows:
            persisted_payment = Payment(
                payment_id=row["payment_id"],
                payer_id=row["payer_id"],
                merchant_id=row["merchant_id"],
                amount=row["amount"],
                currency=row["currency"],
                idempotency_key=row["idempotency_key"],
                status=PaymentStatus(row["status"]),
                created_at=row["created_at"],
            )
            fingerprint = canonical_payment_fingerprint(persisted_payment)
            existing_fingerprint = row["request_fingerprint"]
            if existing_fingerprint is not None and existing_fingerprint != fingerprint:
                raise RuntimeError(
                    "persisted payment fingerprint conflicts with canonical data"
                )

            connection.execute(
                """
                UPDATE payments
                SET request_fingerprint = %s
                WHERE payment_id = %s AND request_fingerprint IS NULL
                """,
                (fingerprint, row["payment_id"]),
            )
            idempotency_row = connection.execute(
                """
                SELECT request_fingerprint, payment_id
                FROM idempotency_records
                WHERE idempotency_key = %s
                """,
                (row["idempotency_key"],),
            ).fetchone()
            if idempotency_row is None:
                connection.execute(
                    """
                    INSERT INTO idempotency_records (
                        idempotency_key, request_fingerprint, payment_id
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        row["idempotency_key"],
                        fingerprint,
                        row["payment_id"],
                    ),
                )
            elif (
                idempotency_row["request_fingerprint"] != fingerprint
                or idempotency_row["payment_id"] != row["payment_id"]
            ):
                raise RuntimeError(
                    "legacy idempotency key has inconsistent payment bindings"
                )

    @staticmethod
    def _lock_request_identities(
        connection: psycopg.Connection,
        payment: Payment,
    ) -> None:
        """Serialize both request identities inside PostgreSQL."""

        lock_names = sorted(
            (
                f"idempotency:{payment.idempotency_key}",
                f"payment:{payment.payment_id}",
            )
        )
        for lock_name in lock_names:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (lock_name,),
            )

    @staticmethod
    def _result_for_idempotency_key(
        connection: psycopg.Connection,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> LedgerResult | None:
        row = connection.execute(
            """
            SELECT
                i.request_fingerprint,
                p.payment_id,
                t.transaction_id,
                t.status
            FROM idempotency_records AS i
            JOIN payments AS p ON p.payment_id = i.payment_id
            JOIN transactions AS t ON t.payment_id = p.payment_id
            WHERE i.idempotency_key = %s
            """,
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise IdempotencyConflictError(
                "idempotency key was reused with a different payment request"
            )
        return ConventionalLedger._ledger_result_from_row(row)

    @staticmethod
    def _result_for_payment_id(
        connection: psycopg.Connection,
        payment_id: str,
        request_fingerprint: str,
    ) -> LedgerResult | None:
        row = connection.execute(
            """
            SELECT
                p.request_fingerprint,
                p.payment_id,
                t.transaction_id,
                t.status
            FROM payments AS p
            JOIN transactions AS t ON t.payment_id = p.payment_id
            WHERE p.payment_id = %s
            """,
            (payment_id,),
        ).fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise PaymentConflictError(
                "payment ID was reused with a different payment request"
            )
        return ConventionalLedger._ledger_result_from_row(row)

    @staticmethod
    def _ledger_result_from_row(row: dict[str, object]) -> LedgerResult:
        return LedgerResult(
            payment_id=str(row["payment_id"]),
            transaction_id=str(row["transaction_id"]),
            status=PaymentStatus(str(row["status"])),
        )

    @staticmethod
    def _transaction_from_row(row: dict[str, object]) -> Transaction:
        return Transaction(
            transaction_id=str(row["transaction_id"]),
            payment_id=str(row["payment_id"]),
            ledger_type=str(row["ledger_type"]),
            status=PaymentStatus(str(row["status"])),
            timestamp=row["timestamp"],  # type: ignore[arg-type]
        )
