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
    ].map((id) => [id, new FakeElement()]),
  );
  elements.get("amount").value = "100.00";
  return {
    elements,
    document: {
      getElementById: (id) => elements.get(id) ?? null,
      createElement: () => new FakeElement(),
    },
  };
}

async function waitForCompletedSubmission(button) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (!button.disabled) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  throw new Error("payment submission did not complete");
}

async function runUiCase({ refreshFails = false, paymentFails = false }) {
  const globalKeys = ["HTMLElement", "document", "crypto", "performance", "fetch"];
  const original = new Map(
    globalKeys.map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]),
  );
  const { document, elements } = createDom();
  let customerReads = 0;
  let merchantReads = 0;
  let historyReads = 0;
  let paymentPosts = 0;
  let uuid = 0;

  const replacements = {
    HTMLElement: FakeElement,
    document,
    crypto: { randomUUID: () => `uuid-${++uuid}` },
    performance: { now: () => 12.5 },
    fetch: async (url) => {
      if (url === "/payments") {
        paymentPosts += 1;
        if (paymentFails) {
          return response({ detail: { message: "payment rejected" } }, { ok: false, status: 422 });
        }
        return response({
          payment_id: "PAY-C06-UI",
          transaction_id: "TX-C06-UI",
          status: "SUCCESS",
        });
      }
      if (url === "/accounts/C001/balance") {
        customerReads += 1;
        if (refreshFails && customerReads === 2) {
          throw new Error("refresh unavailable");
        }
        return response({ balance_ore: customerReads === 1 ? 100000 : 90000 });
      }
      if (url === "/accounts/M001/balance") {
        merchantReads += 1;
        return response({ balance_ore: merchantReads === 1 ? 0 : 10000 });
      }
      if (url === "/transactions") {
        historyReads += 1;
        return response({ transactions: historyReads === 1 ? [] : [{
          transaction_id: "TX-C06-UI",
          payment_id: "PAY-C06-UI",
          status: "SUCCESS",
          ledger_type: "ConventionalLedger",
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
    await waitForCompletedSubmission(elements.get("pay-button"));
    return { elements, paymentPosts, uuid };
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
  assert.equal(result.elements.get("transaction-id").textContent, "TX-C06-UI");
  assert.equal(result.elements.get("customer-balance").textContent, "900.00 SEK");
  assert.equal(result.elements.get("merchant-balance").textContent, "100.00 SEK");
  assert.equal(result.elements.get("transaction-history").children.length, 1);
});

test("refresh failure preserves confirmed payment success without resubmission", async () => {
  const result = await runUiCase({ refreshFails: true });
  assert.equal(result.paymentPosts, 1);
  assert.match(result.elements.get("payment-status").textContent, /^SUCCESS — Payment succeeded, but balance\/history refresh failed\./);
  assert.equal(result.elements.get("payment-status").dataset.state, "success");
  assert.equal(result.elements.get("transaction-id").textContent, "TX-C06-UI");
});

test("payment failure remains a payment failure", async () => {
  const result = await runUiCase({ paymentFails: true });
  assert.equal(result.paymentPosts, 1);
  assert.equal(result.elements.get("payment-status").textContent, "payment rejected");
  assert.equal(result.elements.get("payment-status").dataset.state, "error");
  assert.equal(result.elements.get("transaction-id").textContent, "—");
});
