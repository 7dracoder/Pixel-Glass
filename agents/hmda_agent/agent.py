"""
HMDA Mortgage Lending Analysis Agent — Google ADK
=================================================
Analyzes NYC Home Mortgage Disclosure Act (HMDA) lending data.
Loads mortgage application data from GCS and provides statistical analysis
on approval/denial rates, disparities, and lending patterns.

Run locally:   adk run nyc-agents
Serve as A2A:  adk api_server --port 8080 nyc-agents
Deploy:        gcloud run deploy nyc-agents --source .
"""
from __future__ import annotations

import logging
import os
import sys
import csv
from collections import defaultdict
from typing import Optional

from google.adk import Agent
from google.adk.tools import FunctionTool
from google.cloud import storage

# Allow imports from parent package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global HMDA data cache
hmda_records: list[dict] = []
data_loaded = False


def _load_hmda_data() -> bool:
    """Load HMDA data from GCS and parse into memory."""
    global hmda_records, data_loaded

    if data_loaded:
        return True

    logger.info("📥 Loading HMDA CSV from GCS...")

    try:
        client = storage.Client(project="tourgemini")
        bucket = client.bucket("tourgemini-hmda-data")
        blob = bucket.blob("raw/hmda_nyc.csv")

        logger.info("   Downloading CSV...")
        csv_text = blob.download_as_text()

        logger.info("   Parsing CSV...")
        lines = csv_text.split("\n")
        reader = csv.DictReader(lines)

        hmda_records = [row for row in reader if row and row.get("respondent_id")]
        data_loaded = True

        logger.info(f"✅ Loaded {len(hmda_records)} HMDA records successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error loading data: {str(e)}", exc_info=True)
        return False


# ── Tool functions ────────────────────────────────────────────────────────


