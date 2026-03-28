"""
Restaurant Agent — Google ADK
==============================
Queries NYC restaurant inspection data from the Socrata API (NYC Open Data).
Deployed as an A2A-capable server on Cloud Run.
"""
from __future__ import annotations

import json
import os
import sys

from google.adk import Agent
from google.adk.tools import FunctionTool

# Allow imports from parent package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from socrata_client import SocrataClient

client = SocrataClient(app_token=os.getenv("SOCRATA_APP_TOKEN"))


# ── Tool functions ────────────────────────────────────────────────────────

async def search_restaurants(
    name: str = "",
    zipcode: str = "",
    cuisine: str = "",
    borough: str = "",
    grade: str = "",
    limit: int = 10,
) -> dict:
    """Search for NYC restaurants by name, cuisine, zipcode, borough, or grade.

    Args:
        name: Restaurant name to search for (partial match).
        zipcode: NYC zip code to filter by.
        cuisine: Cuisine type like 'Italian', 'Chinese', 'Mexican', etc.
        borough: Borough name — Manhattan, Brooklyn, Queens, Bronx, or Staten Island.
        grade: Health inspection grade — A, B, or C.
        limit: Max number of results (default 10, max 50).

    Returns:
        dict with a list of matching restaurants and their latest inspection info.
    """
    limit = min(max(limit, 1), 50)
    rows = await client.search_restaurants(
        name=name or None,
        zipcode=zipcode or None,
        cuisine=cuisine or None,
        borough=borough or None,
        grade=grade or None,
        limit=limit,
    )

    # Deduplicate by camis (keep latest inspection per restaurant)
    seen: dict[str, dict] = {}
    for row in rows:
        camis = row.get("camis", "")
        if camis not in seen:
            seen[camis] = {
                "camis": camis,
                "name": row.get("dba", ""),
                "borough": row.get("boro", ""),
                "address": f"{row.get('building', '')} {row.get('street', '')}".strip(),
                "zipcode": row.get("zipcode", ""),
                "phone": row.get("phone", ""),
                "cuisine": row.get("cuisine_description", ""),
                "grade": row.get("grade", "N/A"),
                "score": row.get("score", "N/A"),
                "last_inspection": row.get("inspection_date", ""),
                "latitude": row.get("latitude", ""),
                "longitude": row.get("longitude", ""),
            }

    restaurants = list(seen.values())
    return {
        "count": len(restaurants),
        "restaurants": restaurants,
    }


async def get_restaurant_details(camis: str) -> dict:
    """Get full inspection history for a specific restaurant by its CAMIS ID.

    Args:
        camis: The unique CAMIS identifier for the restaurant.

    Returns:
        dict with restaurant info and all inspection records.
    """
    rows = await client.get_restaurant_by_camis(camis)
    if not rows:
        return {"error": f"No restaurant found with CAMIS {camis}"}

    first = rows[0]
    inspections = []
    for row in rows:
        inspections.append({
            "date": row.get("inspection_date", ""),
            "type": row.get("inspection_type", ""),
            "score": row.get("score", ""),
            "grade": row.get("grade", ""),
            "violation_code": row.get("violation_code", ""),
            "violation_description": row.get("violation_description", ""),
            "critical": row.get("critical_flag", ""),
        })

    return {
        "camis": camis,
        "name": first.get("dba", ""),
        "borough": first.get("boro", ""),
        "address": f"{first.get('building', '')} {first.get('street', '')}".strip(),
        "zipcode": first.get("zipcode", ""),
        "phone": first.get("phone", ""),
        "cuisine": first.get("cuisine_description", ""),
        "total_inspections": len(inspections),
        "inspections": inspections,
    }


async def get_grade_summary(
    zipcode: str = "",
    borough: str = "",
) -> dict:
    """Get a summary of restaurant health grades in an area.

    Args:
        zipcode: NYC zip code (e.g. '10001').
        borough: Borough name (e.g. 'Manhattan').

    Returns:
        dict with grade distribution counts.
    """
    rows = await client.get_restaurant_grades_summary(
        zipcode=zipcode or None,
        borough=borough or None,
    )
    return {
        "area": zipcode or borough or "All NYC",
        "grade_distribution": {
            row["grade"]: int(row["restaurant_count"]) for row in rows
        },
    }


# ── Agent definition ─────────────────────────────────────────────────────

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="restaurant_agent",
    description=(
        "NYC Restaurant Inspection Lookup Agent. Searches restaurant health "
        "inspection data from NYC Open Data (DOHMH). Can find restaurants by "
        "name, cuisine, borough, zip code, or grade, and retrieve detailed "
        "inspection histories."
    ),
    instruction="""You are the NYC Restaurant Inspection Agent. You help users
find information about restaurant health inspections in New York City.

Your data comes live from NYC Open Data (DOHMH Restaurant Inspection Results).

When a user asks about a restaurant or restaurants:
1. Use search_restaurants to find matching restaurants.
2. If they want details on a specific restaurant, use get_restaurant_details
   with the CAMIS ID from the search results.
3. If they ask about overall grades in an area, use get_grade_summary.

Always present results clearly:
- Show restaurant name, address, cuisine, and current grade.
- Explain what the grades mean: A = best (0-13 points), B = 14-27, C = 28+.
- If a restaurant has violations, summarize the key ones.
- Note that scores are from the most recent inspection cycle.

Borough codes for reference: Manhattan, Bronx, Brooklyn, Queens, Staten Island.
""",
    tools=[
        FunctionTool(search_restaurants),
        FunctionTool(get_restaurant_details),
        FunctionTool(get_grade_summary),
    ],
)
