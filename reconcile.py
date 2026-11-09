#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


def parse_amount(value):
    """Parse an amount that may be a number or a string like '1,234.56'."""
    if isinstance(value, bool):
        raise ValueError("invalid amount")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("\u20a6", "")
        return Decimal(cleaned)
    raise ValueError("invalid amount")


def main():
    # Latest attempt per txn_id, by timestamp.
    latest = {}
    with open("payments.jsonl", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue  # unreadable line
            if not isinstance(event, dict):
                continue
            txn_id = event.get("txn_id")
            if not txn_id:
                continue  # event without a transaction id
            ts = event.get("ts") or ""
            current = latest.get(txn_id)
            if current is None or ts >= (current.get("ts") or ""):
                latest[txn_id] = event

    total = Decimal("0")
    count = 0
    for event in latest.values():
        if event.get("status") != "success":
            continue
        try:
            total += parse_amount(event.get("amount"))
        except (InvalidOperation, ValueError):
            continue
        count += 1

    with open("expected.txt", encoding="utf-8") as f:
        expected = int(f.read().strip())

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        code = total.quantize(CENT, rounding=ROUND_HALF_UP).to_integral_value(ROUND_HALF_UP)
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{code}")


if __name__ == "__main__":
    main()
