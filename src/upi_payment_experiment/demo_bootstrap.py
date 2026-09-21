"""Explicit local-only bootstrap for the deterministic C06 interview fixture."""

from contextlib import contextmanager
import os

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .conventional_ledger import ConventionalLedger


DEMO_DATABASE_NAME = "upi_payment_test"
LOCAL_DEMO_HOSTS = frozenset({"", "127.0.0.1", "::1", "localhost", "postgres"})
LOCAL_DEMO_HOSTADDRS = frozenset({"127.0.0.1", "::1"})
IMPLICIT_TARGET_ENVIRONMENT = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")
DEMO_ACCOUNTS = (
    ("ACC-C001", "C001", "SEK", 100000),
    ("ACC-M001", "M001", "SEK", 0),
)


def bootstrap_demo(dsn: str) -> None:
    """Reset only the approved local demo database to the canonical fixture."""

    validated_dsn = _validated_demo_dsn(dsn)
    with _without_implicit_target_environment():
        _clear_existing_demo_state(validated_dsn)
        ConventionalLedger(validated_dsn).initialize_schema()
        with psycopg.connect(validated_dsn) as connection:
            connection.execute(
                "TRUNCATE idempotency_records, transactions, payments, accounts"
            )
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO accounts (account_id, owner_id, currency, balance)
                    VALUES (%s, %s, %s, %s)
                    """,
                    DEMO_ACCOUNTS,
                )


def _clear_existing_demo_state(dsn: str) -> None:
    """Clear a complete existing schema before migration validates stale rows."""

    table_names = ("accounts", "payments", "transactions", "idempotency_records")
    with psycopg.connect(dsn) as connection:
        existing = connection.execute(
            "SELECT to_regclass(name) FROM unnest(%s::text[]) AS name",
            (list(table_names),),
        ).fetchall()
        if all(row[0] is not None for row in existing):
            connection.execute(
                "TRUNCATE idempotency_records, transactions, payments, accounts"
            )


@contextmanager
def _without_implicit_target_environment():
    """Keep libpq environment defaults from changing the validated target."""

    saved = {name: os.environ.pop(name, None) for name in IMPLICIT_TARGET_ENVIRONMENT}
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value


def _require_local_demo_target(dsn: str) -> None:
    _validated_demo_dsn(dsn)


def _validated_demo_dsn(dsn: str) -> str:
    """Return a connection string with its local demo target made explicit."""

    if not isinstance(dsn, str) or not dsn.strip():
        raise ValueError("demo DSN must be a non-empty string")
    parameters = conninfo_to_dict(dsn)
    host = parameters.get("host", "")
    hostaddr = parameters.get("hostaddr")
    service = parameters.get("service")
    database = parameters.get("dbname", "")
    if (
        host not in LOCAL_DEMO_HOSTS
        or database != DEMO_DATABASE_NAME
        or service not in (None, "")
        or (
            hostaddr not in (None, "")
            and hostaddr not in LOCAL_DEMO_HOSTADDRS
        )
    ):
        raise ValueError(
            "demo bootstrap is restricted to the local upi_payment_test database"
        )

    validated = dict(parameters)
    validated.pop("hostaddr", None)
    validated.pop("service", None)
    validated.update(
        {
            "dbname": DEMO_DATABASE_NAME,
            "host": host or hostaddr or "localhost",
        }
    )
    return make_conninfo(**validated)


def main() -> None:
    """Run the deliberately invoked local demo reset command."""

    dsn = os.environ.get("UPI_DATABASE_DSN")
    if not dsn:
        raise SystemExit("UPI_DATABASE_DSN must be configured")
    bootstrap_demo(dsn)
    print("C06 demo fixture ready: C001=100000 öre, M001=0 öre")


if __name__ == "__main__":
    main()
