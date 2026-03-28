"""
Centerline GeoJSON Loader + Spatial Search
============================================
Loads the NYC Street Centerline GeoJSON into memory and provides
fast spatial lookups by name, bbox, and nearest-neighbor.

No external geo libraries required — uses pure Python with a simple
grid-based spatial index for fast coordinate lookups.

Actual field names from the dataset:
  full_street_name, boroughcode, l_zip, r_zip, streetwidth,
  posted_speed, trafdir, snow_priority, bike_lane, segment_type,
  stname_label, number_travel_lanes, rw_type
  Geometry: MultiLineString
"""
from __future__ import annotations

import json
import logging
import math
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "centerline.geojson")

# Borough code -> name mapping
BORO_NAMES = {
    "1": "Manhattan",
    "2": "Bronx",
    "3": "Brooklyn",
    "4": "Queens",
    "5": "Staten Island",
}
BORO_CODES = {v.lower(): k for k, v in BORO_NAMES.items()}

# Grid cell size in degrees (~0.005 deg ≈ 500m)
GRID_CELL_SIZE = 0.005


def _grid_key(lon: float, lat: float) -> Tuple[int, int]:
    return (int(lon / GRID_CELL_SIZE), int(lat / GRID_CELL_SIZE))


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _multiline_midpoint(coords: list) -> Tuple[float, float]:
    """Get the midpoint of a MultiLineString coordinate array.
    coords is a list of lines, each line is a list of [lon, lat] points.
    """
    # Flatten all points
    all_points = []
    for line in coords:
        all_points.extend(line)
    if not all_points:
        return 0.0, 0.0
    mid_idx = len(all_points) // 2
    return all_points[mid_idx][0], all_points[mid_idx][1]


def _flatten_coords(coords: list) -> list:
    """Flatten MultiLineString coords into a single list of [lon, lat] points."""
    flat = []
    for line in coords:
        flat.extend(line)
    return flat


class StreetSegment:
    """A single street segment from the centerline data."""

    __slots__ = (
        "physical_id", "full_street", "st_label", "borocode",
        "l_zip", "r_zip", "street_width", "trafdir", "posted_speed",
        "bike_lane", "snow_priority", "segment_type", "rw_type",
        "travel_lanes", "l_low_hn", "l_high_hn", "r_low_hn", "r_high_hn",
        "coords", "mid_lon", "mid_lat",
    )

    def __init__(self, feature: dict):
        props = feature.get("properties", {})
        self.physical_id = str(props.get("physicalid", ""))
        self.full_street = props.get("full_street_name", "") or ""
        self.st_label = props.get("stname_label", "") or ""
        self.borocode = str(props.get("boroughcode", ""))
        self.l_zip = str(props.get("l_zip", "") or "")
        self.r_zip = str(props.get("r_zip", "") or "")
        self.street_width = str(props.get("streetwidth", "") or "")
        self.trafdir = props.get("trafdir", "") or ""
        self.posted_speed = str(props.get("posted_speed", "") or "")
        self.bike_lane = str(props.get("bike_lane", "") or "")
        self.snow_priority = props.get("snow_priority", "") or ""
        self.segment_type = props.get("segment_type", "") or ""
        self.rw_type = str(props.get("rw_type", "") or "")
        self.travel_lanes = str(props.get("number_travel_lanes", "") or "")
        # Address ranges
        self.l_low_hn = str(props.get("l_low_hn", "") or "")
        self.l_high_hn = str(props.get("l_high_hn", "") or "")
        self.r_low_hn = str(props.get("r_low_hn", "") or "")
        self.r_high_hn = str(props.get("r_high_hn", "") or "")

        # Geometry (MultiLineString)
        geom = feature.get("geometry", {})
        raw_coords = geom.get("coordinates", [])
        self.coords = _flatten_coords(raw_coords) if raw_coords else []
        if raw_coords:
            self.mid_lon, self.mid_lat = _multiline_midpoint(raw_coords)
        else:
            self.mid_lon, self.mid_lat = 0.0, 0.0

    @property
    def address_range(self) -> str:
        """Human-readable address range for this segment."""
        parts = []
        if self.l_low_hn and self.l_high_hn:
            parts.append(f"{self.l_low_hn}-{self.l_high_hn}")
        elif self.r_low_hn and self.r_high_hn:
            parts.append(f"{self.r_low_hn}-{self.r_high_hn}")
        return " / ".join(parts) if parts else ""

    def to_dict(self) -> dict:
        return {
            "physical_id": self.physical_id,
            "street": self.full_street,
            "label": self.st_label,
            "borough": BORO_NAMES.get(self.borocode, self.borocode),
            "address_range": self.address_range,
            "left_zip": self.l_zip,
            "right_zip": self.r_zip,
            "street_width_ft": self.street_width,
            "traffic_direction": self.trafdir,
            "speed_limit": self.posted_speed,
            "travel_lanes": self.travel_lanes,
            "bike_lane": self.bike_lane,
            "snow_priority": self.snow_priority,
            "segment_type": self.segment_type,
            "midpoint": {"lat": self.mid_lat, "lon": self.mid_lon},
        }

    def to_nav_dict(self) -> dict:
        """Compact dict for navigation with geometry."""
        return {
            "street": self.full_street,
            "address_range": self.address_range,
            "borough": BORO_NAMES.get(self.borocode, self.borocode),
            "direction": self.trafdir,
            "speed_limit": self.posted_speed,
            "coordinates": self.coords,
        }


