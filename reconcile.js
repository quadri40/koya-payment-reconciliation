const fs = require("fs");

function parseAmount(value) {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error("invalid amount");
    return value;
  }
  if (typeof value === "string") {
    const cleaned = value.trim().replace(/,/g, "").replace(/\u20a6/g, "");
    const amount = Number(cleaned);
    if (!Number.isFinite(amount)) throw new Error("invalid amount");
    return amount;
  }
  throw new Error("invalid amount");
}


/ Latest attempt per txn_id, by timestamp.
const latest = new Map();
const lines = fs.readFileSync("payments.jsonl", "utf8").split("\n");


for (const line of lines) {
  let event;
  try {
    event = JSON.parse(line);
  } catch {
    continue; // unreadable line
  }
  if (event === null || typeof event !== "object" || Array.isArray(event)) continue;
  const txnId = event.txn_id;
  if (!txnId) continue; // event without a transaction id
  const ts = event.ts || "";
  const current = latest.get(txnId);
  if (!current || ts >= (current.ts || "")) latest.set(txnId, event);
}

// Accumulate in cents so floating point drift can't change the total.
let totalCents = 0;
let count = 0;
for (const event of latest.values()) {
  if (event.status !== "success") continue;
  let amount;
  try {
    amount = parseAmount(event.amount);
  } catch {
    continue;
  }
  totalCents += Math.round(amount * 100);
  count += 1;
}


const expected = parseInt(fs.readFileSync("expected.txt", "utf8").trim(), 10);
  console.log(`Check failed: counted ${count} successful payments, expected ${expected}.`);
  console.log("Something in the data isn't being handled the way the README describes.");
} else {
  const total = totalCents / 100;
  console.log(`Check passed: ${count} successful payments.`);
  console.log(`Your code: KOYA-${Math.round(total)}`);
}
