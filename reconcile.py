#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from decimal import Decimal

latest_events = {}
total = 0.0
count = 0

with open("payments.jsonl") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue

        previous = latest_events.get(txn_id)
        if previous is None or event["ts"] > previous["ts"]:
            latest_events[txn_id] = event

total = Decimal("0")
count = 0
for event in latest_events.values():
    if event["status"] == "success":
        total += Decimal(str(event["amount"]).replace(",", ""))
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
