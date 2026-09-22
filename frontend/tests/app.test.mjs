import assert from "node:assert/strict";
import test from "node:test";

const APP_URL = new URL(
  "../../src/upi_payment_experiment/static/app.js",
  import.meta.url,
);
let moduleNonce = 0;

class FakeElement {
  constructor() {
    this.textContent = "";
    this.dataset = {};
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.children = [];
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  replaceChildren(...children) {
    this.children = children;
  }

  append(child) {
    this.children.push(child);
  }
}

function response(body, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => body };
}

function createDom() {
  const elements = new Map(
    [
      "amount",
      "payment-status",
      "transaction-id",
      "request-duration",
      "pay-button",
      "merchant-qr",
      "payment-form",
      "customer-balance",
      "merchant-balance",
      "transaction-history",
      "history-empty",
      "ledger-conventional",
      "ledger-blockchain",
    ].map((id) => [id, new FakeElement()]),
  );
  elements.get("amount").value = "100.00";
  elements.get("ledger-conventional").checked = true;
  elements.get("ledger-blockchain").checked = false;
  return {
    elements,
    document: {
      getElementById: (id) => elements.get(id) ?? null,
      createElement: () => new FakeElement(),
    },
  };
}

async function waitForCompletedSubmission(status) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (status.textContent !== "Submitting…") {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  throw new Error("payment submission did not complete");
}

async function waitForLedgerRefresh(status) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (status.textContent !== "Loading selected ledger…") {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  throw new Error("ledger refresh did not complete");
}

async function runUiCase({
  refreshFails = false,
  paymentFails = false,
  ledger = "conventional",
  paymentStatus = "SUCCESS",
  exerciseLedgerSwitch = false,
  onPaymentStarted = null,
}) {
  const globalKeys = ["HTMLElement", "document", "crypto", "performance", "fetch"];
  const original = new Map(
    globalKeys.map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]),
  );
  const { document, elements } = createDom();
  elements.get("ledger-conventional").checked = ledger === "conventional";
  elements.get("ledger-blockchain").checked = ledger === "blockchain";
  const customerReads = { conventional: 0, blockchain: 0 };
  const merchantReads = { conventional: 0, blockchain: 0 };
  const historyReads = { conventional: 0, blockchain: 0 };
  let paymentPosts = 0;
  let uuid = 0;
  const fetches = [];

  const replacements = {
    HTMLElement: FakeElement,
    document,
    crypto: { randomUUID: () => `uuid-${++uuid}` },
    performance: { now: () => 12.5 },
    fetch: async (url) => {
      fetches.push(url);
      const selected = new URL(url, "http://test").searchParams.get("ledger");
      if (url.startsWith("/payments?ledger=")) {
        paymentPosts += 1;
        if (onPaymentStarted) {
          await onPaymentStarted({ elements, fetches });
        }
        if (paymentFails) {
          return response({ detail: { message: "payment rejected" } }, { ok: false, status: 422 });
        }
        return response({
          payment_id: "PAY-C06-UI",
          transaction_id: `TX-${selected.toUpperCase()}-UI`,
          status: paymentStatus,
        });
      }
      if (url === `/accounts/C001/balance?ledger=${selected}`) {
        customerReads[selected] += 1;
        if (refreshFails && customerReads[selected] === 2) {
          throw new Error("refresh unavailable");
        }
        return response({ balance_ore: customerReads[selected] === 1 ? 100000 : 90000 });
      }
      if (url === `/accounts/M001/balance?ledger=${selected}`) {
        merchantReads[selected] += 1;
        return response({ balance_ore: merchantReads[selected] === 1 ? 0 : 10000 });
      }
      if (url === `/transactions?ledger=${selected}`) {
        historyReads[selected] += 1;
        return response({ transactions: historyReads[selected] === 1 ? [] : [{
          transaction_id: `TX-${selected.toUpperCase()}-UI`,
          payment_id: "PAY-C06-UI",
          status: "SUCCESS",
          ledger_type: selected === "blockchain" ? "BlockchainLedger" : "ConventionalLedger",
        }] });
      }
      throw new Error(`unexpected fetch: ${url}`);
    },
  };
  for (const [key, value] of Object.entries(replacements)) {
    Object.defineProperty(globalThis, key, {
      configurable: true,
      writable: true,
      value,
    });
  }

  try {
    await import(`${APP_URL.href}?case=${++moduleNonce}`);
    await new Promise((resolve) => setTimeout(resolve, 0));
    elements.get("payment-form").listeners.get("submit")({ preventDefault() {} });
    await waitForCompletedSubmission(elements.get("payment-status"));
    let switchEvidence = null;
    if (exerciseLedgerSwitch) {
      elements.get("ledger-conventional").checked = false;
      elements.get("ledger-blockchain").checked = true;
      elements.get("ledger-blockchain").listeners.get("change")();
      const toBlockchain = {
        status: elements.get("payment-status").textContent,
        state: elements.get("payment-status").dataset.state,
        transaction: elements.get("transaction-id").textContent,
        timing: elements.get("request-duration").textContent,
      };
      await waitForLedgerRefresh(elements.get("payment-status"));
      elements.get("payment-form").listeners.get("submit")({ preventDefault() {} });
      await waitForCompletedSubmission(elements.get("payment-status"));
      const blockchainTransaction = elements.get("transaction-id").textContent;

      elements.get("ledger-conventional").checked = true;
      elements.get("ledger-blockchain").checked = false;
      elements.get("ledger-conventional").listeners.get("change")();
      const toConventional = {
        status: elements.get("payment-status").textContent,
        state: elements.get("payment-status").dataset.state,
        transaction: elements.get("transaction-id").textContent,
        timing: elements.get("request-duration").textContent,
      };
      await waitForLedgerRefresh(elements.get("payment-status"));
      switchEvidence = { toBlockchain, blockchainTransaction, toConventional };
    }
    return { elements, paymentPosts, switchEvidence, uuid, fetches };
  } finally {
    for (const [key, descriptor] of original) {
      if (descriptor) {
        Object.defineProperty(globalThis, key, descriptor);
      } else {
        delete globalThis[key];
      }
    }
  }
}

