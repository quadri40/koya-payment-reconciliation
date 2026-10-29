// Payment reconciliation.
//
// Reads payments.jsonl and works out how much money we actually collected.
// Run:  node reconcile.js

const fs = require("fs");

let total = 0;
let count = 0;

const lines = fs
	.readFileSync("payments.jsonl", "utf8")
	.split("\n")
	.filter((l) => l.length > 0);

let latest_event = new Map();

for (const line of lines) {
	if (!line.trim()) {
		continue;
	}

	let event;

	try {
		event = JSON.parse(line);
	} catch {
		continue;
	}

	let txn_id = event.txn_id;

	if (!txn_id) {
		continue;
	}

	let existing = latest_event.get(txn_id);

	if (
		!existing ||
		new Date(event.ts).getTime() >= new Date(existing.ts).getTime()
	) {
		latest_event.set(txn_id, event);
	}
}
for (let e of latest_event.values()) {
	if (e.status === "success") {
		total += Number(e.amount);
		count += 1;
	}
}

const expected = parseInt(fs.readFileSync("expected.txt", "utf8").trim(), 10);
// console.log(total);

if (count !== expected) {
	console.log(
		`Check failed: counted ${count} successful payments, expected ${expected}.`,
	);
	console.log(
		"Something in the data isn't being handled the way the README describes.",
	);
} else {
	console.log(`Check passed: ${count} successful payments.`);
	console.log(`Your code: KOYA-${Math.round(total)}`);
}
