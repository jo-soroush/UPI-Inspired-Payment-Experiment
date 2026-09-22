from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from threading import Thread
import time
from typing import Any
from urllib.parse import urlsplit

from eth_account import Account
from hexbytes import HexBytes
import httpx
import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict
from web3 import HTTPProvider, Web3
from web3.exceptions import TimeExhausted

from upi_payment_experiment.api import create_app
from upi_payment_experiment.blockchain_ledger import BlockchainLedger, SigningIdentity
from upi_payment_experiment.blockchain_bootstrap import (
    LOCAL_ANVIL_CHAIN_ID,
    _validated_local_anvil_rpc_url,
    _validated_local_demo_dsn,
    deploy_demo_contract,
    reset_operation_journal,
)
from upi_payment_experiment.conventional_ledger import ConventionalLedger
from upi_payment_experiment.demo_bootstrap import bootstrap_demo
from upi_payment_experiment.domain import LedgerResult, Payment, PaymentStatus, Transaction
from upi_payment_experiment.errors import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    InvalidPaymentError,
    PaymentConflictError,
)
from upi_payment_experiment.payment_service import PaymentService
from upi_payment_experiment.ledger import canonical_payment_fingerprint


_C07_TEST_DATABASE_NAME = "upi_payment_test"
_C07_TEST_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_C07_IMPLICIT_TARGET_ENVIRONMENT = (
    "PGHOST",
    "PGHOSTADDR",
    "PGSERVICE",
    "PGSERVICEFILE",
)


def _validated_c07_test_dsn(raw_dsn: str) -> str:
    """Fail closed unless the test harness has an explicit loopback target."""

    if any(os.environ.get(name) for name in _C07_IMPLICIT_TARGET_ENVIRONMENT):
        raise ValueError(
            "C07 tests do not allow implicit libpq database target environment"
        )
    if not isinstance(raw_dsn, str) or not raw_dsn.strip():
        raise ValueError("C07 test database DSN must be a non-empty PostgreSQL URI")

    parsed = urlsplit(raw_dsn)
    if parsed.scheme != "postgresql" or parsed.hostname not in _C07_TEST_LOCAL_HOSTS:
        raise ValueError(
            "C07 tests require an explicit postgresql loopback database host"
        )

    parameters = conninfo_to_dict(raw_dsn)
    if (
        parameters.get("host") not in _C07_TEST_LOCAL_HOSTS
        or parameters.get("hostaddr") not in (None, "")
    ):
        raise ValueError(
            "C07 tests are restricted to the explicit local upi_payment_test database"
        )
    validated_dsn = _validated_local_demo_dsn(raw_dsn)
    if conninfo_to_dict(validated_dsn).get("dbname") != _C07_TEST_DATABASE_NAME:
        raise ValueError(
            "C07 tests are restricted to the explicit local upi_payment_test database"
        )
    return validated_dsn


