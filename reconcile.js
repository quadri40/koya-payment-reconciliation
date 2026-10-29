// Payment reconciliation.
//
// Reads payments.jsonl and works out how much money we actually collected.
// Run:  node reconcile.js
//
// Rules (per README):
// - Ignore lines that can't be read, and events without a txn_id.
// - Only the latest attempt for each txn_id counts.
// - A payment counts as collected only if its latest attempt is success.

const fs = require("fs");

const attempts = {}; // txn_id -> array of events

const lines = fs.readFileSync("payments.jsonl", "utf8").split("\n");
for (const line of lines) {
  const trimmed = line.trim();
  if (!trimmed) continue;
  let event;
  try {
    event = JSON.parse(trimmed);
  } catch (e) {
    // Line can't be read: ignore it.
    continue;
  }
  if (!event || typeof event !== "object") continue;
  const txnId = event.txn_id;
  if (!txnId) {
    // Event without a txn_id: ignore it.
    continue;
  }
  if (!attempts[txnId]) attempts[txnId] = [];
  attempts[txnId].push(event);
}

let total = 0;
let count = 0;

for (const txnId of Object.keys(attempts)) {
  const events = attempts[txnId];
  // Only the latest attempt for each txn_id counts.
  const latest = events.reduce(
    (best, e) => ((e.ts || "") > (best.ts || "") ? e : best),
    events[0]
  );
  if (latest.status !== "success") continue;
  // Amounts may be comma-formatted strings (e.g. "3,218.81").
  total += Number(String(latest.amount ?? 0).replace(/,/g, ""));
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
