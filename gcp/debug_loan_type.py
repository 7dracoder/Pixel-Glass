#!/usr/bin/env python3
from google.cloud import storage
import csv
from collections import Counter

client = storage.Client(project='tourgemini')
bucket = client.bucket('tourgemini-hmda-data')
blob = bucket.blob('raw/hmda_nyc.csv')

print("Downloading CSV...")
csv_text = blob.download_as_text()
lines = csv_text.split('\n')
reader = csv.DictReader(lines)

# Check first 50 records
print("\nFirst 10 records - loan_type_name values:")
for i, record in enumerate(reader):
    if i < 10:
        loan_type = record.get('loan_type_name', '')
        respondent = record.get('respondent_id', '')
        action = record.get('action_taken', '')
        print(f"  Record {i}: loan_type_name='{loan_type}' | respondent_id='{respondent}' | action='{action}'")
    else:
        break

# Count loan types
print("\nCounting loan types in full dataset...")
reader = csv.DictReader(csv_text.split('\n'))
loan_types = Counter()
count = 0
for record in reader:
    if record.get('respondent_id'):
        loan_type = record.get('loan_type_name', '')
        if loan_type:
            loan_types[loan_type] += 1
        count += 1

print(f"\nProcessed {count} valid records")
print(f"Loan types found in full dataset: {dict(loan_types)}")