TEST_DSN = _validated_c07_test_dsn(
    os.environ.get(
        "UPI_TEST_DATABASE_DSN",
        "postgresql://upi@127.0.0.1:55432/upi_payment_test",
    )
)
PAYMENT_TIME = datetime(2026, 1, 7, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class AnvilNode:
    web3: Web3
    accounts: tuple[Any, Any, Any]


@dataclass(frozen=True)
class BlockchainHarness:
    web3: Web3
    contract: Any
    identities: dict[str, SigningIdentity]

    def ledger(self, ledger_type: type[BlockchainLedger] = BlockchainLedger):
        return ledger_type(
            self.web3,
            self.contract,
            TEST_DSN,
            self.identities,
            receipt_timeout=2,
            clock=lambda: PAYMENT_TIME,
        )


@pytest.fixture(scope="session")
def anvil_node() -> AnvilNode:
    Account.enable_unaudited_hdwallet_features()
    _, mnemonic = Account.create_with_mnemonic()
    accounts = tuple(
        Account.from_mnemonic(
            mnemonic,
            account_path=f"m/44'/60'/0'/0/{index}",
        )
        for index in range(3)
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    anvil = shutil.which("anvil") or str(Path.home() / ".foundry/bin/anvil")
    process = subprocess.Popen(
        [
            anvil,
            "--silent",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--mnemonic",
            mnemonic,
            "--accounts",
            "3",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    web3 = Web3(HTTPProvider(f"http://127.0.0.1:{port}"))
    for _ in range(100):
        if web3.is_connected():
            break
        if process.poll() is not None:
            raise RuntimeError(f"Anvil exited early: {process.stderr.read()}")
        time.sleep(0.05)
    else:
        process.terminate()
        raise RuntimeError("Anvil did not become ready")
    try:
        yield AnvilNode(web3, accounts)
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture
def blockchain_harness(anvil_node: AnvilNode) -> BlockchainHarness:
    artifact = json.loads(
        Path("out/PaymentLedger.sol/PaymentLedger.json").read_text(encoding="utf-8")
    )
    admin, payer, merchant = anvil_node.accounts
    contract_address = deploy_demo_contract(
        anvil_node.web3,
        "out/PaymentLedger.sol/PaymentLedger.json",
        admin.key.hex(),
        {"C001": payer.key.hex(), "M001": merchant.key.hex()},
    )
    contract = anvil_node.web3.eth.contract(
        address=contract_address, abi=artifact["abi"]
    )

    ConventionalLedger(TEST_DSN).initialize_schema()
    with psycopg.connect(TEST_DSN) as connection:
        connection.execute(
            "TRUNCATE blockchain_idempotency_records, blockchain_operations"
        )
    identities = {
        "C001": SigningIdentity(payer.address, payer.key.hex()),
        "M001": SigningIdentity(merchant.address, merchant.key.hex()),
    }
    return BlockchainHarness(anvil_node.web3, contract, identities)


def payment(
    *,
    payment_id: str = "PAY-C07-001",
    idempotency_key: str = "IDEM-C07-001",
    amount: int = 10_000,
    payer_id: str = "C001",
    merchant_id: str = "M001",
) -> Payment:
    return Payment(
        payment_id=payment_id,
        payer_id=payer_id,
        merchant_id=merchant_id,
        amount=amount,
        currency="SEK",
        idempotency_key=idempotency_key,
        status=PaymentStatus.PENDING,
        created_at=PAYMENT_TIME,
    )


def _prepare_operation(ledger: BlockchainLedger, candidate: Payment):
    operation, created = ledger._journal.prepare(
        candidate,
        canonical_payment_fingerprint(candidate),
        PAYMENT_TIME,
        lambda reserved_nonce: ledger._build_signed_transaction(
            candidate, reserved_nonce
        ),
    )
    assert created
    return operation


def _configure_runtime_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    rpc_url: str,
    contract_address: str = "0x0000000000000000000000000000000000000001",
    identities: dict[str, SigningIdentity] | None = None,
) -> None:
    if identities is None:
        customer = Account.create()
        merchant = Account.create()
        configured_identities = {
            "C001": SigningIdentity(customer.address, customer.key.hex()),
            "M001": SigningIdentity(merchant.address, merchant.key.hex()),
        }
    else:
        configured_identities = identities
    monkeypatch.setenv("UPI_ANVIL_RPC_URL", rpc_url)
    monkeypatch.setenv("UPI_PAYMENT_LEDGER_ADDRESS", contract_address)
    monkeypatch.setenv("UPI_DATABASE_DSN", TEST_DSN)
    monkeypatch.setenv(
        "UPI_PAYMENT_LEDGER_ARTIFACT",
        str(Path("out/PaymentLedger.sol/PaymentLedger.json").resolve()),
    )
    monkeypatch.setenv(
        "UPI_ANVIL_C001_PRIVATE_KEY", configured_identities["C001"].private_key
    )
    monkeypatch.setenv(
        "UPI_ANVIL_M001_PRIVATE_KEY", configured_identities["M001"].private_key
    )


@contextmanager
def _local_json_rpc_server(*, client_version: str, chain_id: int):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            payload = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
            )
            result = {
                "web3_clientVersion": client_version,
                "eth_chainId": hex(chain_id),
            }.get(payload["method"])
            response = json.dumps(
                {"jsonrpc": "2.0", "id": payload.get("id"), "result": result}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_real_anvil_canonical_payment_and_ledger_interface(
    blockchain_harness: BlockchainHarness,
) -> None:
    ledger = blockchain_harness.ledger()
    service = PaymentService(ledger)

    result = service.execute_payment(payment())

    assert result.status is PaymentStatus.SUCCESS
    assert result.transaction_id is not None
    assert result.transaction_id.startswith("0x")
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000
    assert ledger.get_payment("PAY-C07-001").status is PaymentStatus.SUCCESS
    assert ledger.get_transaction(result.transaction_id).status is PaymentStatus.SUCCESS
    assert ledger.list_transactions() == [ledger.get_transaction(result.transaction_id)]
    receipt = blockchain_harness.web3.eth.get_transaction_receipt(
        result.transaction_id
    )
    events = blockchain_harness.contract.events.PaymentExecuted().process_receipt(
        receipt
    )
    assert len(events) == 1
    assert events[0]["args"]["amount"] == 10_000


def test_fresh_chain_bootstrap_resets_only_blockchain_operation_journal(
    blockchain_harness: BlockchainHarness,
) -> None:
    try:
        PaymentService(blockchain_harness.ledger()).execute_payment(payment())
        with psycopg.connect(TEST_DSN) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS c07_unrelated_reset_probe "
                "(probe_value INTEGER NOT NULL)"
            )
            connection.execute("TRUNCATE c07_unrelated_reset_probe")
            connection.execute(
                "INSERT INTO c07_unrelated_reset_probe (probe_value) VALUES (7)"
            )
            conventional_counts_before = tuple(
                connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in (
                    "accounts",
                    "payments",
                    "transactions",
                    "idempotency_records",
                )
            )
            assert connection.execute(
                "SELECT count(*) FROM blockchain_operations"
            ).fetchone() == (1,)

        reset_operation_journal(TEST_DSN)

        with psycopg.connect(TEST_DSN) as connection:
            assert connection.execute(
                "SELECT count(*) FROM blockchain_operations"
            ).fetchone() == (0,)
            assert tuple(
                connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in (
                    "accounts",
                    "payments",
                    "transactions",
                    "idempotency_records",
                )
            ) == conventional_counts_before
            assert connection.execute(
                "SELECT probe_value FROM c07_unrelated_reset_probe"
            ).fetchone() == (7,)
    finally:
        with psycopg.connect(TEST_DSN) as connection:
            connection.execute("DROP TABLE IF EXISTS c07_unrelated_reset_probe")


def test_replay_and_conflicts_use_journal_without_second_submission(
    blockchain_harness: BlockchainHarness,
) -> None:
    class CountingLedger(BlockchainLedger):
        broadcasts = 0

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            return super()._broadcast_raw_transaction(raw_transaction)

    ledger = blockchain_harness.ledger(CountingLedger)
    service = PaymentService(ledger)
    original = service.execute_payment(payment())
    replay = service.execute_payment(payment())
    assert replay == original
    assert ledger.broadcasts == 1

    with pytest.raises(IdempotencyConflictError):
        service.execute_payment(payment(payment_id="PAY-DIFFERENT", amount=1))
    with pytest.raises(PaymentConflictError):
        service.execute_payment(
            payment(idempotency_key="IDEM-DIFFERENT", amount=1)
        )
    assert ledger.broadcasts == 1
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000


def test_terminal_success_replay_is_provider_independent_and_immutable(
    blockchain_harness: BlockchainHarness,
) -> None:
    class ProviderOutageAfterSuccessLedger(BlockchainLedger):
        broadcasts = 0
        provider_queries = 0
        outage = False

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            return super()._broadcast_raw_transaction(raw_transaction)

        def _receipt_if_available(self, transaction_hash: str):
            self.provider_queries += 1
            if self.outage:
                raise OSError("controlled provider outage")
            return super()._receipt_if_available(transaction_hash)

        def _transaction_is_known(self, transaction_hash: str) -> bool:
            self.provider_queries += 1
            if self.outage:
                raise OSError("controlled provider outage")
            return super()._transaction_is_known(transaction_hash)

    ledger = blockchain_harness.ledger(ProviderOutageAfterSuccessLedger)
    service = PaymentService(ledger)
    original = service.execute_payment(payment())
    ledger.outage = True
    queries_before_replay = ledger.provider_queries

    replay = service.execute_payment(payment())

    assert replay == original
    assert replay.status is PaymentStatus.SUCCESS
    assert ledger.provider_queries == queries_before_replay
    assert ledger.broadcasts == 1
    assert ledger.get_payment(original.payment_id).status is PaymentStatus.SUCCESS
    assert ledger.get_transaction(original.transaction_id).status is PaymentStatus.SUCCESS
    assert ledger.list_transactions() == [ledger.get_transaction(original.transaction_id)]
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000
    with psycopg.connect(TEST_DSN) as connection:
        stored = connection.execute(
            """
            SELECT status, transaction_hash FROM blockchain_operations
            WHERE payment_id = %s
            """,
            (original.payment_id,),
        ).fetchone()
    assert stored == ("SUCCESS", original.transaction_id)


def test_stale_success_resolver_cannot_downgrade_durable_terminal_state(
    blockchain_harness: BlockchainHarness,
) -> None:
    class ProviderOutageLedger(BlockchainLedger):
        broadcasts = 0

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            raise AssertionError("a stale resolver must not broadcast")

        def _wait_for_receipt(self, transaction_hash: str):
            raise OSError("controlled stale resolver provider outage")

    ledger = blockchain_harness.ledger()
    candidate = payment(
        payment_id="PAY-C07-STALE-SUCCESS",
        idempotency_key="IDEM-C07-STALE-SUCCESS",
    )
    stale_operation = _prepare_operation(ledger, candidate)
    original = ledger._submit_new(stale_operation)
    terminal_before = ledger._journal.get_by_payment_id(candidate.payment_id)
    assert terminal_before is not None
    assert terminal_before.status == "SUCCESS"
    balances_before = (ledger.get_balance("C001"), ledger.get_balance("M001"))

    stale_resolver = ProviderOutageLedger(
        blockchain_harness.web3,
        blockchain_harness.contract,
        TEST_DSN,
        blockchain_harness.identities,
    )
    resolved = stale_resolver._resolve_receipt(stale_operation)
    terminal_after = ledger._journal.get_by_payment_id(candidate.payment_id)

    assert resolved == original
    assert stale_resolver.broadcasts == 0
    assert terminal_after is not None
    assert terminal_after.status == "SUCCESS"
    assert terminal_after.transaction_hash == terminal_before.transaction_hash
    assert terminal_after.receipt_status == terminal_before.receipt_status == 1
    assert terminal_after.gas_used == terminal_before.gas_used
    assert (ledger.get_balance("C001"), ledger.get_balance("M001")) == balances_before
    assert ledger.get_payment(candidate.payment_id).status is PaymentStatus.SUCCESS
    assert ledger.get_transaction(original.transaction_id).status is PaymentStatus.SUCCESS
    assert [entry.status for entry in ledger.list_transactions(candidate.payment_id)] == [
        PaymentStatus.SUCCESS
    ]


def test_stale_failed_receipt_cannot_downgrade_durable_terminal_state(
    blockchain_harness: BlockchainHarness,
) -> None:
    class StaleReceiptLedger(BlockchainLedger):
        broadcasts = 0

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            raise AssertionError("a stale receipt handler must not broadcast")

    ledger = blockchain_harness.ledger()
    candidate = payment(
        payment_id="PAY-C07-STALE-FAILED",
        idempotency_key="IDEM-C07-STALE-FAILED",
    )
    stale_operation = _prepare_operation(ledger, candidate)
    terminal_before = ledger._journal.update_status(
        candidate.payment_id,
        "FAILED",
        observed_at=PAYMENT_TIME,
        receipt_status=0,
        gas_used=42_000,
    )
    balances_before = (ledger.get_balance("C001"), ledger.get_balance("M001"))

    stale_handler = StaleReceiptLedger(
        blockchain_harness.web3,
        blockchain_harness.contract,
        TEST_DSN,
        blockchain_harness.identities,
    )
    resolved = stale_handler._apply_receipt(
        stale_operation, {"status": "malformed", "gasUsed": 42_000}
    )
    terminal_after = ledger._journal.get_by_payment_id(candidate.payment_id)

    assert resolved.status is PaymentStatus.FAILED
    assert stale_handler.broadcasts == 0
    assert terminal_after is not None
    assert terminal_after.status == "FAILED"
    assert terminal_after.transaction_hash == terminal_before.transaction_hash
    assert terminal_after.receipt_status == terminal_before.receipt_status == 0
    assert terminal_after.gas_used == terminal_before.gas_used == 42_000
    assert (ledger.get_balance("C001"), ledger.get_balance("M001")) == balances_before
    assert ledger.get_payment(candidate.payment_id).status is PaymentStatus.FAILED
    assert ledger.get_transaction(stale_operation.transaction_hash).status is PaymentStatus.FAILED
    assert [entry.status for entry in ledger.list_transactions(candidate.payment_id)] == [
        PaymentStatus.FAILED
    ]


def test_validation_and_authorization_fail_without_balance_mutation(
    blockchain_harness: BlockchainHarness,
) -> None:
    ledger = blockchain_harness.ledger()
    service = PaymentService(ledger)
    with pytest.raises(InsufficientFundsError):
        service.execute_payment(payment(amount=100_001))
    with pytest.raises(AccountNotFoundError):
        service.execute_payment(payment(payer_id="C999"))
    with pytest.raises(AccountNotFoundError):
        service.execute_payment(payment(merchant_id="M999"))

    wrong_account = Account.create()
    wrong_identity = SigningIdentity(wrong_account.address, wrong_account.key.hex())
    unauthorized = BlockchainLedger(
        blockchain_harness.web3,
        blockchain_harness.contract,
        TEST_DSN,
        {**blockchain_harness.identities, "C001": wrong_identity},
    )
    with pytest.raises(InvalidPaymentError, match="not authorized"):
        PaymentService(unauthorized).execute_payment(payment())
    assert ledger.get_balance("C001") == 100_000
    assert ledger.get_balance("M001") == 0


def test_lost_receipt_reconciles_original_hash_without_new_transaction(
    blockchain_harness: BlockchainHarness,
) -> None:
    class LostReceiptOnceLedger(BlockchainLedger):
        broadcasts = 0
        waits = 0

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            return super()._broadcast_raw_transaction(raw_transaction)

        def _wait_for_receipt(self, transaction_hash: str):
            self.waits += 1
            if self.waits == 1:
                raise TimeExhausted()
            return super()._wait_for_receipt(transaction_hash)

    ledger = blockchain_harness.ledger(LostReceiptOnceLedger)
    service = PaymentService(ledger)
    uncertain = service.execute_payment(payment())
    assert uncertain.status is PaymentStatus.UNKNOWN
    retained_hash = uncertain.transaction_id

    reconciled = service.execute_payment(payment())

    assert reconciled.status is PaymentStatus.SUCCESS
    assert reconciled.transaction_id == retained_hash
    assert ledger.broadcasts == 1
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000


def test_prebroadcast_failure_reuses_exact_signed_transaction(
    blockchain_harness: BlockchainHarness,
) -> None:
    class FailBeforeBroadcastOnceLedger(BlockchainLedger):
        attempts: list[bytes] = []

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.attempts.append(raw_transaction)
            if len(self.attempts) == 1:
                raise OSError("controlled failure before provider accepted transaction")
            return super()._broadcast_raw_transaction(raw_transaction)

    ledger = blockchain_harness.ledger(FailBeforeBroadcastOnceLedger)
    service = PaymentService(ledger)
    uncertain = service.execute_payment(payment())
    reconciled = service.execute_payment(payment())

    assert uncertain.status is PaymentStatus.UNKNOWN
    assert reconciled.status is PaymentStatus.SUCCESS
    assert uncertain.transaction_id == reconciled.transaction_id
    assert len(ledger.attempts) == 2
    assert ledger.attempts[0] == ledger.attempts[1]
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000


def test_prepared_operations_reserve_distinct_sender_nonces(
    blockchain_harness: BlockchainHarness,
) -> None:
    class NeverBroadcastLedger(BlockchainLedger):
        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            raise OSError("controlled provider outage")

    service = PaymentService(blockchain_harness.ledger(NeverBroadcastLedger))
    first = service.execute_payment(
        payment(payment_id="PAY-NONCE-1", idempotency_key="IDEM-NONCE-1")
    )
    second = service.execute_payment(
        payment(payment_id="PAY-NONCE-2", idempotency_key="IDEM-NONCE-2")
    )
    assert first.status is PaymentStatus.UNKNOWN
    assert second.status is PaymentStatus.UNKNOWN
    with psycopg.connect(TEST_DSN) as connection:
        nonces = connection.execute(
            """
            SELECT nonce FROM blockchain_operations
            WHERE ledger_type = 'blockchain'
            ORDER BY nonce
            """
        ).fetchall()
    assert len(nonces) == 2
    assert nonces[1][0] == nonces[0][0] + 1


def test_failed_receipt_maps_to_failed_without_web3_leakage(
    blockchain_harness: BlockchainHarness,
) -> None:
    class FailedReceiptLedger(BlockchainLedger):
        expected_hash: str | None = None
        broadcasts = 0
        receipt_queries = 0
        outage = False

        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            self.broadcasts += 1
            signed_hash = Web3.keccak(raw_transaction)
            self.expected_hash = Web3.to_hex(signed_hash)
            return signed_hash

        def _wait_for_receipt(self, transaction_hash: str):
            return {"status": 0, "gasUsed": 42_000}

        def _receipt_if_available(self, transaction_hash: str):
            self.receipt_queries += 1
            if self.outage:
                raise OSError("controlled provider outage")
            return None

    ledger = blockchain_harness.ledger(FailedReceiptLedger)
    service = PaymentService(ledger)
    result = service.execute_payment(payment())
    ledger.outage = True
    replay = service.execute_payment(payment())
    assert result.status is PaymentStatus.FAILED
    assert result.transaction_id == ledger.expected_hash
    assert replay == result
    assert ledger.broadcasts == 1
    assert ledger.receipt_queries == 0
    assert ledger.get_payment(result.payment_id).status is PaymentStatus.FAILED
    with psycopg.connect(TEST_DSN) as connection:
        assert connection.execute(
            """
            SELECT status, receipt_status, transaction_hash
            FROM blockchain_operations WHERE payment_id = %s
            """,
            (result.payment_id,),
        ).fetchone() == ("FAILED", 0, result.transaction_id)
    assert isinstance(result, LedgerResult)


@pytest.mark.parametrize(
    "receipt",
    [
        None,
        [],
        {},
        {"status": "1", "gasUsed": 42_000},
        {"status": "malformed", "gasUsed": 42_000},
        {"status": True, "gasUsed": 42_000},
        {"status": 2, "gasUsed": 42_000},
        {"status": 1},
        {"status": 1, "gasUsed": "42000"},
        {"status": 1, "gasUsed": -1},
    ],
)
def test_malformed_or_ambiguous_receipt_becomes_unknown_without_raw_error(
    blockchain_harness: BlockchainHarness, receipt: Any
) -> None:
    class MalformedReceiptLedger(BlockchainLedger):
        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            return Web3.keccak(raw_transaction)

        def _wait_for_receipt(self, transaction_hash: str):
            return receipt

    ledger = blockchain_harness.ledger(MalformedReceiptLedger)
    result = PaymentService(ledger).execute_payment(payment())

    assert result.status is PaymentStatus.UNKNOWN
    assert result.transaction_id is not None
    assert ledger.get_payment(result.payment_id).status is PaymentStatus.UNKNOWN
    assert ledger.get_transaction(result.transaction_id).status is PaymentStatus.UNKNOWN


def test_provider_receipt_exception_becomes_unknown_without_raw_error(
    blockchain_harness: BlockchainHarness,
) -> None:
    class ProviderFormatFailureLedger(BlockchainLedger):
        def _broadcast_raw_transaction(self, raw_transaction: bytes):
            return Web3.keccak(raw_transaction)

        def _wait_for_receipt(self, transaction_hash: str):
            raise ValueError("malformed provider receipt")

    result = PaymentService(
        blockchain_harness.ledger(ProviderFormatFailureLedger)
    ).execute_payment(payment())

    assert result.status is PaymentStatus.UNKNOWN
    assert result.transaction_id is not None


def test_duplicate_participant_addresses_are_rejected_before_activity(
    blockchain_harness: BlockchainHarness, anvil_node: AnvilNode
) -> None:
    payer = blockchain_harness.identities["C001"]
    duplicate_identities = {
        "C001": payer,
        "M001": SigningIdentity(payer.address.lower(), payer.private_key),
    }
    with pytest.raises(ValueError, match="must be distinct"):
        BlockchainLedger(
            blockchain_harness.web3,
            blockchain_harness.contract,
            TEST_DSN,
            duplicate_identities,
        )

    block_before = anvil_node.web3.eth.block_number
    admin, payer_account, _ = anvil_node.accounts
    with pytest.raises(ValueError, match="must be distinct"):
        deploy_demo_contract(
            anvil_node.web3,
            "out/PaymentLedger.sol/PaymentLedger.json",
            admin.key.hex(),
            {"C001": payer_account.key.hex(), "M001": payer_account.key.hex()},
        )
    assert anvil_node.web3.eth.block_number == block_before


def test_c07_test_dsn_guard_accepts_only_the_explicit_loopback_target() -> None:
    validated_dsn = _validated_c07_test_dsn(
        "postgresql://upi@127.0.0.1:55432/upi_payment_test"
    )

    parameters = conninfo_to_dict(validated_dsn)
    assert parameters["host"] == "127.0.0.1"
    assert parameters["dbname"] == "upi_payment_test"
    assert parameters.get("hostaddr") in (None, "")
    assert parameters.get("service") in (None, "")


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://upi@example.com:55432/upi_payment_test",
        "postgresql://upi@203.0.113.10:55432/upi_payment_test",
        "postgresql://upi@localhost:55432/upi_payment_test?hostaddr=127.0.0.1",
        "postgresql://upi@localhost:55432/upi_payment_test?service=remote",
        "postgresql://upi@127.0.0.1:55432/other_database",
        "postgresql:///upi_payment_test",
    ],
)
def test_c07_test_dsn_guard_rejects_unsafe_targets_before_database_activity(
    monkeypatch: pytest.MonkeyPatch, dsn: str
) -> None:
    connection_attempts = 0

    def forbid_connection(*args: object, **kwargs: object) -> None:
        nonlocal connection_attempts
        connection_attempts += 1
        raise AssertionError("test DSN validation must run before database activity")

    monkeypatch.setattr(psycopg, "connect", forbid_connection)

    with pytest.raises(ValueError):
        _validated_c07_test_dsn(dsn)

    assert connection_attempts == 0