class CenterlineIndex:
    """In-memory spatial index over the NYC Street Centerline data."""

    def __init__(self):
        self.segments: List[StreetSegment] = []
        self.name_index: Dict[str, List[int]] = defaultdict(list)
        self.grid_index: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        self.boro_index: Dict[str, List[int]] = defaultdict(list)
        self.zip_index: Dict[str, List[int]] = defaultdict(list)
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def load(self, path: str = DATA_PATH) -> None:
        """Load the GeoJSON file and build indexes."""
        if self._loaded:
            return

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Centerline data not found at {path}. "
                f"Run: python download_centerline.py"
            )

        logger.info("Loading centerline GeoJSON from %s ...", path)
        with open(path, "r") as f:
            data = json.load(f)

        features = data.get("features", [])
        logger.info("Parsing %d features...", len(features))

        for i, feature in enumerate(features):
            seg = StreetSegment(feature)
            self.segments.append(seg)

            # Name index (uppercase for case-insensitive search)
            if seg.full_street:
                key = seg.full_street.upper()
                self.name_index[key].append(i)

            # Grid index
            if seg.mid_lon != 0 and seg.mid_lat != 0:
                gk = _grid_key(seg.mid_lon, seg.mid_lat)
                self.grid_index[gk].append(i)

            # Borough index
            if seg.borocode:
                self.boro_index[seg.borocode].append(i)

            # Zip index
            if seg.l_zip:
                self.zip_index[seg.l_zip].append(i)
            if seg.r_zip and seg.r_zip != seg.l_zip:
                self.zip_index[seg.r_zip].append(i)

        self._loaded = True
        logger.info(
            "Centerline loaded: %d segments, %d unique names, %d grid cells",
            len(self.segments),
            len(self.name_index),
            len(self.grid_index),
        )

    def search_by_name(
        self,
        name: str,
        borocode: str = "",
        zipcode: str = "",
        limit: int = 20,
    ) -> List[StreetSegment]:
        """Search street segments by name (partial match)."""
        name_upper = name.upper()
        candidates: List[int] = []

        # Exact name match first
        if name_upper in self.name_index:
            candidates = self.name_index[name_upper]
        else:
            for key, idxs in self.name_index.items():
                if name_upper in key:
                    candidates.extend(idxs)

        results = []
        for idx in candidates:
            seg = self.segments[idx]
            if borocode and seg.borocode != borocode:
                continue
            if zipcode and seg.l_zip != zipcode and seg.r_zip != zipcode:
                continue
            results.append(seg)
            if len(results) >= limit:
                break

        return results

    def search_nearby(
        self,
        lon: float,
        lat: float,
        radius_m: float = 500,
        limit: int = 20,
    ) -> List[Tuple[StreetSegment, float]]:
        """Find street segments near a coordinate. Returns (segment, distance_m)."""
        radius_deg = radius_m / 111000
        cells_to_check = int(radius_deg / GRID_CELL_SIZE) + 1

        center_gx, center_gy = _grid_key(lon, lat)
        candidates: List[Tuple[int, float]] = []

        for dx in range(-cells_to_check, cells_to_check + 1):
            for dy in range(-cells_to_check, cells_to_check + 1):
                gk = (center_gx + dx, center_gy + dy)
                for idx in self.grid_index.get(gk, []):
                    seg = self.segments[idx]
                    dist = _haversine_m(lon, lat, seg.mid_lon, seg.mid_lat)
                    if dist <= radius_m:
                        candidates.append((idx, dist))

        candidates.sort(key=lambda x: x[1])

        # Deduplicate by street name
        seen_streets: set = set()
        results: List[Tuple[StreetSegment, float]] = []
        for idx, dist in candidates:
            seg = self.segments[idx]
            street_key = (seg.full_street, seg.borocode)
            if street_key not in seen_streets:
                seen_streets.add(street_key)
                results.append((seg, dist))
                if len(results) >= limit:
                    break

        return results

    def get_route_segments(
        self,
        street_name: str,
        borocode: str = "",
    ) -> List[StreetSegment]:
        """Get all segments for a street, sorted south-to-north for navigation."""
        segments = self.search_by_name(
            street_name, borocode=borocode, limit=500
        )
        segments.sort(key=lambda s: s.mid_lat)
        return segments

    def get_streets_at_intersection(
        self,
        lon: float,
        lat: float,
        radius_m: float = 50,
    ) -> List[str]:
        """Get street names at or near an intersection."""
        nearby = self.search_nearby(lon, lat, radius_m=radius_m, limit=10)
        return list(set(seg.full_street for seg, _ in nearby if seg.full_street))


# ── Module-level singleton ───────────────────────────────────────────────

_index = CenterlineIndex()


def get_index() -> CenterlineIndex:
    """Get the (lazily-loaded) centerline index singleton."""
    if not _index.loaded:
        _index.load()
    return _index
