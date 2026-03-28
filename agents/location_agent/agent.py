"""
Location Agent — Google ADK
============================
Queries NYC street/geographic data using a bundled Street Centerline
GeoJSON file for geometry + spatial lookups, and the Socrata API for
supplementary restaurant location context.

Deployed as an A2A-capable server on Cloud Run.
"""
from __future__ import annotations

import os
import sys

from google.adk import Agent
from google.adk.tools import FunctionTool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from centerline import get_index, BORO_CODES, BORO_NAMES
from socrata_client import SocrataClient

socrata = SocrataClient(app_token=os.getenv("SOCRATA_APP_TOKEN"))


# ── Tool functions ────────────────────────────────────────────────────────

async def search_streets(
    street_name: str = "",
    borough: str = "",
    zipcode: str = "",
    limit: int = 10,
) -> dict:
    """Search NYC streets by name from the Street Centerline dataset.

    Returns street segments with address ranges, zip codes, traffic info,
    speed limits, and geometry coordinates for navigation.

    Args:
        street_name: Full or partial street name (e.g. 'Broadway', '5th Ave').
        borough: Borough name — Manhattan, Brooklyn, Queens, Bronx, or Staten Island.
        zipcode: NYC zip code to filter by.
        limit: Max results (default 10, max 50).

    Returns:
        dict with matching street segments and their full attributes.
    """
    limit = min(max(limit, 1), 50)
    idx = get_index()
    borocode = BORO_CODES.get(borough.lower(), "") if borough else ""

    segments = idx.search_by_name(
        street_name, borocode=borocode, zipcode=zipcode, limit=limit
    )

    return {
        "count": len(segments),
        "streets": [s.to_dict() for s in segments],
    }


async def find_nearby_streets(
    latitude: float,
    longitude: float,
    radius_meters: float = 500,
    limit: int = 10,
) -> dict:
    """Find streets near a GPS coordinate. Ideal for glasses navigation.

    Given the user's current lat/lon (from the glasses GPS or phone),
    returns nearby streets sorted by distance with full geometry.

    Args:
        latitude: GPS latitude (e.g. 40.7580).
        longitude: GPS longitude (e.g. -73.9855).
        radius_meters: Search radius in meters (default 500, max 2000).
        limit: Max results (default 10, max 30).

    Returns:
        dict with nearby streets, distances, and navigation-ready geometry.
    """
    radius_meters = min(max(radius_meters, 50), 2000)
    limit = min(max(limit, 1), 30)
    idx = get_index()

    nearby = idx.search_nearby(
        lon=longitude, lat=latitude, radius_m=radius_meters, limit=limit
    )

    streets = []
    for seg, dist_m in nearby:
        info = seg.to_dict()
        info["distance_meters"] = round(dist_m, 1)
        info["coordinates"] = seg.coords
        streets.append(info)

    # Also get cross-street names at this location
    intersection_streets = idx.get_streets_at_intersection(
        lon=longitude, lat=latitude, radius_m=50
    )

    return {
        "location": {"lat": latitude, "lon": longitude},
        "radius_m": radius_meters,
        "count": len(streets),
        "nearest_intersection": intersection_streets[:4],
        "streets": streets,
    }


async def get_route_segments(
    street_name: str,
    borough: str = "",
) -> dict:
    """Get ordered street segments for navigation along a street.

    Returns geometry coordinates for each segment sorted south-to-north,
    suitable for rendering a route on a map or providing turn-by-turn context.

    Args:
        street_name: The street to navigate along (e.g. 'Broadway').
        borough: Borough to filter by (optional but recommended).

    Returns:
        dict with ordered segments and their geometries for navigation.
    """
    idx = get_index()
    borocode = BORO_CODES.get(borough.lower(), "") if borough else ""

    segments = idx.get_route_segments(
        street_name=street_name,
        borocode=borocode,
    )

    return {
        "street": street_name,
        "borough": borough or "All",
        "segment_count": len(segments),
        "segments": [s.to_nav_dict() for s in segments[:100]],
    }


