import { formatOreAsSek, parseSekToOre } from "./money.js";
const CUSTOMER_ID = "C001";
const MERCHANT_ID = "M001";
let paymentIntentActive = false;
function element(id) {
    const found = document.getElementById(id);
    if (!(found instanceof HTMLElement)) {
        throw new Error(`Required UI element is missing: ${id}`);
    }
    return found;
}
async function readError(response) {
    try {
        const body = (await response.json());
        if (typeof body.detail === "string") {
            return body.detail;
        }
        if (body.detail?.message) {
            return body.detail.code
                ? `${body.detail.code}: ${body.detail.message}`
                : body.detail.message;
        }
    }
    catch {
        // Fall back to the transport status when the response is not JSON.
    }
    return `Request failed (${response.status})`;
}
function selectedLedger() {
    return element("ledger-blockchain").checked
        ? "blockchain"
        : "conventional";
}
function ledgerQuery(ledger) {
    return `ledger=${encodeURIComponent(ledger)}`;
}
function setLedgerControlsDisabled(disabled) {
    for (const id of ["ledger-conventional", "ledger-blockchain"]) {
        element(id).disabled = disabled;
    }
}
async function loadBalance(ownerId, outputId, ledger) {
    const response = await fetch(`/accounts/${encodeURIComponent(ownerId)}/balance?${ledgerQuery(ledger)}`);
    if (!response.ok) {
        throw new Error(await readError(response));
    }
    const balance = (await response.json());
    element(outputId).textContent = formatOreAsSek(balance.balance_ore);
}
async function loadHistory(ledger) {
    const response = await fetch(`/transactions?${ledgerQuery(ledger)}`);
    if (!response.ok) {
        throw new Error(await readError(response));
    }
    const history = (await response.json());
    const body = element("transaction-history");
    body.replaceChildren();
    for (const transaction of history.transactions) {
        const row = document.createElement("tr");
        for (const value of [
            transaction.transaction_id,
            transaction.payment_id,
            transaction.status,
            transaction.ledger_type,
        ]) {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.append(cell);
        }
        body.append(row);
    }
    element("history-empty").hidden = history.transactions.length !== 0;
}
async function refreshBackendState(ledger) {
    await Promise.all([
        loadBalance(CUSTOMER_ID, "customer-balance", ledger),
        loadBalance(MERCHANT_ID, "merchant-balance", ledger),
        loadHistory(ledger),
    ]);
}
async function submitPayment(event) {
    event.preventDefault();
    if (paymentIntentActive) {
        return;
    }
    const ledger = selectedLedger();
    const amountInput = element("amount");
    const status = element("payment-status");
    const transaction = element("transaction-id");
    const timing = element("request-duration");
    const submit = element("pay-button");
    let keepDisabled = false;
    let amount;
    try {
        amount = parseSekToOre(amountInput.value);
    }
    catch (error) {
        status.textContent = error instanceof Error ? error.message : "Invalid amount";
        status.dataset.state = "error";
        return;
    }
    const request = {
        payment_id: crypto.randomUUID(),
        payer_id: CUSTOMER_ID,
        merchant_id: MERCHANT_ID,
        amount,
        currency: "SEK",
        idempotency_key: crypto.randomUUID(),
    };
    paymentIntentActive = true;
    submit.disabled = true;
    setLedgerControlsDisabled(true);
    status.textContent = "Submitting…";
    status.dataset.state = "pending";
    transaction.textContent = "—";
    const started = performance.now();
    try {
        const response = await fetch(`/payments?${ledgerQuery(ledger)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request),
        });
        timing.textContent = `${(performance.now() - started).toFixed(1)} ms`;
        if (!response.ok) {
            throw new Error(await readError(response));
        }
        const result = (await response.json());
        status.textContent = result.status;
        status.dataset.state =
            result.status === "SUCCESS"
                ? "success"
                : result.status === "FAILED"
                    ? "error"
                    : "pending";
        keepDisabled = result.status === "PENDING" || result.status === "UNKNOWN";
        transaction.textContent = result.transaction_id ?? "—";
        try {
            await refreshBackendState(ledger);
        }
        catch {
            if (result.status === "SUCCESS") {
                status.textContent =
                    "SUCCESS — Payment succeeded, but balance/history refresh failed. " +
                        "Do not retry the payment.";
                status.dataset.state = "success";
            }
            else if (keepDisabled) {
                status.textContent =
                    `${result.status} — Outcome unresolved; do not submit another payment.`;
                status.dataset.state = "pending";
            }
            else {
                status.textContent = `${result.status} — Balance/history refresh failed.`;
            }
        }
    }
    catch (error) {
        timing.textContent = `${(performance.now() - started).toFixed(1)} ms`;
        status.textContent = error instanceof Error ? error.message : "Request failed";
        status.dataset.state = "error";
    }
    finally {
        submit.disabled = keepDisabled;
        paymentIntentActive = keepDisabled;
        setLedgerControlsDisabled(keepDisabled);
    }
}
async function changeLedger() {
    if (paymentIntentActive) {
        return;
    }
    const ledger = selectedLedger();
    const status = element("payment-status");
    status.textContent = "Loading selected ledger…";
    status.dataset.state = "pending";
    element("transaction-id").textContent = "—";
    element("request-duration").textContent = "—";
    try {
        await refreshBackendState(ledger);
        status.textContent = "Ready";
        status.dataset.state = "ready";
    }
    catch (error) {
        status.textContent = error instanceof Error ? error.message : "Ledger unavailable";
        status.dataset.state = "error";
    }
}
async function start() {
    element("merchant-qr").src = `/merchants/${MERCHANT_ID}/qr`;
    element("payment-form").addEventListener("submit", (event) => {
        void submitPayment(event);
    });
    for (const id of ["ledger-conventional", "ledger-blockchain"]) {
        element(id).addEventListener("change", () => {
            void changeLedger();
        });
    }
    try {
        await refreshBackendState(selectedLedger());
    }
    catch (error) {
        const status = element("payment-status");
        status.textContent = error instanceof Error ? error.message : "Demo state unavailable";
        status.dataset.state = "error";
    }
}
void start();
