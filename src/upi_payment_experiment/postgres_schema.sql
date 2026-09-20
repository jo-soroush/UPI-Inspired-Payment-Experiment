CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'SEK'),
    balance BIGINT NOT NULL CHECK (balance >= 0),
    UNIQUE (owner_id, currency)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    payer_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    merchant_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL CHECK (currency = 'SEK'),
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'UNKNOWN')),
    created_at TIMESTAMPTZ NOT NULL,
    CHECK (payer_account_id <> merchant_account_id)
);

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS request_fingerprint TEXT;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL UNIQUE REFERENCES payments(payment_id),
    ledger_type TEXT NOT NULL CHECK (ledger_type <> ''),
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'UNKNOWN')),
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS transactions_timestamp_idx
    ON transactions (timestamp, transaction_id);

CREATE TABLE IF NOT EXISTS idempotency_records (
    idempotency_key TEXT PRIMARY KEY,
    request_fingerprint TEXT NOT NULL,
    payment_id TEXT NOT NULL REFERENCES payments(payment_id)
);
