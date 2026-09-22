import { formatOreAsSek, parseSekToOre } from "./money.js";

const CUSTOMER_ID = "C001";
const MERCHANT_ID = "M001";
type LedgerSelection = "conventional" | "blockchain";
let paymentIntentActive = false;

interface BalanceResponse {
  owner_id: string;
  currency: "SEK";
  balance_ore: number;
}

interface PaymentResponse {
  payment_id: string;
  transaction_id: string | null;
  status: string;
}

interface TransactionResponse {
  transaction_id: string;
  payment_id: string;
  ledger_type: string;
  status: string;
  timestamp: string;
}

interface TransactionHistoryResponse {
  transactions: TransactionResponse[];
}

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!(found instanceof HTMLElement)) {
    throw new Error(`Required UI element is missing: ${id}`);
  }
  return found as T;
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?: { code?: string; message?: string } | string;
    };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (body.detail?.message) {
      return body.detail.code
        ? `${body.detail.code}: ${body.detail.message}`
        : body.detail.message;
    }
  } catch {
    // Fall back to the transport status when the response is not JSON.
  }
  return `Request failed (${response.status})`;
}

function selectedLedger(): LedgerSelection {
  return element<HTMLInputElement>("ledger-blockchain").checked
    ? "blockchain"
    : "conventional";
}

function ledgerQuery(ledger: LedgerSelection): string {
  return `ledger=${encodeURIComponent(ledger)}`;
}

function setLedgerControlsDisabled(disabled: boolean): void {
  for (const id of ["ledger-conventional", "ledger-blockchain"]) {
    element<HTMLInputElement>(id).disabled = disabled;
  }
}

async function loadBalance(
  ownerId: string,
  outputId: string,
  ledger: LedgerSelection,
): Promise<void> {
  const response = await fetch(
    `/accounts/${encodeURIComponent(ownerId)}/balance?${ledgerQuery(ledger)}`,
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const balance = (await response.json()) as BalanceResponse;
  element(outputId).textContent = formatOreAsSek(balance.balance_ore);
}

async function loadHistory(ledger: LedgerSelection): Promise<void> {
  const response = await fetch(`/transactions?${ledgerQuery(ledger)}`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const history = (await response.json()) as TransactionHistoryResponse;
  const body = element<HTMLTableSectionElement>("transaction-history");
  body.replaceChildren();

  for (const transaction of history.transactions) {
    const row = document.createElement("tr");
    for (const value of (
      [
        transaction.transaction_id,
        transaction.payment_id,
        transaction.status,
        transaction.ledger_type,
      ] as const
    )) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    body.append(row);
  }

  element("history-empty").hidden = history.transactions.length !== 0;
}

async function refreshBackendState(ledger: LedgerSelection): Promise<void> {
  await Promise.all([
    loadBalance(CUSTOMER_ID, "customer-balance", ledger),
    loadBalance(MERCHANT_ID, "merchant-balance", ledger),
    loadHistory(ledger),
  ]);
}

async function submitPayment(event: SubmitEvent): Promise<void> {
  event.preventDefault();
  if (paymentIntentActive) {
    return;
  }
  const ledger = selectedLedger();
  const amountInput = element<HTMLInputElement>("amount");
  const status = element("payment-status");
  const transaction = element("transaction-id");
  const timing = element("request-duration");
  const submit = element<HTMLButtonElement>("pay-button");
  let keepDisabled = false;

  let amount: number;
  try {
    amount = parseSekToOre(amountInput.value);
  } catch (error) {
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
    const result = (await response.json()) as PaymentResponse;
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
    } catch {
      if (result.status === "SUCCESS") {
        status.textContent =
          "SUCCESS — Payment succeeded, but balance/history refresh failed. " +
          "Do not retry the payment.";
        status.dataset.state = "success";
      } else if (keepDisabled) {
        status.textContent =
          `${result.status} — Outcome unresolved; do not submit another payment.`;
        status.dataset.state = "pending";
      } else {
        status.textContent = `${result.status} — Balance/history refresh failed.`;
      }
    }
  } catch (error) {
    timing.textContent = `${(performance.now() - started).toFixed(1)} ms`;
    status.textContent = error instanceof Error ? error.message : "Request failed";
    status.dataset.state = "error";
  } finally {
    submit.disabled = keepDisabled;
    paymentIntentActive = keepDisabled;
    setLedgerControlsDisabled(keepDisabled);
  }
}

async function changeLedger(): Promise<void> {
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
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : "Ledger unavailable";
    status.dataset.state = "error";
  }
}

async function start(): Promise<void> {
  element<HTMLImageElement>("merchant-qr").src = `/merchants/${MERCHANT_ID}/qr`;
  element<HTMLFormElement>("payment-form").addEventListener("submit", (event) => {
    void submitPayment(event as SubmitEvent);
  });
  for (const id of ["ledger-conventional", "ledger-blockchain"]) {
    element<HTMLInputElement>(id).addEventListener("change", () => {
      void changeLedger();
    });
  }
  try {
    await refreshBackendState(selectedLedger());
  } catch (error) {
    const status = element("payment-status");
    status.textContent = error instanceof Error ? error.message : "Demo state unavailable";
    status.dataset.state = "error";
  }
}

void start();
