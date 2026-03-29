"""
Full pipeline test simulating what the iOS app does for a location query.
Tests: GPS enrichment → correct API format → response parsing → readable output
"""
import json
import urllib.request
import urllib.error
import ssl
import certifi

ADK_BASE_URL = "https://agents-c5nlrwz5vq-ue.a.run.app"

# Simulated GPS (from LocationManager fallback)
LAT = 40.7126
LON = -74.0066

# Simulated tool call args from Gemini (nyc_lookup)
QUERY = "What restaurants are near me?"
CATEGORY = "restaurant"

# --- Step 1: GPS enrichment (mirrors ADKAgentBridge.isLocationRelevant + enrichment) ---
LOCATION_KEYWORDS = ["near me", "nearby", "around here", "where am i",
                     "this street", "this area", "close to me", "my location"]

def is_location_relevant(query, category):
    if category == "location":
        return True
    lower = query.lower()
    return any(kw in lower for kw in LOCATION_KEYWORDS)

enriched_query = QUERY
if is_location_relevant(QUERY, CATEGORY):
    enriched_query = f"User's current GPS location: latitude={LAT}, longitude={LON}. {QUERY}"

print(f"=== Step 1: GPS Enrichment ===")
print(f"Original:  {QUERY}")
print(f"Enriched:  {enriched_query}")
print()

# --- Step 2: Map category to mode (mirrors ADKAgentBridge.sendQuery) ---
mode_map = {"restaurant": "restaurant", "location": "location"}
mode = mode_map.get(CATEGORY, "restaurant")

payload = {"message": enriched_query, "mode": mode}
url = f"{ADK_BASE_URL}/"

print(f"=== Step 2: HTTP POST to {url} ===")
print(f"Payload: {json.dumps(payload)}")
print()

# --- Step 3: Send request ---
ctx = ssl.create_default_context(cafile=certifi.where())
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
        data = json.loads(body)

        print(f"=== Step 3: Response (HTTP {status}) ===")

        # --- Step 4: Parse response (mirrors ADKAgentBridge.extractTextFromResponse) ---
        lines = []
        if "restaurants" in data and data["restaurants"]:
            count = data.get("count", len(data["restaurants"]))
            lines.append(f"Found {count} restaurant(s):")
            for r in data["restaurants"][:5]:
                name    = r.get("name", "Unknown")
                address = r.get("address", "")
                borough = r.get("borough", "")
                cuisine = r.get("cuisine", "")
                grade   = r.get("grade", "N/A")
                lines.append(f"  • {name} — {cuisine}, {address} {borough}, Grade: {grade}")
        elif "streets" in data and data["streets"]:
            count = data.get("count", len(data["streets"]))
            lines.append(f"Found {count} street(s):")
            for s in data["streets"][:5]:
                name    = s.get("full_name") or s.get("street", "Unknown")
                borough = s.get("boro_name") or s.get("borough", "")
                zip_    = s.get("zip_code", "N/A")
                lines.append(f"  • {name}, {borough} (zip: {zip_})")
        elif "error" in data:
            lines.append(f"Error: {data['error']}")
        else:
            lines.append(body[:500])

        result = "\n".join(lines)
        print(f"=== Step 4: Parsed Result (what Gemini will speak) ===")
        print(result)
        print()
        print("✅ Pipeline test PASSED")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}: {e.reason}")
    print(e.read().decode())
except Exception as e:
    print(f"❌ Error: {e}")
