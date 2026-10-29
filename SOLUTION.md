# Payment reconciliation — solution notes

## Form answers (copy/paste)

### Question 1 — "Write a function to call the API, and extract the first address in the array. Paste the full address below."

Submit the function from [The function](#the-function-positionstackpy) plus the address. Function:

```python
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.positionstack.com/v1/reverse"
API_KEY = os.environ.get("POSITIONSTACK_API_KEY", "")


def get_full_address(latitude, longitude, api_key=API_KEY):
    """Call Positionstack's reverse endpoint and return the first address."""
    params = urllib.parse.urlencode(
        {"access_key": api_key, "query": f"{latitude},{longitude}", "limit": 1}
    )
    try:
        with urllib.request.urlopen(f"{API_URL}?{params}", timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8", "replace") or "{}")

    if "error" in payload:
        raise RuntimeError(
            f"Positionstack error {payload['error'].get('code')}: "
            f"{payload['error'].get('message')}"
        )

    results = payload.get("data") or []   # the address array
    if not results:
        return None

    return results[0].get("label") or results[0].get("name")   # first address


print(get_full_address(6.4410, 3.5357))
```

Full address: **not obtainable with the supplied key** — Positionstack returns 401
`invalid_access_key` for the supplied key (see
[Result: blocked by the API key](#result-blocked-by-the-api-key)). The best available
reference for 6.4410, 3.5357, from an independent geocoder, is:
**Lekki Conservation Center, Chevron, Lekki Peninsula II, Eti Osa, Lagos, Nigeria**
(plus code `6FR5CGRP+C7`). Replace this line with Positionstack's `data[0].label` once
the key works: `POSITIONSTACK_API_KEY=<valid key> python3 positionstack.py 6.4410 3.5357`.

### Question 2 — "Paste the code the script prints"

```
KOYA-1964687346
```

---

## The code the script prints

```
Check passed: 22733 successful payments.
Your code: KOYA-1964687346
```

Total collected (latest successful attempt per `txn_id`): **₦1,964,687,345.74**

---

## Why the original script failed

`payments.jsonl` has 39,723 lines, of which 39,697 parse as JSON objects. There are
**3,000 distinct `txn_id`s** spread across up to 4 attempts each. `reconcile.py` counted
every `success` row and crashed on the first damaged line, so both the count and the
total were wrong.

| Problem in the data | Count | Fix applied |
| --- | --- | --- |
| Truncated / garbled lines (e.g. line 14,764: `{"txn_id": "`) | 25 | `try/except json.JSONDecodeError` → skip the line |
| Events with no `txn_id` | 15 | skip, they can't belong to a payment |
| `amount` stored as a string with thousands separators (`"269,766.08"`) | 2,326 | strip commas, parse with `Decimal` |
| Same `txn_id` attempted several times | 7,772 ids | keep only the attempt with the latest `ts` |
| `amount` as `int` instead of `float` | 15 | `Decimal(str(value))` handles both |

Status after deduplication (latest attempt only): **22,733 success**, 5,201 failed,
2,066 pending — the success count matches `expected.txt`.

Note: no two attempts of the same `txn_id` share a timestamp, so "latest" is unambiguous.

---

## The fix (`reconcile.py`)

```python
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
```

`reconcile.js` was left untouched — only one working implementation is needed.

---

## Positionstack lookup

### Result: blocked by the API key

The supplied key is rejected by Positionstack on
every endpoint and protocol tried (`/v1/reverse` and `/v1/forward`, HTTP and HTTPS):

```json
{"error":{"code":"invalid_access_key","message":"You have not supplied a valid API Access Key. [Technical Support: support@apilayer.com]"}}
```

That is a 401 from Positionstack itself, so the `data[0]` address could **not** be
retrieved with this key.

The second key supplied (redacted here) is an **Aviationstack** key:
it returns live flight data from `api.apilayer.net/aviationstack/v1/flights` but is also
rejected by Positionstack with the same `invalid_access_key`. Aviationstack and
Positionstack are separate apilayer products, each with its own subscription and key, so
a Positionstack key has to be issued for the Positionstack product.

### Cross-check from another geocoder (not Positionstack)

As a sanity check, a free reverse geocoder (Photon / BigDataCloud) places
**6.4410, 3.5357** at:

> **Lekki Conservation Center, Chevron, Lekki Peninsula II, Eti Osa, Lagos, Nigeria**
> (plus code `6FR5CGRP+C7`)

Nearest OSM features from that geocoder, by distance from 6.4410, 3.5357: the Lekki
Conservation Center access road at 149 m, the conservation centre itself at 207 m, then
the residential street *Wood Dove Drive* at 314 m (house numbers 2–13 within 314–376 m).
There is no house number or postcode at the coordinate itself; it falls inside the
conservation centre grounds.

Use this only as a reference; the address for the form must come from Positionstack's
first result once a valid key is available.

### The function (`positionstack.py`)

```python
#!/usr/bin/env python3
"""Reverse-geocode coordinates with the Positionstack API.

Usage:  python3 positionstack.py [LAT] [LON]
Prints the full address (the `label` of the first result in the data array).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.positionstack.com/v1/reverse"
API_KEY = os.environ.get("POSITIONSTACK_API_KEY", "")


def get_full_address(latitude, longitude, api_key=API_KEY):
    """Return the full address string for the coordinates, or None."""
    params = urllib.parse.urlencode(
        {"access_key": api_key, "query": f"{latitude},{longitude}", "limit": 1}
    )
    try:
        with urllib.request.urlopen(f"{API_URL}?{params}", timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # The API returns its error message in the body of 4xx responses.
        payload = json.loads(exc.read().decode("utf-8", "replace") or "{}")

    if "error" in payload:
        raise RuntimeError(
            f"Positionstack error {payload['error'].get('code')}: "
            f"{payload['error'].get('message')}"
        )

    results = payload.get("data") or []
    if not results:
        return None

    first = results[0]
    return first.get("label") or first.get("name")


if __name__ == "__main__":
    lat = float(sys.argv[1]) if len(sys.argv) > 1 else 6.4410
    lon = float(sys.argv[2]) if len(sys.argv) > 2 else 3.5357
    try:
        print(get_full_address(lat, lon))
    except (RuntimeError, urllib.error.URLError) as exc:
        sys.exit(f"Could not geocode {lat},{lon}: {exc}")
```

Run it with a working key:

```bash
POSITIONSTACK_API_KEY=<valid key> python3 positionstack.py 6.4410 3.5357
```

---

## How this was verified

- `python3 reconcile.py` → `Check passed: 22733 successful payments.` and
  `Your code: KOYA-1964687346`.
- `python3 positionstack.py` → exits with the Positionstack `invalid_access_key`
  message, confirming the request/parsing path works and only the key is at fault.

## Still to do

1. `git commit` the fix to your fork and push it.
2. Put a valid Positionstack key in the environment and rerun `positionstack.py` to get
   the real first-result address.
3. Submit `KOYA-1964687346` and your fork's URL in the form.
