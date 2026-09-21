import assert from "node:assert/strict";
import test from "node:test";

import {
  formatOreAsSek,
  parseSekToOre,
} from "../../src/upi_payment_experiment/static/money.js";

test("SEK decimal strings convert deterministically to integer ore", () => {
  assert.equal(parseSekToOre("100"), 10000);
  assert.equal(parseSekToOre("100.0"), 10000);
  assert.equal(parseSekToOre("100.00"), 10000);
  assert.equal(parseSekToOre("1.2"), 120);
  assert.equal(parseSekToOre("1.23"), 123);
  assert.equal(parseSekToOre("0"), 0);
});

test("malformed or locale-ambiguous presentation values are rejected", () => {
  for (const value of [
    "00",
    "01",
    "1.",
    ".5",
    "1.234",
    "-1",
    "+1",
    "1,50",
    " 1",
    "1 ",
    "1e2",
  ]) {
    assert.throws(() => parseSekToOre(value), { name: "Error" }, value);
  }
});

test("amounts outside safe JSON integer transport are rejected", () => {
  assert.equal(parseSekToOre("90071992547409.91"), Number.MAX_SAFE_INTEGER);
  assert.throws(() => parseSekToOre("90071992547409.92"), /too large/);
});

test("backend integer balances format as SEK without floating point", () => {
  assert.equal(formatOreAsSek(100000), "1000.00 SEK");
  assert.equal(formatOreAsSek(90000), "900.00 SEK");
  assert.equal(formatOreAsSek(10000), "100.00 SEK");
});
