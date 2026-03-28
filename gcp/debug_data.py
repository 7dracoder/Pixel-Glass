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

loan_types = Counter()
actions = Counter()
count = 0

for record in reader:
    loan_type = record.get('loan_type_name', '')
    action = record.get('action_taken', '')
    action_name = record.get('action_taken_name', '')
    
    if loan_type:
        loan_types[loan_type] += 1
    actions[f"{action} ({action_name})"] += 1
    count += 1
    if count >= 100000:
        break

print(f"\nProcessed {count} records")
print(f"\nLoan Types found: {len(loan_types)}")
for loan_type, count in loan_types.most_common(10):
    print(f"  {loan_type}: {count}")

print(f"\nAction codes found:")
for action, count in actions.most_common():
    print(f"  {action}: {count}")
