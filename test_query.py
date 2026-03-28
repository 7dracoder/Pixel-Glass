#!/usr/bin/env python3
"""
Test script — queries all 3 agents in one shot using GPS coordinates.
The agent identifies the location, then returns nearby restaurants and HMDA data.

Usage:
    python test_query.py                        # uses default coordinates (Atlantic Ave, Brooklyn)
    python test_query.py 40.7580 -73.9855       # custom lat/lon
    python test_query.py 40.7580 -73.9855 http://localhost:8080   # custom endpoint
"""

import json
import sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_LAT = 40.6782   # Atlantic Ave, Brooklyn
DEFAULT_LON = -73.9442
DEFAULT_ENDPOINT = "http://localhost:8080"

lat  = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LAT
lon  = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LON
base = sys.argv[3]        if len(sys.argv) > 3 else DEFAULT_ENDPOINT

# ── Query ─────────────────────────────────────────────────────────────────────

query = (
    f"My GPS coordinates are latitude {lat}, longitude {lon}. "
    "What street am I on? "
    "Find A-grade restaurants nearby. "
    "Also give me the mortgage denial rates by race for this area."
)

print(f"Endpoint : {base}/run")
print(f"Location : {lat}, {lon}")
print(f"Query    : {query}\n")
print("─" * 60)

# ── Request ───────────────────────────────────────────────────────────────────

try:
    response = requests.post(
        f"{base}/run",
        json={"message": query},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    # ADK responses vary slightly by version — handle both shapes
    answer = (
        data.get("response")
        or data.get("output")
        or data.get("answer")
        or json.dumps(data, indent=2)
    )

    print(answer)

except requests.exceptions.ConnectionError:
    print(f"ERROR: Could not connect to {base}")
    print("Make sure the agent server is running:  adk api_server --port 8080 agents")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out (>60s). The agent may still be processing.")
except requests.exceptions.HTTPError as e:
    print(f"ERROR: {e}")
    print(response.text)
