#!/usr/bin/env python
import requests

print("Testing NSE API...")
try:
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    if 'data' in data:
        symbols = [stock['symbol'] for stock in data['data']]
        print(f"Fetched {len(symbols)} symbols")
        print("First 10 symbols:", symbols[:10])
    else:
        print("No 'data' key in response")
        print("Available keys:", list(data.keys()))
except Exception as e:
    print(f"Error: {e}")
