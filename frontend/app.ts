import { formatOreAsSek, parseSekToOre } from "./money.js";

const CUSTOMER_ID = "C001";
const MERCHANT_ID = "M001";

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

async function loadBalance(ownerId: string, outputId: string): Promise<void> {
  const response = await fetch(`/accounts/${encodeURIComponent(ownerId)}/balance`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const balance = (await response.json()) as BalanceResponse;
  element(outputId).textContent = formatOreAsSek(balance.balance_ore);
}

async function loadHistory(): Promise<void> {
  const response = await fetch("/transactions");
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

async function refreshBackendState(): Promise<void> {
  await Promise.all([
    loadBalance(CUSTOMER_ID, "customer-balance"),
    loadBalance(MERCHANT_ID, "merchant-balance"),
    loadHistory(),
  ]);
}

async function submitPayment(event: SubmitEvent): Promise<void> {
  event.preventDefault();
  const amountInput = element<HTMLInputElement>("amount");
  const status = element("payment-status");
  const transaction = element("transaction-id");
  const timing = element("request-duration");
  const submit = element<HTMLButtonElement>("pay-button");

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

  submit.disabled = true;
  status.textContent = "Submitting…";
  status.dataset.state = "pending";
  transaction.textContent = "—";
  const started = performance.now();

  try {
    const response = await fetch("/payments", {
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
    status.dataset.state = result.status === "SUCCESS" ? "success" : "error";
    transaction.textContent = result.transaction_id ?? "—";
    try {
      await refreshBackendState();
    } catch {
      status.textContent =
        `${result.status} — Payment succeeded, but balance/history refresh failed. ` +
        "Do not retry the payment.";
      status.dataset.state = "success";
    }
  } catch (error) {
    timing.textContent = `${(performance.now() - started).toFixed(1)} ms`;
    status.textContent = error instanceof Error ? error.message : "Request failed";
    status.dataset.state = "error";
  } finally {
    submit.disabled = false;
  }
}

async function start(): Promise<void> {
  element<HTMLImageElement>("merchant-qr").src = `/merchants/${MERCHANT_ID}/qr`;
  element<HTMLFormElement>("payment-form").addEventListener("submit", (event) => {
    void submitPayment(event as SubmitEvent);
  });
  try {
    await refreshBackendState();
  } catch (error) {
    const status = element("payment-status");
    status.textContent = error instanceof Error ? error.message : "Demo state unavailable";
    status.dataset.state = "error";
  }
}

void start();
