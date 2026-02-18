#!/usr/bin/env python3
"""
Amazon Creators API テストスクリプト
"""
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

CREATORS_API_ID = os.getenv('CREATORS_API_ID')
CREATORS_API_SECRET = os.getenv('CREATORS_API_SECRET')
CREATORS_API_VERSION = os.getenv('CREATORS_API_VERSION')
ASSOCIATE_TAG = os.getenv('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')

# エンドポイント（仮）
ENDPOINT = 'https://api.amazon.com/creatorsapi/searchitems'  # 実際のURLは管理画面で要確認

headers = {
    'Content-Type': 'application/json',
    'x-api-key': CREATORS_API_ID,
    'x-api-secret': CREATORS_API_SECRET,
    'x-api-version': CREATORS_API_VERSION,
}

payload = {
    "Keywords": "嫌われる勇気",
    "SearchIndex": "Books",
    "ItemCount": 1,
    "PartnerTag": ASSOCIATE_TAG,
    "Marketplace": "A1VC38T7YXB528"
}

print("=== Creators API テスト ===")
print("Endpoint:", ENDPOINT)
print("Headers:", headers)
print("Payload:", payload)

try:
    response = requests.post(ENDPOINT, headers=headers, json=payload, timeout=30)
    print("Status:", response.status_code)
    print("Response:")
    print(response.text)
except Exception as e:
    print("Error:", e)
