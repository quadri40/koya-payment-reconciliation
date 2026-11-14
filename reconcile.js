// Payment reconciliation.
//
// Reads payments.jsonl and works out how much money we actually collected.
// Run:  node reconcile.js

const fs = require("fs");

const latestByTransaction = new Map();

for (const line of fs.readFileSync("payments.jsonl", "utf8").split(/\r?\n/)) {
  if (line.trim() === "") continue;

  let event;
  try {
    event = JSON.parse(line);
  } catch (error) {
    if (error instanceof SyntaxError) continue;
    throw error;
  }

  if (!event || typeof event !== "object" || Array.isArray(event) || !event.txn_id) {
    continue;
  }

  const timestamp = Date.parse(event.ts);
  if (!Number.isFinite(timestamp)) {
    throw new Error(`Invalid timestamp for transaction ${event.txn_id}.`);
  }

  const previous = latestByTransaction.get(event.txn_id);
  if (!previous || timestamp >= previous.timestamp) {
    latestByTransaction.set(event.txn_id, { timestamp, event });
  }
}

function amountInKobo(amount) {
  const value = typeof amount === "string" ? amount.trim() : String(amount);
  const match = /^([+-]?)(\d+|\d{1,3}(?:,\d{3})+)(?:\.(\d{1,2}))?$/.exec(value);
  if (!match) {
    throw new Error(`Invalid payment amount: ${value}`);
  }

  const naira = BigInt(match[2].replace(/,/g, ""));
  const kobo = BigInt((match[3] || "").padEnd(2, "0"));
  return (match[1] === "-" ? -1n : 1n) * (naira * 100n + kobo);
}

let totalKobo = 0n;
let count = 0;

for (const { event } of latestByTransaction.values()) {
  if (event.status === "success") {
    totalKobo += amountInKobo(event.amount);
    count += 1;
  }
}

const expected = parseInt(fs.readFileSync("expected.txt", "utf8").trim(), 10);

if (count !== expected) {
  console.log(`Check failed: counted ${count} successful payments, expected ${expected}.`);
  console.log("Something in the data isn't being handled the way the README describes.");
} else {
  const roundedTotal =
    totalKobo >= 0n
      ? (totalKobo + 50n) / 100n
      : -((-totalKobo + 49n) / 100n);
  console.log(`Check passed: ${count} successful payments.`);
  console.log(`Your code: KOYA-${roundedTotal}`);
}