@pytest.mark.parametrize(
    ("environment_name", "value"),
    [
        ("PGHOST", "203.0.113.10"),
        ("PGHOSTADDR", "203.0.113.10"),
        ("PGSERVICE", "remote-service"),
        ("PGSERVICEFILE", "/tmp/remote-service.conf"),
    ],
)
def test_c07_test_dsn_guard_rejects_implicit_target_environment(
    monkeypatch: pytest.MonkeyPatch, environment_name: str, value: str
) -> None:
    monkeypatch.setenv(environment_name, value)

    with pytest.raises(ValueError, match="implicit libpq"):
        _validated_c07_test_dsn(
            "postgresql://upi@127.0.0.1:55432/upi_payment_test"
        )


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://upi@example.com:55432/upi_payment_test",
        "postgresql://upi@127.0.0.1:55432/other_database",
        "postgresql://upi@localhost:55432/upi_payment_test?hostaddr=203.0.113.10",
        "service=remote dbname=upi_payment_test host=localhost",
        "postgresql:///upi_payment_test",
    ],
)
def test_blockchain_bootstrap_rejects_ambiguous_or_nonlocal_database_targets(
    dsn: str,
) -> None:
    with pytest.raises(ValueError):
        _validated_local_demo_dsn(dsn)


def test_blockchain_bootstrap_rejects_implicit_database_target_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGHOST", "example.com")
    with pytest.raises(ValueError, match="implicit libpq"):
        _validated_local_demo_dsn(TEST_DSN)


