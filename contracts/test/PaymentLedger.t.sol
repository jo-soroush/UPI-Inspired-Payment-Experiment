// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {PaymentLedger} from "../PaymentLedger.sol";

interface Vm {
    function expectEmit(bool, bool, bool, bool) external;
    function prank(address) external;
}

contract PaymentLedgerTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    bytes32 private constant C001 = keccak256("C001");
    bytes32 private constant M001 = keccak256("M001");
    bytes32 private constant PAYMENT = keccak256("PAY-C07-001");
    address private constant PAYER = address(0xC001);
    address private constant MERCHANT = address(0x1001);
    address private constant STRANGER = address(0xBAD);

    PaymentLedger private ledger;

    event PaymentExecuted(
        bytes32 indexed paymentId,
        bytes32 indexed payerId,
        bytes32 indexed merchantId,
        uint256 amount,
        address sender
    );

    function setUp() public {
        ledger = new PaymentLedger(address(this));
        ledger.registerParticipant(C001, PAYER);
        ledger.registerParticipant(M001, MERCHANT);
        ledger.seedBalance(C001, 100_000);
        ledger.seedBalance(M001, 0);
    }

    function testInitialFixtureAndParticipantMapping() public view {
        require(ledger.knownParticipant(C001));
        require(ledger.knownParticipant(M001));
        require(ledger.authorizedAddress(C001) == PAYER);
        require(ledger.authorizedAddress(M001) == MERCHANT);
        require(ledger.getBalance(C001) == 100_000);
        require(ledger.getBalance(M001) == 0);
    }

    function testOnlyOwnerCanRegisterAndSeed() public {
        bytes32 other = keccak256("C002");
        vm.prank(STRANGER);
        (bool registered,) =
            address(ledger).call(abi.encodeCall(ledger.registerParticipant, (other, STRANGER)));
        require(!registered);

        vm.prank(STRANGER);
        (bool seeded,) = address(ledger).call(abi.encodeCall(ledger.seedBalance, (C001, 1)));
        require(!seeded);
        require(ledger.getBalance(C001) == 100_000);
    }

    function testSuccessfulPaymentEmitsEvidenceAndExactDeltas() public {
        vm.expectEmit(true, true, true, true);
        emit PaymentExecuted(PAYMENT, C001, M001, 10_000, PAYER);
        vm.prank(PAYER);
        ledger.pay(PAYMENT, C001, M001, 10_000);

        require(ledger.getBalance(C001) == 90_000);
        require(ledger.getBalance(M001) == 10_000);
        require(ledger.isProcessed(PAYMENT));
    }

    function testZeroAmountRevertsWithoutMutation() public {
        _assertFailedPayment(PAYMENT, C001, M001, 0, PAYER);
    }

    function testInsufficientFundsRevertsWithoutMutation() public {
        _assertFailedPayment(PAYMENT, C001, M001, 100_001, PAYER);
    }

    function testUnknownPayerRevertsWithoutMutation() public {
        _assertFailedPayment(PAYMENT, keccak256("C999"), M001, 1, PAYER);
    }

    function testUnknownMerchantRevertsWithoutMutation() public {
        _assertFailedPayment(PAYMENT, C001, keccak256("M999"), 1, PAYER);
    }

    function testUnauthorizedSignerRevertsWithoutMutation() public {
        _assertFailedPayment(PAYMENT, C001, M001, 10_000, STRANGER);
    }

    function testProcessedPaymentCannotTransferTwice() public {
        vm.prank(PAYER);
        ledger.pay(PAYMENT, C001, M001, 10_000);
        _assertBalances(90_000, 10_000);

        vm.prank(PAYER);
        (bool success,) =
            address(ledger).call(abi.encodeCall(ledger.pay, (PAYMENT, C001, M001, 10_000)));
        require(!success);
        _assertBalances(90_000, 10_000);
    }

    function testFuzzSuccessfulPaymentConservesValueAndUsesExactDeltas(uint96 rawAmount) public {
        uint256 amount = (uint256(rawAmount) % 100_000) + 1;
        bytes32 paymentId = keccak256(abi.encode(rawAmount));
        uint256 totalBefore = ledger.getBalance(C001) + ledger.getBalance(M001);

        vm.prank(PAYER);
        ledger.pay(paymentId, C001, M001, amount);

        require(ledger.getBalance(C001) == 100_000 - amount);
        require(ledger.getBalance(M001) == amount);
        require(ledger.getBalance(C001) + ledger.getBalance(M001) == totalBefore);
    }

    function _assertFailedPayment(
        bytes32 paymentId,
        bytes32 payerId,
        bytes32 merchantId,
        uint256 amount,
        address sender
    ) private {
        uint256 payerBefore = ledger.getBalance(C001);
        uint256 merchantBefore = ledger.getBalance(M001);
        vm.prank(sender);
        (bool success,) = address(ledger)
            .call(abi.encodeCall(ledger.pay, (paymentId, payerId, merchantId, amount)));
        require(!success);
        require(ledger.getBalance(C001) == payerBefore);
        require(ledger.getBalance(M001) == merchantBefore);
        require(!ledger.isProcessed(paymentId));
    }

    function _assertBalances(uint256 payer, uint256 merchant) private view {
        require(ledger.getBalance(C001) == payer);
        require(ledger.getBalance(M001) == merchant);
    }
}
