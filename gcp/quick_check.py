#!/usr/bin/env python3
from google.cloud import storage
import csv
import io

client = storage.Client(project='tourgemini')
bucket = client.bucket('tourgemini-hmda-data')
blob = bucket.blob('raw/hmda_nyc.csv')

# Just read first 1KB to get headers
data = blob.download_as_bytes(start_byte=0, end_byte=5000)
text = data.decode('utf-8')
lines = text.split('\n')[:2]

if lines:
    headers = lines[0].split(',')
    print("Columns in CSV:")
    for h in headers:
        print(f"  {h}")
