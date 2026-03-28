"""
Quick test script for the Socrata client + Centerline data.
Run: python test_socrata.py
No API keys needed — Socrata is free and open.
Centerline tests require: python download_centerline.py (run once first)
"""

import asyncio
import os
from socrata_client import SocrataClient


async def test_socrata():
    """Test live Socrata API queries."""
    client = SocrataClient()

    # ── Test 1: Search restaurants ───────────────────────────────────
    print("=" * 60)
    print("TEST 1: Search for Italian restaurants in Manhattan")
    print("=" * 60)
    results = await client.search_restaurants(
        cuisine="Italian", borough="Manhattan", limit=5
    )
    for r in results:
        print(f"  {r.get('dba', 'N/A'):30s} | Grade: {r.get('grade', 'N/A')} | {r.get('building', '')} {r.get('street', '')}")
    print(f"  -> {len(results)} results returned\n")

    # ── Test 2: Search by restaurant name ────────────────────────────
    print("=" * 60)
    print("TEST 2: Search for 'Joe's Pizza'")
    print("=" * 60)
    results = await client.search_restaurants(name="Joes Pizza", limit=5)
    for r in results:
        print(f"  {r.get('dba', 'N/A'):30s} | {r.get('boro', '')} | Grade: {r.get('grade', 'N/A')}")
    print(f"  -> {len(results)} results returned\n")

    # ── Test 3: Grade summary ────────────────────────────────────────
    print("=" * 60)
    print("TEST 3: Grade distribution in zip 10001 (Chelsea)")
    print("=" * 60)
    results = await client.get_restaurant_grades_summary(zipcode="10001")
    for r in results:
        print(f"  Grade {r.get('grade', '?')}: {r.get('restaurant_count', 0)} restaurants")
    print()

    # ── Test 4: Restaurants on a street ──────────────────────────────
    print("=" * 60)
    print("TEST 4: Restaurants on Broadway in Manhattan")
    print("=" * 60)
    results = await client.get_restaurants_on_street(
        street_name="BROADWAY", borough="Manhattan", limit=5
    )
    for r in results:
        name = r.get("dba", "N/A")
        cuisine = r.get("cuisine_description", "")
        grade = r.get("grade", "N/A")
        print(f"  {name:30s} | {cuisine:20s} | Grade: {grade}")
    print(f"  -> {len(results)} results returned\n")

    print("Socrata API tests completed!\n")


def test_centerline():
    """Test the bundled centerline GeoJSON data."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "centerline.geojson")
    if not os.path.exists(data_path):
        print("=" * 60)
        print("SKIPPING centerline tests (data not downloaded yet)")
        print("Run: python download_centerline.py")
        print("=" * 60)
        return

    from centerline import get_index

    print("Loading centerline data (first load may take 10-30 seconds)...")
    idx = get_index()
    print(f"  Loaded {len(idx.segments)} street segments\n")

    # ── Test 5: Search by name ───────────────────────────────────────
    print("=" * 60)
    print("TEST 5: Search for 'Broadway' in centerline data")
    print("=" * 60)
    results = idx.search_by_name("Broadway", borocode="1", limit=5)
    for s in results:
        d = s.to_dict()
        print(f"  {d['street']:30s} | Addr: {d['address_range']:15s} | {d['borough']} | Zip: {d['left_zip']}")
    print(f"  -> {len(results)} segments found\n")

    # ── Test 6: Nearby streets (Times Square) ────────────────────────
    print("=" * 60)
    print("TEST 6: Streets near Times Square (40.7580, -73.9855)")
    print("=" * 60)
    nearby = idx.search_nearby(lon=-73.9855, lat=40.7580, radius_m=200, limit=5)
    for seg, dist in nearby:
        d = seg.to_dict()
        print(f"  {d['street']:30s} | {dist:.0f}m away | Speed: {d['speed_limit']}mph | Dir: {d['traffic_direction']}")
    print(f"  -> {len(nearby)} streets found\n")

    # ── Test 7: Route segments ───────────────────────────────────────
    print("=" * 60)
    print("TEST 7: Broadway route segments in Manhattan")
    print("=" * 60)
    route = idx.get_route_segments("BROADWAY", borocode="1")
    print(f"  Total segments on Broadway in Manhattan: {len(route)}")
    if route:
        first = route[0]
        last = route[-1]
        print(f"  First segment: addr {first.address_range}, zip {first.l_zip}")
        print(f"  Last segment:  addr {last.address_range}, zip {last.l_zip}")
        print(f"  Points in first segment: {len(first.coords)}")
    print()

    # ── Test 8: Intersection detection ───────────────────────────────
    print("=" * 60)
    print("TEST 8: Streets at Times Square intersection")
    print("=" * 60)
    streets = idx.get_streets_at_intersection(lon=-73.9855, lat=40.7580, radius_m=80)
    for s in streets:
        print(f"  {s}")
    print(f"  -> {len(streets)} streets at intersection\n")

    print("Centerline tests completed!")


async def main():
    await test_socrata()
    test_centerline()
    print("\nAll tests done!")


if __name__ == "__main__":
    asyncio.run(main())
