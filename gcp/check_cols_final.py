#!/usr/bin/env python3
from google.cloud import storage
import csv

client = storage.Client(project='tourgemini')
bucket = client.bucket('tourgemini-hmda-data')
blob = bucket.blob('raw/hmda_nyc.csv')

# Download and parse
print("Downloading CSV...")
csv_text = blob.download_as_text()
lines = csv_text.split('\n')
reader = csv.DictReader(lines)

first_row = next(reader)
print(f"\nTotal columns: {len(first_row)}\n")
print("Columns containing 'loan' or 'type' or 'property':")
for key in sorted(first_row.keys()):
    if any(x in key.lower() for x in ['loan', 'type', 'property']):
        print(f"  {key}: {first_row[key]}")

print("\nAll columns:")
for key in sorted(first_row.keys()):
    print(f"  {key}")