test("successful payment refreshes backend state without a second submission", async () => {
  const result = await runUiCase({});
  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "SUCCESS");
  assert.equal(result.elements.get("payment-status").dataset.state, "success");
  assert.equal(result.elements.get("transaction-id").textContent, "TX-CONVENTIONAL-UI");
  assert.equal(result.elements.get("customer-balance").textContent, "900.00 SEK");
  assert.equal(result.elements.get("merchant-balance").textContent, "100.00 SEK");
  assert.equal(result.elements.get("transaction-history").children.length, 1);
});

test("refresh failure preserves confirmed payment success without resubmission", async () => {
  const result = await runUiCase({ refreshFails: true });
  assert.equal(result.paymentPosts, 1);
  assert.match(result.elements.get("payment-status").textContent, /^SUCCESS — Payment succeeded, but balance\/history refresh failed\./);
  assert.equal(result.elements.get("payment-status").dataset.state, "success");
  assert.equal(result.elements.get("transaction-id").textContent, "TX-CONVENTIONAL-UI");
});

test("payment failure remains a payment failure", async () => {
  const result = await runUiCase({ paymentFails: true });
  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "payment rejected");
  assert.equal(result.elements.get("payment-status").dataset.state, "error");
  assert.equal(result.elements.get("transaction-id").textContent, "—");
});

test("blockchain selection is sent only as transport metadata", async () => {
  const result = await runUiCase({ ledger: "blockchain" });
  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "SUCCESS");
});

test("unresolved blockchain outcome prevents a new payment intent", async () => {
  const result = await runUiCase({
    ledger: "blockchain",
    paymentStatus: "UNKNOWN",
  });
  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "UNKNOWN");
  assert.equal(result.elements.get("payment-status").dataset.state, "pending");
  assert.equal(result.elements.get("pay-button").disabled, true);
});

test("ledger switches clear stale result context in both directions", async () => {
  const result = await runUiCase({ exerciseLedgerSwitch: true });

  assert.equal(result.paymentPosts, 2);
  assert.deepEqual(result.switchEvidence.toBlockchain, {
    status: "Loading selected ledger…",
    state: "pending",
    transaction: "—",
    timing: "—",
  });
  assert.equal(result.switchEvidence.blockchainTransaction, "TX-BLOCKCHAIN-UI");
  assert.deepEqual(result.switchEvidence.toConventional, {
    status: "Loading selected ledger…",
    state: "pending",
    transaction: "—",
    timing: "—",
  });
  assert.equal(result.elements.get("payment-status").textContent, "Ready");
  assert.equal(result.elements.get("transaction-id").textContent, "—");
  assert.equal(result.elements.get("request-duration").textContent, "—");
});

test("an in-flight payment keeps result and refresh on its captured ledger", async () => {
  const result = await runUiCase({
    onPaymentStarted: async ({ elements, fetches }) => {
      assert.equal(elements.get("ledger-conventional").disabled, true);
      assert.equal(elements.get("ledger-blockchain").disabled, true);
      assert.equal(elements.get("payment-status").textContent, "Submitting…");

      elements.get("ledger-conventional").checked = false;
      elements.get("ledger-blockchain").checked = true;
      elements.get("ledger-blockchain").listeners.get("change")();
      await new Promise((resolve) => setTimeout(resolve, 0));

      assert.equal(elements.get("payment-status").textContent, "Submitting…");
      assert.ok(fetches.every((url) => url.endsWith("ledger=conventional")));
    },
  });

  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "SUCCESS");
  assert.equal(result.elements.get("transaction-id").textContent, "TX-CONVENTIONAL-UI");
  assert.equal(result.elements.get("customer-balance").textContent, "900.00 SEK");
  assert.equal(result.elements.get("merchant-balance").textContent, "100.00 SEK");
  assert.equal(
    result.elements.get("transaction-history").children[0].children[3].textContent,
    "ConventionalLedger",
  );
  assert.ok(result.fetches.every((url) => url.endsWith("ledger=conventional")));
  assert.equal(result.elements.get("ledger-conventional").disabled, false);
  assert.equal(result.elements.get("ledger-blockchain").disabled, false);
});
