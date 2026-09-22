// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract PaymentLedger is Ownable {
    error AlreadyProcessed(bytes32 paymentId);
    error AlreadySeeded(bytes32 participantId);
    error InsufficientFunds(bytes32 payerId, uint256 balance, uint256 amount);
    error InvalidAddress();
    error InvalidAmount();
    error ParticipantAlreadyRegistered(bytes32 participantId);
    error UnauthorizedPayer(bytes32 payerId, address sender);
    error UnknownParticipant(bytes32 participantId);

    mapping(bytes32 participantId => address) public authorizedAddress;
    mapping(bytes32 participantId => bool) public knownParticipant;
    mapping(bytes32 participantId => bool) public seededParticipant;
    mapping(bytes32 participantId => uint256) private balances;
    mapping(bytes32 paymentId => bool) private processedPayments;

    event ParticipantRegistered(bytes32 indexed participantId, address indexed account);
    event BalanceSeeded(bytes32 indexed participantId, uint256 amount);
    event PaymentExecuted(
        bytes32 indexed paymentId,
        bytes32 indexed payerId,
        bytes32 indexed merchantId,
        uint256 amount,
        address sender
    );

    constructor(address initialOwner) Ownable(initialOwner) {}

    function registerParticipant(bytes32 participantId, address account) external onlyOwner {
        if (participantId == bytes32(0) || account == address(0)) revert InvalidAddress();
        if (knownParticipant[participantId]) revert ParticipantAlreadyRegistered(participantId);
        knownParticipant[participantId] = true;
        // forge-lint: disable-next-line(missing-events-access-control)
        authorizedAddress[participantId] = account;
        emit ParticipantRegistered(participantId, account);
    }

    function seedBalance(bytes32 participantId, uint256 amount) external onlyOwner {
        if (!knownParticipant[participantId]) revert UnknownParticipant(participantId);
        if (seededParticipant[participantId]) revert AlreadySeeded(participantId);
        seededParticipant[participantId] = true;
        balances[participantId] = amount;
        emit BalanceSeeded(participantId, amount);
    }

    function getBalance(bytes32 participantId) external view returns (uint256) {
        if (!knownParticipant[participantId]) revert UnknownParticipant(participantId);
        return balances[participantId];
    }

    function isProcessed(bytes32 paymentId) external view returns (bool) {
        return processedPayments[paymentId];
    }

    function pay(bytes32 paymentId, bytes32 payerId, bytes32 merchantId, uint256 amount) external {
        if (!knownParticipant[payerId]) revert UnknownParticipant(payerId);
        if (!knownParticipant[merchantId]) revert UnknownParticipant(merchantId);
        if (amount == 0) revert InvalidAmount();
        if (authorizedAddress[payerId] != msg.sender) {
            revert UnauthorizedPayer(payerId, msg.sender);
        }
        if (processedPayments[paymentId]) revert AlreadyProcessed(paymentId);

        uint256 payerBalance = balances[payerId];
        if (payerBalance < amount) revert InsufficientFunds(payerId, payerBalance, amount);

        balances[payerId] = payerBalance - amount;
        balances[merchantId] += amount;
        processedPayments[paymentId] = true;

        emit PaymentExecuted(paymentId, payerId, merchantId, amount, msg.sender);
    }
}
