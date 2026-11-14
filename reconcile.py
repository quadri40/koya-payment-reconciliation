#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime, timezone

DATA_FILE = "payments.jsonl"
EXPECTED_FILE = "expected.txt"


def parse_amount(value):
    """Amounts arrive as numbers or as formatted strings like '4,804.15'."""
    if isinstance(value, bool):
        raise ValueError("boolean amount")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace(",", "").replace(" ", ""))
    raise ValueError(f"unusable amount: {value!r}")


def parse_ts(value):
    """Parse an ISO-8601 UTC timestamp; positive means later."""
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    ts = datetime.fromisoformat(text)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def load_latest_attempts(path):
    """Return {txn_id: event} with only the latest attempt per transaction."""
    latest = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                # Truncated or otherwise unreadable export line.
                continue
            if not isinstance(event, dict):
                continue

            txn_id = event.get("txn_id")
            if not txn_id:
                # Events without a transaction id cannot be attributed.
                continue

            try:
                ts = parse_ts(event.get("ts"))
            except (TypeError, ValueError):
                continue

            current = latest.get(txn_id)
            if current is None or ts > current[0]:
                latest[txn_id] = (ts, event)
    return {txn_id: event for txn_id, (_, event) in latest.items()}


def main():
    latest = load_latest_attempts(DATA_FILE)

    total = 0.0
    count = 0
    for event in latest.values():
        if event.get("status") != "success":
            continue
        try:
            amount = parse_amount(event.get("amount"))
        except (TypeError, ValueError):
            continue
        total += amount
        count += 1

    with open(EXPECTED_FILE, encoding="utf-8") as f:
        expected = int(f.read().strip())

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    main()