async def get_streets_in_area(
    borough: str = "",
    zipcode: str = "",
    limit: int = 20,
) -> dict:
    """List streets in a borough or zip code area.

    Args:
        borough: Borough name — Manhattan, Brooklyn, Queens, Bronx, or Staten Island.
        zipcode: NYC zip code (e.g. '10001').
        limit: Max results (default 20, max 100).

    Returns:
        dict with street names and info in that area.
    """
    if not borough and not zipcode:
        return {"error": "Provide at least a borough or zipcode."}

    limit = min(max(limit, 1), 100)
    idx = get_index()
    borocode = BORO_CODES.get(borough.lower(), "") if borough else ""

    if zipcode and zipcode in idx.zip_index:
        candidate_idxs = idx.zip_index[zipcode][:500]
    elif borocode and borocode in idx.boro_index:
        candidate_idxs = idx.boro_index[borocode][:500]
    else:
        return {"error": "No data found for that area."}

    seen = {}
    for i in candidate_idxs:
        seg = idx.segments[i]
        if borocode and seg.borocode != borocode:
            continue
        if seg.full_street and seg.full_street not in seen:
            seen[seg.full_street] = seg.to_dict()
            if len(seen) >= limit:
                break

    return {
        "area": zipcode or borough,
        "count": len(seen),
        "streets": list(seen.values()),
    }


async def find_restaurants_on_street(
    street_name: str,
    borough: str = "",
    zipcode: str = "",
    limit: int = 15,
) -> dict:
    """Find restaurants on a specific street (live from Socrata API).

    Args:
        street_name: Street name (e.g. 'Broadway', 'Canal St').
        borough: Optional borough filter.
        zipcode: Optional zip code filter.
        limit: Max results (default 15, max 50).

    Returns:
        dict with restaurants on that street.
    """
    limit = min(max(limit, 1), 50)
    rows = await socrata.get_restaurants_on_street(
        street_name=street_name,
        borough=borough or None,
        zipcode=zipcode or None,
        limit=limit,
    )

    seen = {}
    for row in rows:
        camis = row.get("camis", "")
        if camis not in seen:
            seen[camis] = {
                "name": row.get("dba", ""),
                "address": f"{row.get('building', '')} {row.get('street', '')}".strip(),
                "borough": row.get("boro", ""),
                "zipcode": row.get("zipcode", ""),
                "cuisine": row.get("cuisine_description", ""),
                "grade": row.get("grade", "N/A"),
                "latitude": row.get("latitude", ""),
                "longitude": row.get("longitude", ""),
            }

    restaurants = list(seen.values())
    return {
        "street": street_name,
        "count": len(restaurants),
        "restaurants": restaurants,
    }


# ── Agent definition ─────────────────────────────────────────────────────

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="location_agent",
    description=(
        "NYC Location, Street, and Navigation Agent. Uses bundled Street "
        "Centerline geometry data for spatial lookups and navigation, plus "
        "live Socrata API queries for restaurant context."
    ),
    instruction="""You are the NYC Location and Navigation Agent. You help users
find street information and navigate New York City.

You have access to the full NYC Street Centerline dataset (~122K street segments)
with geometry coordinates, address ranges, traffic direction, speed limits, etc.

Tools:
1. **search_streets** — Find streets by name, borough, or zip code.
2. **find_nearby_streets** — Given GPS lat/lon, find streets within a radius.
   This is the primary tool for glasses navigation — when the user's location
   is known, use this to tell them what streets are around them.
3. **get_route_segments** — Get ordered street geometry along a named street.
   Use for navigation: "walk along Broadway in Manhattan."
4. **get_streets_in_area** — List streets in a borough or zip code.
5. **find_restaurants_on_street** — Find restaurants on a street (live data).

For navigation:
- Use find_nearby_streets with the user's GPS to orient them.
- Use get_route_segments to describe a path along a street.
- Mention address ranges, traffic direction, and speed limits.
- When giving directions, reference nearby streets and intersections.

When responding to a GPS lookup, always include:
- The nearest street name and borough
- The zip code (from left_zip or right_zip of the nearest segment) — this is critical for downstream queries

Borough codes: Manhattan=1, Bronx=2, Brooklyn=3, Queens=4, Staten Island=5.
Traffic direction codes: TW=Two-way, FT=With digitized direction, TF=Against.

Never refer to yourself by name or mention that you are a sub-agent. Just answer directly.
""",
    tools=[
        FunctionTool(search_streets),
        FunctionTool(find_nearby_streets),
        FunctionTool(get_route_segments),
        FunctionTool(get_streets_in_area),
        FunctionTool(find_restaurants_on_street),
    ],
)
