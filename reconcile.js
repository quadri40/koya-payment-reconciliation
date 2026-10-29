// Payment reconciliation.
//
// Reads payments.jsonl and works out how much money we actually collected.
// Run:  node reconcile.js

const fs = require("fs");

function parseAmount(value) {
  // Amounts may be JSON numbers or strings such as "1,234.56".
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error("invalid amount");
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value.replace(/,/g, "").trim());
    if (!Number.isFinite(parsed)) throw new Error("invalid amount");
    return parsed;
  }
  throw new Error("invalid amount");
}

const latest = new Map();

const lines = fs.readFileSync("payments.jsonl", "utf8").split(/\r?\n/);
lines.forEach((line, lineNo) => {
  line = line.trim();
  if (!line) return;

  let event;
  try {
    event = JSON.parse(line);
  } catch {
    return; // Ignore unreadable lines.
  }

  if (event === null || typeof event !== "object" || Array.isArray(event)) return;

  const txnId = event.txn_id;
  if (!txnId) return; // Ignore events without a txn_id.

  // Keep only the latest attempt for each txn_id. Timestamps are ISO-8601 UTC
  // strings, so they sort chronologically. The line number breaks ties.
  const key = [String(event.ts ?? ""), lineNo];
  const previous = latest.get(txnId);
  if (
    !previous ||
    key[0] > previous.key[0] ||
    (key[0] === previous.key[0] && key[1] > previous.key[1])
  ) {
    latest.set(txnId, { key, event });
  }
});

let total = 0;
let count = 0;

for (const { event } of latest.values()) {
  if (event.status !== "success") continue;
  try {
    total += parseAmount(event.amount);
  } catch {
    continue;
  }
  count += 1;
}

const expected = parseInt(fs.readFileSync("expected.txt", "utf8").trim(), 10);

if (count !== expected) {
  console.log(`Check failed: counted ${count} successful payments, expected ${expected}.`);
  console.log("Something in the data isn't being handled the way the README describes.");
} else {
  console.log(`Check passed: ${count} successful payments.`);
  console.log(`Your code: KOYA-${Math.round(total)}`);
}
