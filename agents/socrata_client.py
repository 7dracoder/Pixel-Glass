"""
Socrata API Client for NYC Open Data
=====================================
Lightweight client that queries NYC Open Data endpoints live.
No GCP storage needed - all queries hit the Socrata SODA API directly.

Endpoints used:
  - Restaurant Inspections: https://data.cityofnewyork.us/resource/43nn-pn8j.json
  - 311 Service Requests:   https://data.cityofnewyork.us/resource/erm2-nwe9.json
"""
from __future__ import annotations

import httpx
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

NYC_OPEN_DATA_BASE = "https://data.cityofnewyork.us/resource"

# Dataset identifiers on NYC Open Data (all confirmed to have SODA JSON APIs)
DATASETS = {
    "restaurant_inspections": "43nn-pn8j",
    "service_requests_311": "erm2-nwe9",
}

DEFAULT_LIMIT = 20
TIMEOUT = 30.0


class SocrataClient:
    """Async client for the Socrata SODA API (NYC Open Data)."""

    def __init__(self, app_token: str | None = None):
        """
        Args:
            app_token: Optional Socrata app token. Increases rate limits from
                       ~1 req/s (anonymous) to ~1000 req/s. Get one free at
                       https://data.cityofnewyork.us/profile/edit/developer_settings
        """
        self.app_token = app_token
        self._headers: dict[str, str] = {"Accept": "application/json"}
        if app_token:
            self._headers["X-App-Token"] = app_token

    def _url(self, dataset_key: str) -> str:
        resource_id = DATASETS[dataset_key]
        return f"{NYC_OPEN_DATA_BASE}/{resource_id}.json"

    async def query(
        self,
        dataset_key: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict]:
        """
        Execute a SoQL query against a NYC Open Data dataset.

        Args:
            dataset_key: One of the keys in DATASETS (e.g. "restaurant_inspections")
            params: SoQL parameters like $where, $select, $order, $limit, $offset, $q

        Returns:
            List of result dicts
        """
        url = self._url(dataset_key)
        params = params or {}
        params.setdefault("$limit", str(DEFAULT_LIMIT))

        logger.info("Socrata query: %s  params=%s", dataset_key, params)

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=self._headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        logger.info("Socrata returned %d rows", len(data))
        return data

    # ── Restaurant-specific helpers ──────────────────────────────────────

    async def search_restaurants(
        self,
        name: str | None = None,
        zipcode: str | None = None,
        cuisine: str | None = None,
        borough: str | None = None,
        grade: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        """Search NYC restaurant inspection records with filters."""
        clauses: list[str] = []
        if name:
            clauses.append(f"upper(dba) LIKE '%{name.upper().replace(chr(39), '')}%'")
        if zipcode:
            clauses.append(f"zipcode='{zipcode}'")
        if cuisine:
            clauses.append(
                f"upper(cuisine_description) LIKE '%{cuisine.upper().replace(chr(39), '')}%'"
            )
        if borough:
            clauses.append(f"upper(boro) LIKE '%{borough.upper().replace(chr(39), '')}%'")
        if grade:
            clauses.append(f"grade='{grade.upper()}'")

        params: dict[str, str] = {
            "$select": (
                "camis, dba, boro, building, street, zipcode, phone, "
                "cuisine_description, inspection_date, action, violation_code, "
                "violation_description, critical_flag, score, grade, "
                "inspection_type, latitude, longitude"
            ),
            "$order": "inspection_date DESC",
            "$limit": str(limit),
        }
        if clauses:
            params["$where"] = " AND ".join(clauses)

        return await self.query("restaurant_inspections", params)

    async def get_restaurant_by_camis(self, camis: str) -> list[dict]:
        """Get all inspection records for a specific restaurant by CAMIS ID."""
        return await self.query(
            "restaurant_inspections",
            {
                "$where": f"camis='{camis}'",
                "$order": "inspection_date DESC",
                "$limit": "50",
            },
        )

    async def get_restaurant_grades_summary(
        self,
        zipcode: str | None = None,
        borough: str | None = None,
    ) -> list[dict]:
        """Aggregate grade distribution for an area."""
        clauses: list[str] = ["grade IS NOT NULL"]
        if zipcode:
            clauses.append(f"zipcode='{zipcode}'")
        if borough:
            clauses.append(f"upper(boro) LIKE '%{borough.upper()}%'")

        return await self.query(
            "restaurant_inspections",
            {
                "$select": "grade, count(camis) as restaurant_count",
                "$where": " AND ".join(clauses),
                "$group": "grade",
                "$order": "restaurant_count DESC",
            },
        )

    # ── Location helpers (via restaurant data + 311) ─────────────────────

    async def get_restaurants_on_street(
        self,
        street_name: str,
        borough: str | None = None,
        zipcode: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        """Find restaurants on a given street (uses restaurant inspection data)."""
        clauses: list[str] = [
            f"upper(street) LIKE '%{street_name.upper().replace(chr(39), '')}%'"
        ]
        if borough:
            clauses.append(f"upper(boro) LIKE '%{borough.upper().replace(chr(39), '')}%'")
        if zipcode:
            clauses.append(f"zipcode='{zipcode}'")

        return await self.query(
            "restaurant_inspections",
            {
                "$select": (
                    "camis, dba, boro, building, street, zipcode, "
                    "cuisine_description, grade, latitude, longitude"
                ),
                "$where": " AND ".join(clauses),
                "$order": "dba ASC",
                "$limit": str(limit),
            },
        )

    async def get_distinct_streets(
        self,
        borough: str | None = None,
        zipcode: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        """Get distinct street names from restaurant data for an area."""
        clauses: list[str] = []
        if borough:
            clauses.append(f"upper(boro) LIKE '%{borough.upper().replace(chr(39), '')}%'")
        if zipcode:
            clauses.append(f"zipcode='{zipcode}'")

        params: dict[str, str] = {
            "$select": "street, count(camis) as restaurant_count",
            "$group": "street",
            "$order": "restaurant_count DESC",
            "$limit": str(limit),
        }
        if clauses:
            params["$where"] = " AND ".join(clauses)

        return await self.query("restaurant_inspections", params)

    async def search_311_location(
        self,
        street_name: str | None = None,
        borough: str | None = None,
        zipcode: str | None = None,
        complaint_type: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        """Search 311 service requests for location context.

        The 311 dataset has rich address data including street, cross streets,
        borough, zip, lat/lon for millions of NYC locations.
        """
        clauses: list[str] = []
        if street_name:
            clauses.append(
                f"upper(street_name) LIKE '%{street_name.upper().replace(chr(39), '')}%'"
            )
        if borough:
            clauses.append(
                f"upper(borough) LIKE '%{borough.upper().replace(chr(39), '')}%'"
            )
        if zipcode:
            clauses.append(f"incident_zip='{zipcode}'")
        if complaint_type:
            clauses.append(
                f"upper(complaint_type) LIKE '%{complaint_type.upper().replace(chr(39), '')}%'"
            )

        params: dict[str, str] = {
            "$select": (
                "unique_key, complaint_type, descriptor, "
                "incident_address, street_name, cross_street_1, cross_street_2, "
                "borough, incident_zip, latitude, longitude, "
                "created_date, status"
            ),
            "$order": "created_date DESC",
            "$limit": str(limit),
        }
        if clauses:
            params["$where"] = " AND ".join(clauses)

        return await self.query("service_requests_311", params)

    async def get_location_context(
        self,
        zipcode: str | None = None,
        borough: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get distinct streets and cross-street info for an area via 311 data."""
        clauses: list[str] = ["street_name IS NOT NULL"]
        if zipcode:
            clauses.append(f"incident_zip='{zipcode}'")
        if borough:
            clauses.append(
                f"upper(borough) LIKE '%{borough.upper().replace(chr(39), '')}%'"
            )

        return await self.query(
            "service_requests_311",
            {
                "$select": (
                    "street_name, cross_street_1, cross_street_2, "
                    "incident_zip, borough, count(*) as request_count"
                ),
                "$where": " AND ".join(clauses),
                "$group": "street_name, cross_street_1, cross_street_2, incident_zip, borough",
                "$order": "request_count DESC",
                "$limit": str(limit),
            },
        )
