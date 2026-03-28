"""
Download NYC Street Centerline GeoJSON — run this ONCE locally.
=================================================================
Downloads the CSCL dataset from NYC Open Data and saves it as
data/centerline.geojson inside the agents folder.

Usage:
    python download_centerline.py

The file is ~120MB. It only needs to be downloaded once — it's bundled
into the Docker image for Cloud Run deployment.
"""

import os
import sys
import urllib.request
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "centerline.geojson")

# NYC Open Data GeoJSON export URL for the Centerline dataset (3mf9-qshr)
GEOJSON_URL = (
    "https://data.cityofnewyork.us/api/geospatial/3mf9-qshr"
    "?method=export&type=GeoJSON"
)


def download():
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_FILE):
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"File already exists: {OUTPUT_FILE} ({size_mb:.1f} MB)")
        resp = input("Re-download? [y/N] ").strip().lower()
        if resp != "y":
            print("Skipped.")
            return

    print(f"Downloading NYC Street Centerline GeoJSON...")
    print(f"  URL: {GEOJSON_URL}")
    print(f"  This may take 1-3 minutes (~120 MB)...\n")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  {mb:.1f} / {total_mb:.1f} MB ({pct:.0f}%)")
        else:
            mb = downloaded / (1024 * 1024)
            sys.stdout.write(f"\r  {mb:.1f} MB downloaded...")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(GEOJSON_URL, OUTPUT_FILE, reporthook=progress)
        print()
    except Exception as e:
        print(f"\n\nDownload failed: {e}")
        print("\nAlternative: download manually from:")
        print("  https://data.cityofnewyork.us/City-Government/Centerline/3mf9-qshr")
        print("  Click Export -> GeoJSON -> Download")
        print(f"  Save as: {OUTPUT_FILE}")
        sys.exit(1)

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\nSaved to: {OUTPUT_FILE} ({size_mb:.1f} MB)")

    # Quick validation
    print("Validating GeoJSON...")
    with open(OUTPUT_FILE, "r") as f:
        # Just parse the first chunk to validate it's valid JSON
        header = f.read(200)
        if '"type"' in header and '"Feature"' in header:
            print("  Valid GeoJSON detected.")
        else:
            print("  WARNING: File may not be valid GeoJSON. Check the download.")

    print("\nDone! The centerline data is ready.")
    print("You can now run the agents with: adk run .")


if __name__ == "__main__":
    download()
