#!/usr/bin/env python3
"""Reverse-geocode coordinates with the Positionstack API.

Usage:
    python3 positionstack.py [LAT] [LON] [API_KEY]
    POSITIONSTACK_API_KEY=... python3 positionstack.py [LAT] [LON]

Defaults to 6.4410, 3.5357. Prints the full address, i.e. the `label` of the
first element of the response's `data` array. No third-party packages needed.
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
    key = sys.argv[3] if len(sys.argv) > 3 else API_KEY
    if not key:
        sys.exit(
            "No API key. Pass it as the third argument or set POSITIONSTACK_API_KEY.\n"
            "Get a free key at https://positionstack.com/signup"
        )
    try:
        address = get_full_address(lat, lon, key)
    except (RuntimeError, urllib.error.URLError) as exc:
        sys.exit(f"Could not geocode {lat},{lon}: {exc}")

    if address is None:
        sys.exit(f"No address returned for {lat},{lon}.")
    print(address)
