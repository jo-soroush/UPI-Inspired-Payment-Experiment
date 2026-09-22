"""LedgerInterface adapter for the local Anvil PaymentLedger contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider, Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound

from .blockchain_journal import (
    BlockchainOperation,
    BlockchainOperationJournal,
    PreparedTransaction,
)
from .blockchain_bootstrap import (
    _validated_local_anvil_connection,
    _validated_local_anvil_rpc_url,
)
from .domain import LedgerResult, Payment, PaymentStatus, Transaction
from .errors import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidPaymentError,
    PaymentError,
    PaymentInfrastructureError,
)


@dataclass(frozen=True)
class SigningIdentity:
    """Backend-only local Anvil signing identity."""

    address: str
    private_key: str


class BlockchainLedger:
    """Execute the shared payment semantics against a local EVM contract."""

    ledger_type = "BlockchainLedger"

    def __init__(
        self,
        web3: Web3,
        contract: Contract,
        journal_dsn: str,
        identities: dict[str, SigningIdentity],
        *,
        receipt_timeout: float = 10.0,
        clock: Any | None = None,
    ) -> None:
        self._web3 = web3
        self._contract = contract
        self._journal = BlockchainOperationJournal(journal_dsn)
        self._journal_dsn = journal_dsn
        self._identities = dict(identities)
        self._receipt_timeout = receipt_timeout
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        identities_by_address: dict[str, str] = {}
        for identity, signing_identity in self._identities.items():
            if not identity.strip():
                raise ValueError("application identity must be non-empty")
            account = self._web3.eth.account.from_key(signing_identity.private_key)
            configured_address = Web3.to_checksum_address(signing_identity.address)
            if account.address != configured_address:
                raise ValueError(f"private key does not match address for {identity}")
            normalized_address = configured_address.lower()
            existing_identity = identities_by_address.get(normalized_address)
            if existing_identity is not None:
                raise ValueError(
                    "participant Ethereum addresses must be distinct: "
                    f"{existing_identity} and {identity} resolve to the same address"
                )
            identities_by_address[normalized_address] = identity

    @classmethod
    def from_environment(cls) -> "BlockchainLedger":
        """Build the local-only adapter without embedding test keys in source."""

        rpc_url = os.environ.get("UPI_ANVIL_RPC_URL", "http://127.0.0.1:8545")
        contract_address = os.environ.get("UPI_PAYMENT_LEDGER_ADDRESS")
        journal_dsn = os.environ.get("UPI_DATABASE_DSN")
        artifact_path = os.environ.get(
            "UPI_PAYMENT_LEDGER_ARTIFACT",
            "out/PaymentLedger.sol/PaymentLedger.json",
        )
        identity_keys = {
            "C001": os.environ.get("UPI_ANVIL_C001_PRIVATE_KEY"),
            "M001": os.environ.get("UPI_ANVIL_M001_PRIVATE_KEY"),
        }
        if not contract_address or not journal_dsn:
            raise RuntimeError(
                "UPI_PAYMENT_LEDGER_ADDRESS and UPI_DATABASE_DSN must be configured"
            )
        if any(not key for key in identity_keys.values()):
            raise RuntimeError(
                "local Anvil fixture addresses and private keys must be configured"
            )
        try:
            validated_rpc_url = _validated_local_anvil_rpc_url(rpc_url)
            web3 = Web3(HTTPProvider(validated_rpc_url))
            _validated_local_anvil_connection(web3)
        except ValueError as error:
            raise RuntimeError("local Anvil runtime configuration was rejected") from error
        artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=artifact["abi"],
        )
        identities = {}
        for identity, key in identity_keys.items():
            account = web3.eth.account.from_key(str(key))
            identities[identity] = SigningIdentity(account.address, str(key))
        return cls(web3, contract, journal_dsn, identities)

    def initialize_schema(self) -> None:
        """Create the existing schema, including the operation journal."""

        from .conventional_ledger import ConventionalLedger

        ConventionalLedger(self._journal_dsn).initialize_schema()

    def get_balance(self, owner_id: str, currency: str = "SEK") -> int:
        if currency != "SEK":
            raise InvalidPaymentError(f"unsupported currency: {currency}")
        self._require_known_identity(owner_id)
        try:
            return int(
                self._contract.functions.getBalance(
                    self._identity_hash(owner_id)
                ).call()
            )
        except Exception as error:
            raise PaymentInfrastructureError(
                "blockchain balance lookup is unavailable"
            ) from error

    def execute_payment(
        self, payment: Payment, *, request_fingerprint: str
    ) -> LedgerResult:
        if payment.payer_id == payment.merchant_id:
            raise InvalidPaymentError("payer and merchant must be different")
        if not isinstance(request_fingerprint, str) or not request_fingerprint:
            raise ValueError("request_fingerprint must be a non-empty string")

        operation, created = self._journal.prepare(
            payment,
            request_fingerprint,
            self._clock(),
            lambda reserved_nonce: self._build_signed_transaction(
                payment, reserved_nonce
            ),
        )
        if not created:
            if operation.status in {"SUCCESS", "FAILED"}:
                return self._result_from_operation(operation)
            return self._reconcile(operation, allow_exact_rebroadcast=True)
        return self._submit_new(operation)

    def get_payment(self, payment_id: str) -> Payment | None:
        operation = self._journal.get_by_payment_id(payment_id)
        if operation is None:
            return None
        return self._payment_from_operation(operation)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        operation = self._journal.get_by_transaction_hash(transaction_id)
        if operation is None:
            return None
        return self._transaction_from_operation(operation)

    def list_transactions(self, payment_id: str | None = None) -> list[Transaction]:
        return [
            self._transaction_from_operation(operation)
            for operation in self._journal.list_operations(payment_id)
        ]

    def _build_signed_transaction(
        self, payment: Payment, reserved_nonce: int
    ) -> PreparedTransaction:
        try:
            return self._build_signed_transaction_with_provider(
                payment, reserved_nonce
            )
        except PaymentError:
            raise
        except Exception as error:
            raise PaymentInfrastructureError(
                "blockchain transaction preparation is unavailable"
            ) from error

    def _build_signed_transaction_with_provider(
        self, payment: Payment, reserved_nonce: int
    ) -> PreparedTransaction:
        payer = self._require_known_identity(payment.payer_id)
        self._require_known_identity(payment.merchant_id)
        on_chain_authorized = Web3.to_checksum_address(
            self._contract.functions.authorizedAddress(
                self._identity_hash(payment.payer_id)
            ).call()
        )
        if on_chain_authorized != Web3.to_checksum_address(payer.address):
            raise InvalidPaymentError("configured signer is not authorized for payer")
        payer_balance = self.get_balance(payment.payer_id, payment.currency)
        if payer_balance < payment.amount:
            raise InsufficientFundsError("payer has insufficient funds")

        account: LocalAccount = self._web3.eth.account.from_key(payer.private_key)
        nonce = max(
            reserved_nonce,
            self._web3.eth.get_transaction_count(account.address, "pending"),
        )
        transaction = self._contract.functions.pay(
            self._payment_hash(payment.payment_id),
            self._identity_hash(payment.payer_id),
            self._identity_hash(payment.merchant_id),
            payment.amount,
        ).build_transaction(
            {
                "chainId": self._web3.eth.chain_id,
                "from": account.address,
                "gas": 500_000,
                "gasPrice": self._web3.eth.gas_price,
                "nonce": nonce,
            }
        )
        signed = account.sign_transaction(transaction)
        return PreparedTransaction(
            transaction_hash=Web3.to_hex(signed.hash),
            sender_address=account.address,
            nonce=nonce,
            signed_raw_transaction=bytes(signed.raw_transaction),
        )

    def _submit_new(self, operation: BlockchainOperation) -> LedgerResult:
        try:
            observed_hash = Web3.to_hex(
                self._broadcast_raw_transaction(operation.signed_raw_transaction)
            )
            if observed_hash.lower() != operation.transaction_hash.lower():
                raise RuntimeError("provider returned a different transaction hash")
            operation = self._journal.update_status(
                operation.payment_id, "SUBMITTED", observed_at=self._clock()
            )
        except Exception:
            operation = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._reconcile(operation, allow_exact_rebroadcast=False)
        return self._resolve_receipt(operation)

    def _reconcile(
        self, operation: BlockchainOperation, *, allow_exact_rebroadcast: bool
    ) -> LedgerResult:
        if operation.status in {"SUCCESS", "FAILED"}:
            return self._result_from_operation(operation)
        try:
            receipt = self._receipt_if_available(operation.transaction_hash)
        except Exception:
            updated = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(updated)
        if receipt is not None:
            return self._apply_receipt(operation, receipt)

        try:
            transaction_is_known = self._transaction_is_known(
                operation.transaction_hash
            )
        except Exception:
            updated = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(updated)
        if transaction_is_known:
            updated = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(updated)

        if not allow_exact_rebroadcast:
            return self._result_from_operation(operation)

        try:
            observed_hash = Web3.to_hex(
                self._broadcast_raw_transaction(operation.signed_raw_transaction)
            )
            if observed_hash.lower() != operation.transaction_hash.lower():
                raise RuntimeError("exact rebroadcast changed transaction hash")
            operation = self._journal.update_status(
                operation.payment_id, "SUBMITTED", observed_at=self._clock()
            )
        except Exception:
            operation = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(operation)
        return self._resolve_receipt(operation)

    def _resolve_receipt(self, operation: BlockchainOperation) -> LedgerResult:
        try:
            receipt = self._wait_for_receipt(operation.transaction_hash)
        except Exception:
            updated = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(updated)
        return self._apply_receipt(operation, receipt)

    def _apply_receipt(
        self, operation: BlockchainOperation, receipt: Any
    ) -> LedgerResult:
        if operation.status in {"SUCCESS", "FAILED"}:
            return self._result_from_operation(operation)
        try:
            receipt_status, gas_used = self._validated_receipt_facts(receipt)
        except PaymentInfrastructureError:
            updated = self._journal.update_status(
                operation.payment_id, "UNKNOWN", observed_at=self._clock()
            )
            return self._result_from_operation(updated)
        status = "SUCCESS" if receipt_status == 1 else "FAILED"
        updated = self._journal.update_status(
            operation.payment_id,
            status,
            observed_at=self._clock(),
            receipt_status=receipt_status,
            gas_used=gas_used,
        )
        return self._result_from_operation(updated)

    @staticmethod
    def _validated_receipt_facts(receipt: Any) -> tuple[int, int]:
        """Accept only an unambiguous EVM receipt status and gas value."""

        if not isinstance(receipt, Mapping):
            raise PaymentInfrastructureError("blockchain receipt has an invalid shape")
        try:
            receipt_status = receipt["status"]
            gas_used = receipt["gasUsed"]
        except Exception as error:
            raise PaymentInfrastructureError(
                "blockchain receipt is missing required fields"
            ) from error
        if (
            isinstance(receipt_status, bool)
            or not isinstance(receipt_status, int)
            or receipt_status not in {0, 1}
        ):
            raise PaymentInfrastructureError(
                "blockchain receipt has an invalid status"
            )
        if isinstance(gas_used, bool) or not isinstance(gas_used, int) or gas_used < 0:
            raise PaymentInfrastructureError(
                "blockchain receipt has an invalid gas value"
            )
        return receipt_status, gas_used

    def _broadcast_raw_transaction(self, raw_transaction: bytes):
        return self._web3.eth.send_raw_transaction(raw_transaction)

    def _wait_for_receipt(self, transaction_hash: str):
        return self._web3.eth.wait_for_transaction_receipt(
            transaction_hash, timeout=self._receipt_timeout, poll_latency=0.05
        )

    def _receipt_if_available(self, transaction_hash: str):
        try:
            return self._web3.eth.get_transaction_receipt(transaction_hash)
        except TransactionNotFound:
            return None

    def _transaction_is_known(self, transaction_hash: str) -> bool:
        try:
            self._web3.eth.get_transaction(transaction_hash)
        except TransactionNotFound:
            return False
        return True

    def _require_known_identity(self, identity: str) -> SigningIdentity:
        signing_identity = self._identities.get(identity)
        if signing_identity is None:
            raise AccountNotFoundError(f"account not found for owner {identity!r}")
        try:
            is_known = self._contract.functions.knownParticipant(
                self._identity_hash(identity)
            ).call()
        except Exception as error:
            raise PaymentInfrastructureError(
                "blockchain participant lookup is unavailable"
            ) from error
        if not is_known:
            raise AccountNotFoundError(f"account not found for owner {identity!r}")
        return signing_identity

    @staticmethod
    def _identity_hash(identity: str) -> bytes:
        return Web3.keccak(text=identity)

    @staticmethod
    def _payment_hash(payment_id: str) -> bytes:
        return Web3.keccak(text=payment_id)

    @staticmethod
    def _payment_from_operation(operation: BlockchainOperation) -> Payment:
        return Payment(
            payment_id=operation.payment_id,
            payer_id=operation.payer_id,
            merchant_id=operation.merchant_id,
            amount=operation.amount,
            currency=operation.currency,
            idempotency_key=operation.original_idempotency_key,
            status=BlockchainLedger._domain_status(operation.status),
            created_at=operation.prepared_at,
        )

    @staticmethod
    def _transaction_from_operation(operation: BlockchainOperation) -> Transaction:
        timestamp = (
            operation.confirmed_at or operation.submitted_at or operation.prepared_at
        )
        return Transaction(
            transaction_id=operation.transaction_hash,
            payment_id=operation.payment_id,
            ledger_type=BlockchainLedger.ledger_type,
            status=BlockchainLedger._domain_status(operation.status),
            timestamp=timestamp,
        )

    @staticmethod
    def _result_from_operation(operation: BlockchainOperation) -> LedgerResult:
        return LedgerResult(
            payment_id=operation.payment_id,
            transaction_id=operation.transaction_hash,
            status=BlockchainLedger._domain_status(operation.status),
        )

    @staticmethod
    def _domain_status(status: str) -> PaymentStatus:
        if status == "SUCCESS":
            return PaymentStatus.SUCCESS
        if status == "FAILED":
            return PaymentStatus.FAILED
        if status == "UNKNOWN":
            return PaymentStatus.UNKNOWN
        return PaymentStatus.PENDING