@pytest.mark.parametrize(
    "rpc_url",
    [
        "https://127.0.0.1:8545",
        "http://example.com:8545",
        "http://0.0.0.0:8545",
        "http://127.0.0.1:8545/rpc",
        "http://127.0.0.1",
        "http://user:password@127.0.0.1:8545",
    ],
)
def test_blockchain_bootstrap_rejects_nonlocal_or_ambiguous_rpc_urls(
    rpc_url: str,
) -> None:
    with pytest.raises(ValueError):
        _validated_local_anvil_rpc_url(rpc_url)


def test_blockchain_bootstrap_accepts_explicit_local_targets() -> None:
    assert "dbname=upi_payment_test" in _validated_local_demo_dsn(TEST_DSN)
    assert "host=localhost" in _validated_local_demo_dsn(
        "postgresql://upi@localhost:55432/upi_payment_test"
    )
    assert (
        _validated_local_anvil_rpc_url("http://127.0.0.1:8545")
        == "http://127.0.0.1:8545"
    )
    assert (
        _validated_local_anvil_rpc_url("http://localhost:8545/")
        == "http://localhost:8545/"
    )


@pytest.mark.parametrize(
    "rpc_url",
    [
        "https://mainnet.infura.io/v3/example",
        "http://example.com:8545",
        "http://192.0.2.10:8545",
        "http://0.0.0.0:8545",
        "http://127.0.0.1",
        "http://user:password@127.0.0.1:8545",
        "not-a-url",
    ],
)
def test_runtime_environment_rejects_unsafe_rpc_before_signing(
    monkeypatch: pytest.MonkeyPatch, rpc_url: str
) -> None:
    _configure_runtime_environment(monkeypatch, rpc_url=rpc_url)

    with pytest.raises(RuntimeError, match="local Anvil runtime configuration"):
        BlockchainLedger.from_environment()


