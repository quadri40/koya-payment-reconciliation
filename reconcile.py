#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from decimal import Decimal, InvalidOperation


def parse_amount(value):
    """Amounts are in naira. Some come as strings with thousands separators."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value))


events = {}

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # truncated/garbled line from a production export
        if not isinstance(event, dict):
            continue
        if not event.get("txn_id"):
            continue  # events without a txn_id can't be tied to a payment
        try:
            parse_amount(event["amount"])
        except (InvalidOperation, KeyError):
            continue

        # Keep only the latest attempt for each txn_id.
        current = events.get(event["txn_id"])
        if current is None or event["ts"] > current["ts"]:
            events[event["txn_id"]] = event

total = Decimal(0)
count = 0
for event in events.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