async def get_lending_summary() -> dict:
    """Get overall NYC mortgage lending statistics and approval/denial rates.

    Provides a high-level overview of mortgage applications including total volume,
    approval rates, denial rates, and withdrawal rates.

    Returns:
        dict with summary statistics including total applications and approval/denial rates.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    total = len(hmda_records)
    approved = sum(1 for r in hmda_records if r.get("action_taken") == "1")
    denied = sum(1 for r in hmda_records if r.get("action_taken") == "3")
    withdrawn = sum(1 for r in hmda_records if r.get("action_taken") == "4")

    return {
        "total_applications": total,
        "approved": approved,
        "denied": denied,
        "withdrawn": withdrawn,
        "approval_rate_percent": round((approved / total * 100) if total > 0 else 0, 2),
        "denial_rate_percent": round((denied / total * 100) if total > 0 else 0, 2),
        "withdrawal_rate_percent": round(
            (withdrawn / total * 100) if total > 0 else 0, 2
        ),
    }


async def get_denial_rates_by_lender(limit: int = 10) -> dict:
    """Get mortgage denial/approval rates broken down by lender.

    Shows the top lenders by application volume with their respective
    approval and denial rates.

    Args:
        limit: Maximum number of lenders to return (default 10, max 50).

    Returns:
        dict with lender statistics and approval/denial rates.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    limit = min(max(limit, 1), 50)
    lender_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})

    for record in hmda_records:
        lender = record.get("respondent_id", "Unknown")
        action = record.get("action_taken", "")

        lender_stats[lender]["total"] += 1
        if action == "3":
            lender_stats[lender]["denied"] += 1
        elif action == "1":
            lender_stats[lender]["approved"] += 1

    # Calculate rates and sort by total applications
    results = []
    for lender, stats in lender_stats.items():
        denial_rate = (
            (stats["denied"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        approval_rate = (
            (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        results.append(
            {
                "lender_id": lender,
                "total_applications": stats["total"],
                "denied": stats["denied"],
                "approved": stats["approved"],
                "denial_rate_percent": round(denial_rate, 2),
                "approval_rate_percent": round(approval_rate, 2),
            }
        )

    # Sort by total applications (descending) and return top N
    results_sorted = sorted(results, key=lambda x: x["total_applications"], reverse=True)
    return {
        "count": len(results_sorted[:limit]),
        "lenders": results_sorted[:limit],
    }


async def get_denial_rates_by_income() -> dict:
    """Get mortgage denial rates broken down by applicant income level.

    Shows approval and denial statistics for different income brackets,
    useful for understanding lending patterns across socioeconomic groups.

    Returns:
        dict with income bracket statistics and approval/denial rates.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    income_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})

    for record in hmda_records:
        try:
            income = int(record.get("applicant_income_000s", "0") or "0")
            action = record.get("action_taken", "")

            # Bracket by income (in thousands)
            if income < 50:
                bracket = "Under $50k"
            elif income < 100:
                bracket = "$50k-$100k"
            elif income < 150:
                bracket = "$100k-$150k"
            elif income < 250:
                bracket = "$150k-$250k"
            else:
                bracket = "Over $250k"

            income_stats[bracket]["total"] += 1
            if action == "3":
                income_stats[bracket]["denied"] += 1
            elif action == "1":
                income_stats[bracket]["approved"] += 1
        except (ValueError, TypeError):
            pass

    result = {}
    for bracket in [
        "Under $50k",
        "$50k-$100k",
        "$100k-$150k",
        "$150k-$250k",
        "Over $250k",
    ]:
        if bracket in income_stats:
            stats = income_stats[bracket]
            denial_rate = (
                (stats["denied"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            approval_rate = (
                (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            result[bracket] = {
                "total_applications": stats["total"],
                "denied": stats["denied"],
                "approved": stats["approved"],
                "denial_rate_percent": round(denial_rate, 2),
                "approval_rate_percent": round(approval_rate, 2),
            }

    return {"income_brackets": result}


async def get_lending_disparities_by_race() -> dict:
    """Get mortgage approval/denial disparities by applicant race/ethnicity.

    Analyzes lending patterns across racial and ethnic groups to identify
    potential disparities in approval rates. Data comes from official HMDA disclosures.

    Returns:
        dict with approval/denial statistics by race/ethnicity.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    race_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})

    race_map = {
        "1": "White",
        "2": "Black/African American",
        "3": "Asian",
        "4": "Native American",
        "5": "Pacific Islander",
        "6": "Hispanic",
        "7": "Multiple Race",
    }

    for record in hmda_records:
        race_code = record.get("applicant_race_1", "")
        action = record.get("action_taken", "")

        if race_code in race_map:
            race = race_map[race_code]
            race_stats[race]["total"] += 1
            if action == "3":
                race_stats[race]["denied"] += 1
            elif action == "1":
                race_stats[race]["approved"] += 1

    result = {}
    for race in sorted(race_stats.keys()):
        stats = race_stats[race]
        # Only include groups with significant data (100+ applications)
        if stats["total"] >= 100:
            denial_rate = (
                (stats["denied"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            approval_rate = (
                (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            result[race] = {
                "total_applications": stats["total"],
                "denied": stats["denied"],
                "approved": stats["approved"],
                "denial_rate_percent": round(denial_rate, 2),
                "approval_rate_percent": round(approval_rate, 2),
            }

    return {
        "note": "Key metric for monitoring fair lending practices under the Fair Housing Act",
        "disparities": result,
    }


async def get_lending_by_loan_type() -> dict:
    """Get mortgage approval/denial rates broken down by loan type.

    Analyzes lending patterns across different loan products including
    conventional, FHA, VA, and USDA loans.

    Returns:
        dict with approval/denial statistics by loan type.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    type_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})

    for record in hmda_records:
        loan_type_name = record.get("loan_type_name", "")
        action = record.get("action_taken", "")

        if loan_type_name:
            type_stats[loan_type_name]["total"] += 1
            if action == "3":
                type_stats[loan_type_name]["denied"] += 1
            elif action == "1":
                type_stats[loan_type_name]["approved"] += 1

    result = {}
    for loan_type in sorted(type_stats.keys()):
        stats = type_stats[loan_type]
        denial_rate = (
            (stats["denied"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        approval_rate = (
            (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        result[loan_type] = {
            "total_applications": stats["total"],
            "denied": stats["denied"],
            "approved": stats["approved"],
            "denial_rate_percent": round(denial_rate, 2),
            "approval_rate_percent": round(approval_rate, 2),
        }

    return {"loan_types": result}


async def get_lending_by_property_type() -> dict:
    """Get mortgage approval/denial rates broken down by property type.

    Analyzes lending patterns across single-family homes, multifamily buildings,
    manufactured homes, and other property types.

    Returns:
        dict with approval/denial statistics by property type.
    """
    if not await _ensure_data_loaded():
        return {"error": "Failed to load HMDA data"}

    property_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})

    for record in hmda_records:
        prop_type = record.get("property_type_name", "")
        action = record.get("action_taken", "")

        if prop_type:
            property_stats[prop_type]["total"] += 1
            if action == "3":
                property_stats[prop_type]["denied"] += 1
            elif action == "1":
                property_stats[prop_type]["approved"] += 1

    result = {}
    for prop_type in sorted(property_stats.keys()):
        stats = property_stats[prop_type]
        denial_rate = (
            (stats["denied"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        approval_rate = (
            (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )
        result[prop_type] = {
            "total_applications": stats["total"],
            "denied": stats["denied"],
            "approved": stats["approved"],
            "denial_rate_percent": round(denial_rate, 2),
            "approval_rate_percent": round(approval_rate, 2),
        }

    return {"property_types": result}


# Helper to ensure data is loaded
async def _ensure_data_loaded() -> bool:
    """Ensure HMDA data is loaded, loading if necessary."""
    global data_loaded
    if not data_loaded:
        return _load_hmda_data()
    return True


# ── Agent Definition ──────────────────────────────────────────────────────

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="hmda_agent",
    description=(
        "HMDA Mortgage Lending Analysis Agent. Analyzes Home Mortgage Disclosure Act (HMDA) "
        "data for NYC to answer questions about mortgage lending patterns, approval/denial rates, "
        "disparities by race/ethnicity, income level, lender, and property type."
    ),
    instruction="""You are the HMDA Mortgage Lending Analysis Agent. You provide insights
into mortgage lending patterns in New York City using official HMDA data.

You have access to NYC mortgage application data with the following analysis capabilities:

**Available Analysis Tools:**
1. **get_lending_summary** — Overall NYC mortgage lending statistics.
   Shows total applications, approval rate, denial rate, and withdrawal rate.

2. **get_denial_rates_by_lender** — Analysis by lender/institution.
   Get approval and denial rates for major lenders (banks, credit unions, etc).

3. **get_denial_rates_by_income** — Analysis by applicant income level.
   Shows approval/denial patterns across income brackets from under $50k to over $250k.

4. **get_lending_disparities_by_race** — Demographic disparity analysis.
   Analyzes approval/denial rates by race and ethnicity to identify fair lending issues.
   Critical for monitoring compliance with Fair Housing Act requirements.

5. **get_lending_by_loan_type** — Analysis by loan product.
   Shows statistics for conventional, FHA, VA, and USDA loans.

6. **get_lending_by_property_type** — Analysis by property type.
   Breaks down lending by single-family homes, multifamily, manufactured homes, etc.

**How to help users:**
- When asked about overall lending trends → use get_lending_summary
- When asked about specific lenders → use get_denial_rates_by_lender
- When asked about income-based patterns → use get_denial_rates_by_income
- When asked about racial disparities or fair lending → use get_lending_disparities_by_race
- When asked about loan types (FHA, VA, conventional) → use get_lending_by_loan_type
- When asked about property types → use get_lending_by_property_type
- For general questions, combine relevant tools to provide comprehensive analysis

**Important Notes:**
- All data comes from official HMDA filings (updated regularly)
- Analysis helps identify disparities and monitor fair lending practices
- Disparities in approval rates by race/ethnicity are tracked under Fair Housing Act requirements
- Compare rates ratios (e.g., approval rate for one group vs another) to understand disparities

Always cite that data comes from HMDA (Home Mortgage Disclosure Act) filings.
""",
    tools=[
        FunctionTool(get_lending_summary),
        FunctionTool(get_denial_rates_by_lender),
        FunctionTool(get_denial_rates_by_income),
        FunctionTool(get_lending_disparities_by_race),
        FunctionTool(get_lending_by_loan_type),
        FunctionTool(get_lending_by_property_type),
    ],
)