@pytest.mark.parametrize(
    ("client_version", "chain_id"),
    [
        ("Geth/v1.14.0", LOCAL_ANVIL_CHAIN_ID),
        ("anvil/v1.8.3", 1),
    ],
)
def test_runtime_environment_rejects_reachable_non_anvil_or_wrong_chain(
    monkeypatch: pytest.MonkeyPatch, client_version: str, chain_id: int
) -> None:
    with _local_json_rpc_server(
        client_version=client_version, chain_id=chain_id
    ) as rpc_url:
        _configure_runtime_environment(monkeypatch, rpc_url=rpc_url)

        with pytest.raises(RuntimeError, match="local Anvil runtime configuration"):
            BlockchainLedger.from_environment()


def test_runtime_environment_accepts_and_executes_on_local_anvil(
    monkeypatch: pytest.MonkeyPatch,
    blockchain_harness: BlockchainHarness,
) -> None:
    _configure_runtime_environment(
        monkeypatch,
        rpc_url=blockchain_harness.web3.provider.endpoint_uri,
        contract_address=blockchain_harness.contract.address,
        identities=blockchain_harness.identities,
    )

    ledger = BlockchainLedger.from_environment()
    result = PaymentService(ledger).execute_payment(
        payment(payment_id="PAY-C07-RUNTIME-LOCAL", idempotency_key="IDEM-C07-RUNTIME-LOCAL")
    )

    assert result.status is PaymentStatus.SUCCESS
    assert ledger.get_balance("C001") == 90_000
    assert ledger.get_balance("M001") == 10_000


