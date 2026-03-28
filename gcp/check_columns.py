#!/usr/bin/env python3
from google.cloud import storage
import csv

client = storage.Client(project='tourgemini')
bucket = client.bucket('tourgemini-hmda-data')
blob = bucket.blob('raw/hmda_nyc.csv')
csv_text = blob.download_as_text()

lines = csv_text.split('\n')
reader = csv.DictReader(lines)

first_row = next(reader)
print("All available columns:")
for key in sorted(first_row.keys()):
    print(f"  {key}")

# Check sample data
print("\nChecking for loan/property type fields:")
relevant_cols = [k for k in first_row.keys() if any(x in k.lower() for x in ['loan', 'type', 'property'])]
print(f"Relevant columns: {relevant_cols}")

# Show sample values
reader = csv.DictReader(csv_text.split('\n'))
print("\nSample data from first 5 rows:")
for i, row in enumerate(reader):
    if i < 5:
        print(f"\nRow {i}:")
        for col in relevant_cols:
            print(f"  {col}: {row.get(col, 'N/A')}")
    else:
        break
