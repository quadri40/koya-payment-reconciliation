#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json


def parse_amount(val):
    """Sanitize and parse transaction amount into a float."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        return float(val.replace(",", "").strip())
    return 0.0


# Map txn_id -> latest event dictionary
latest_attempts = {}

with open("payments.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue

        ts = event.get("ts", "")
        # Keep only the latest attempt for each txn_id
        if txn_id not in latest_attempts or ts > latest_attempts[txn_id].get("ts", ""):
            latest_attempts[txn_id] = event

# Count and sum only transactions whose latest attempt was successful
total = 0.0
count = 0

for event in latest_attempts.values():
    if event.get("status") == "success":
        count += 1
        total += parse_amount(event.get("amount", 0))

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