def test_deterministic_history_ordering(blockchain_harness: BlockchainHarness) -> None:
    ledger = blockchain_harness.ledger()
    service = PaymentService(ledger)
    first = service.execute_payment(payment(payment_id="PAY-B", idempotency_key="IDEM-B"))
    second = service.execute_payment(
        payment(payment_id="PAY-A", idempotency_key="IDEM-A", amount=1)
    )
    history = ledger.list_transactions()
    expected = sorted(
        [first.transaction_id, second.transaction_id],
    )
    assert [transaction.transaction_id for transaction in history] == expected


def test_same_raw_identifiers_are_isolated_across_ledgers(
    blockchain_harness: BlockchainHarness,
) -> None:
    bootstrap_demo(TEST_DSN)
    shared = payment(payment_id="PAY-SHARED", idempotency_key="IDEM-SHARED")
    conventional = PaymentService(
        ConventionalLedger(
            TEST_DSN,
            transaction_id_factory=lambda: "TX-CONVENTIONAL-SHARED",
            clock=lambda: PAYMENT_TIME,
        )
    )
    blockchain = PaymentService(blockchain_harness.ledger())

    conventional_result = conventional.execute_payment(shared)
    blockchain_result = blockchain.execute_payment(shared)

    assert conventional_result.status is PaymentStatus.SUCCESS
    assert blockchain_result.status is PaymentStatus.SUCCESS
    assert conventional_result.transaction_id != blockchain_result.transaction_id
    assert conventional.get_balance("C001") == 90_000
    assert blockchain.get_balance("C001") == 90_000
    with psycopg.connect(TEST_DSN) as connection:
        assert connection.execute(
            "SELECT count(*) FROM idempotency_records WHERE idempotency_key = %s",
            ("IDEM-SHARED",),
        ).fetchone()[0] == 1
        assert connection.execute(
            """
            SELECT count(*) FROM blockchain_idempotency_records
            WHERE ledger_type = 'blockchain' AND idempotency_key = %s
            """,
            ("IDEM-SHARED",),
        ).fetchone()[0] == 1


