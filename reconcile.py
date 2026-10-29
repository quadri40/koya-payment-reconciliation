#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from decimal import Decimal, InvalidOperation


def parse_amount(value):
    """Amounts may be JSON numbers or strings such as "1,234.56"."""
    if isinstance(value, bool):
        raise ValueError("invalid amount")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value.replace(",", "").strip())
    raise ValueError("invalid amount")


latest = {}

with open("payments.jsonl", encoding="utf-8", errors="replace") as f:
    for line_no, line in enumerate(f):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue

        # Keep only the latest attempt for each txn_id. Timestamps are ISO-8601
        # UTC strings, so they sort chronologically. The line number breaks ties.
        key = (str(event.get("ts") or ""), line_no)
        if txn_id not in latest or key > latest[txn_id][0]:
            latest[txn_id] = (key, event)

total = Decimal("0")
count = 0

for _, event in latest.values():
    if event.get("status") != "success":
        continue
    try:
        total += parse_amount(event["amount"])
    except (KeyError, ValueError, InvalidOperation):
        continue
    count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
