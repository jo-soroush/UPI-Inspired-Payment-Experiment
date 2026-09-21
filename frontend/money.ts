const SEK_PATTERN = /^(0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$/;

export function parseSekToOre(value: string): number {
  if (!SEK_PATTERN.test(value)) {
    throw new Error("Use SEK with '.' and at most two decimals, for example 100.00");
  }

  const [whole, suppliedFraction = ""] = value.split(".");
  const fraction = suppliedFraction.padEnd(2, "0");
  const oreText = `${whole}${fraction}`;
  const ore = BigInt(oreText);
  if (ore > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new Error("Amount is too large for safe browser transport");
  }
  return Number(ore);
}

export function formatOreAsSek(ore: number): string {
  if (!Number.isSafeInteger(ore) || ore < 0) {
    throw new Error("Backend balance must be a non-negative safe integer");
  }
  const whole = Math.floor(ore / 100);
  const fraction = String(ore % 100).padStart(2, "0");
  return `${whole}.${fraction} SEK`;
}
