"""Explicit local-Anvil deployment for the deterministic C07 demo fixture."""

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import psycopg
from psycopg.conninfo import conninfo_to_dict
from web3 import HTTPProvider, Web3

from .conventional_ledger import ConventionalLedger
from .demo_bootstrap import (
    IMPLICIT_TARGET_ENVIRONMENT,
    _validated_demo_dsn,
    _without_implicit_target_environment,
)


LOCAL_ANVIL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
LOCAL_ANVIL_CHAIN_ID = 31_337


def deploy_demo_contract(
    web3: Web3,
    artifact_path: str | Path,
    admin_private_key: str,
    participant_private_keys: dict[str, str],
) -> str:
    """Deploy and initialize one fresh local-only PaymentLedger contract."""

    artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    admin = web3.eth.account.from_key(admin_private_key)
    participants = {
        identity: web3.eth.account.from_key(participant_private_keys[identity])
        for identity in ("C001", "M001")
    }
    normalized_addresses = {
        Web3.to_checksum_address(participant.address).lower()
        for participant in participants.values()
    }
    if len(normalized_addresses) != len(participants):
        raise ValueError("participant Ethereum addresses must be distinct")
    factory = web3.eth.contract(
        abi=artifact["abi"], bytecode=artifact["bytecode"]["object"]
    )
    deployment = factory.constructor(admin.address).build_transaction(
        _transaction_parameters(web3, admin.address, gas=2_500_000)
    )
    receipt = _send_and_wait(web3, admin, deployment)
    contract = web3.eth.contract(address=receipt["contractAddress"], abi=artifact["abi"])

    for identity, balance in (("C001", 100_000), ("M001", 0)):
        participant = participants[identity]
        registration = contract.functions.registerParticipant(
            Web3.keccak(text=identity), participant.address
        ).build_transaction(_transaction_parameters(web3, admin.address))
        _send_and_wait(web3, admin, registration)
        seeding = contract.functions.seedBalance(
            Web3.keccak(text=identity), balance
        ).build_transaction(_transaction_parameters(web3, admin.address))
        _send_and_wait(web3, admin, seeding)
    return Web3.to_checksum_address(receipt["contractAddress"])


def _transaction_parameters(
    web3: Web3, address: str, *, gas: int = 500_000
) -> dict[str, int | str]:
    return {
        "chainId": web3.eth.chain_id,
        "from": address,
        "gas": gas,
        "gasPrice": web3.eth.gas_price,
        "nonce": web3.eth.get_transaction_count(address, "pending"),
    }


def _send_and_wait(web3: Web3, account: Any, transaction: dict[str, Any]):
    signed = account.sign_transaction(transaction)
    transaction_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
    if int(receipt["status"]) != 1:
        raise RuntimeError("local Anvil fixture transaction failed")
    return receipt


def reset_operation_journal(dsn: str) -> None:
    """Align the operational journal with a deliberately fresh local chain."""

    validated_dsn = _validated_local_demo_dsn(dsn)
    with _without_implicit_target_environment():
        _reset_operation_journal(validated_dsn)


def _reset_operation_journal(validated_dsn: str) -> None:
    with psycopg.connect(validated_dsn) as connection:
        connection.execute(
            "TRUNCATE blockchain_idempotency_records, blockchain_operations"
        )


def _validated_local_demo_dsn(dsn: str) -> str:
    """Require an explicit local demo database without libpq target overrides."""

    if any(os.environ.get(name) for name in IMPLICIT_TARGET_ENVIRONMENT):
        raise ValueError(
            "implicit libpq target environment is not allowed for C07 bootstrap"
        )
    parameters = conninfo_to_dict(dsn)
    if not parameters.get("host") and not parameters.get("hostaddr"):
        raise ValueError("C07 bootstrap requires an explicit local database host")
    return _validated_demo_dsn(dsn)


def _validated_local_anvil_rpc_url(rpc_url: str) -> str:
    """Accept only an explicit loopback HTTP endpoint for local Anvil."""

    if not isinstance(rpc_url, str) or not rpc_url.strip():
        raise ValueError("Anvil RPC URL must be a non-empty string")
    try:
        parsed = urlsplit(rpc_url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Anvil RPC URL is invalid") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname not in LOCAL_ANVIL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or port is None
    ):
        raise ValueError("Anvil RPC URL must be an explicit local loopback HTTP endpoint")
    return rpc_url


def _validated_local_anvil_connection(web3: Web3) -> None:
    """Require the configured endpoint to be the expected local Anvil chain."""

    try:
        if not web3.is_connected():
            raise ValueError("local Anvil RPC is unavailable")
        if "anvil" not in web3.client_version.lower():
            raise ValueError("RPC endpoint is not a local Anvil node")
        if int(web3.eth.chain_id) != LOCAL_ANVIL_CHAIN_ID:
            raise ValueError("RPC endpoint has an unexpected local Anvil chain ID")
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("local Anvil identity check failed") from error


def main() -> None:
    """Deploy only when deliberately invoked with local test-key configuration."""

    rpc_url = os.environ.get("UPI_ANVIL_RPC_URL", "http://127.0.0.1:8545")
    artifact_path = os.environ.get(
        "UPI_PAYMENT_LEDGER_ARTIFACT", "out/PaymentLedger.sol/PaymentLedger.json"
    )
    journal_dsn = os.environ.get("UPI_DATABASE_DSN")
    admin_key = os.environ.get("UPI_ANVIL_ADMIN_PRIVATE_KEY")
    participant_keys = {
        "C001": os.environ.get("UPI_ANVIL_C001_PRIVATE_KEY"),
        "M001": os.environ.get("UPI_ANVIL_M001_PRIVATE_KEY"),
    }
    if not journal_dsn or not admin_key or any(not key for key in participant_keys.values()):
        raise SystemExit(
            "UPI_DATABASE_DSN and local Anvil admin/C001/M001 test keys are required"
        )
    try:
        validated_dsn = _validated_local_demo_dsn(journal_dsn)
        validated_rpc_url = _validated_local_anvil_rpc_url(rpc_url)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    web3 = Web3(HTTPProvider(validated_rpc_url))
    try:
        _validated_local_anvil_connection(web3)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    with _without_implicit_target_environment():
        ConventionalLedger(validated_dsn).initialize_schema()
        _reset_operation_journal(validated_dsn)
    contract_address = deploy_demo_contract(
        web3,
        artifact_path,
        admin_key,
        {identity: str(key) for identity, key in participant_keys.items()},
    )
    print(f"C07 local PaymentLedger ready: {contract_address}")
    print("Set UPI_PAYMENT_LEDGER_ADDRESS to this local contract address.")
