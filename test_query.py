#!/usr/bin/env python3
"""Test script to query the HMDA agent"""

import requests
import json

q = {"question": "What are the denial rates by lender?"}
response = requests.post("http://localhost:8080/query", json=q)
result = response.json()

print("Question:", result['question'])
print("\nAnswer:")
print(result['answer'])
print("\nData Records:", result['data_records'])