@pytest.mark.anyio
async def test_api_selector_defaults_and_routes_reads_consistently() -> None:
    class MemoryLedger:
        def __init__(self, ledger_type: str) -> None:
            self.ledger_type = ledger_type
            self.executions = 0

        def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
            return 100_000 if self.ledger_type == "ConventionalLedger" else 200_000

        def execute_payment(
            self, candidate: Payment, *, request_fingerprint: str
        ) -> LedgerResult:
            self.executions += 1
            return LedgerResult(candidate.payment_id, f"TX-{self.ledger_type}", PaymentStatus.SUCCESS)

        def get_payment(self, payment_id: str) -> Payment | None:
            return None

        def get_transaction(self, transaction_id: str) -> Transaction | None:
            return None

        def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
            return []

    conventional = MemoryLedger("ConventionalLedger")
    blockchain = MemoryLedger("BlockchainLedger")
    app = create_app(
        PaymentService(conventional),
        services={
            "conventional": PaymentService(conventional),
            "blockchain": PaymentService(blockchain),
        },
        clock=lambda: PAYMENT_TIME,
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        default_balance = await client.get("/accounts/C001/balance")
        blockchain_balance = await client.get(
            "/accounts/C001/balance?ledger=blockchain"
        )
        response = await client.post(
            "/payments?ledger=blockchain",
            json={
                "payment_id": "PAY-API",
                "payer_id": "C001",
                "merchant_id": "M001",
                "amount": 10_000,
                "currency": "SEK",
                "idempotency_key": "IDEM-API",
            },
        )
    assert default_balance.json()["balance_ore"] == 100_000
    assert blockchain_balance.json()["balance_ore"] == 200_000
    assert response.status_code == 200
    assert blockchain.executions == 1
    assert conventional.executions == 0


@pytest.mark.anyio
async def test_real_api_end_to_end_runs_both_ledgers_through_shared_boundary(
    blockchain_harness: BlockchainHarness,
) -> None:
    bootstrap_demo(TEST_DSN)
    conventional = PaymentService(
        ConventionalLedger(
            TEST_DSN,
            transaction_id_factory=lambda: "TX-C07-DEMO-CONVENTIONAL",
            clock=lambda: PAYMENT_TIME,
        )
    )
    blockchain = PaymentService(blockchain_harness.ledger())
    app = create_app(
        conventional,
        services={"conventional": conventional, "blockchain": blockchain},
        clock=lambda: PAYMENT_TIME,
    )
    payload = {
        "payment_id": "PAY-C07-DEMO",
        "payer_id": "C001",
        "merchant_id": "M001",
        "amount": 10_000,
        "currency": "SEK",
        "idempotency_key": "IDEM-C07-DEMO",
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        qr = await client.get("/merchants/M001/qr")
        conventional_result = await client.post("/payments", json=payload)
        blockchain_result = await client.post(
            "/payments?ledger=blockchain", json=payload
        )
        conventional_customer = await client.get("/accounts/C001/balance")
        conventional_merchant = await client.get("/accounts/M001/balance")
        blockchain_customer = await client.get(
            "/accounts/C001/balance?ledger=blockchain"
        )
        blockchain_merchant = await client.get(
            "/accounts/M001/balance?ledger=blockchain"
        )
        blockchain_history = await client.get(
            "/transactions?ledger=blockchain"
        )
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert conventional_result.json()["status"] == "SUCCESS"
    assert blockchain_result.json()["status"] == "SUCCESS"
    assert blockchain_result.json()["transaction_id"].startswith("0x")
    assert conventional_customer.json()["balance_ore"] == 90_000
    assert conventional_merchant.json()["balance_ore"] == 10_000
    assert blockchain_customer.json()["balance_ore"] == 90_000
    assert blockchain_merchant.json()["balance_ore"] == 10_000
    assert blockchain_history.json()["transactions"][0]["ledger_type"] == (
        "BlockchainLedger"
    )


@pytest.mark.anyio
async def test_selector_is_transport_only_and_unavailable_ledger_is_explicit() -> None:
    class NoopLedger:
        def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
            return 0

        def execute_payment(
            self, candidate: Payment, *, request_fingerprint: str
        ) -> LedgerResult:
            return LedgerResult(candidate.payment_id, "TX", PaymentStatus.SUCCESS)

        def get_payment(self, payment_id: str) -> Payment | None:
            return None

        def get_transaction(self, transaction_id: str) -> Transaction | None:
            return None

        def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
            return []

    app = create_app(PaymentService(NoopLedger()), clock=lambda: PAYMENT_TIME)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        unavailable = await client.get(
            "/accounts/C001/balance?ledger=blockchain"
        )
        invalid = await client.get("/accounts/C001/balance?ledger=other")
        schema = (await client.get("/openapi.json")).json()
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"]["code"] == "LEDGER_UNAVAILABLE"
    assert invalid.status_code == 422
    payment_schema = schema["components"]["schemas"]["PaymentRequest"]
    assert "ledger" not in payment_schema["properties"]
