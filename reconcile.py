#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (per README):
- Ignore lines that can't be read, and events without a txn_id.
- Only the latest attempt for each txn_id counts.
- A payment counts as collected only if its latest attempt is success.
"""
import json
from collections import defaultdict

attempts = defaultdict(list)  # txn_id -> list of events

with open("payments.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            # Line can't be read: ignore it.
            continue
        if not isinstance(event, dict):
            continue
        txn_id = event.get("txn_id")
        if not txn_id:
            # Event without a txn_id: ignore it.
            continue
        attempts[txn_id].append(event)

total = 0.0
count = 0

for txn_id, events in attempts.items():
    # Only the latest attempt for each txn_id counts.
    latest = max(events, key=lambda e: e.get("ts", "") or "")
    if latest.get("status") != "success":
        continue
    # Amounts may be comma-formatted strings (e.g. "3,218.81").
    amount = latest.get("amount", 0)
    total += float(str(amount).replace(",", ""))
    count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
