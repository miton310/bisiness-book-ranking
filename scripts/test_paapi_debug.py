#!/usr/bin/env python3
"""
PA-API詳細デバッグ - 生のHTTPレスポンスを確認
"""
import os
import sys
import json
import hashlib
import hmac
import urllib.request
import urllib.error
from datetime import datetime, timezone

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value
    return env_vars

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(secret_key, date_stamp, region, service):
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing

def test():
    env = load_env()
    access_key = env.get('AMAZON_ACCESS_KEY')
    secret_key = env.get('AMAZON_SECRET_KEY')
    tag = env.get('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')

    host = 'webservices.amazon.co.jp'
    region = 'us-west-2'
    service = 'ProductAdvertisingAPI'
    endpoint = f'https://{host}/paapi5/getitems'
    
    payload = json.dumps({
        "ItemIds": ["4478025819"],
        "Resources": ["ItemInfo.Title"],
        "PartnerTag": tag,
        "PartnerType": "Associates",
    }, separators=(',', ':'))

    now = datetime.now(timezone.utc)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')

    # ペイロードのハッシュ
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    # 正規リクエスト
    canonical_headers = (
        f'content-encoding:amz-1.0\n'
        f'content-type:application/json; charset=utf-8\n'
        f'host:{host}\n'
        f'x-amz-date:{amz_date}\n'
        f'x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems\n'
    )
    signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'

    canonical_request = (
        f'POST\n'
        f'/paapi5/getitems\n'
        f'\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{payload_hash}'
    )

    # 署名文字列
    credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
    string_to_sign = (
        f'AWS4-HMAC-SHA256\n'
        f'{amz_date}\n'
        f'{credential_scope}\n'
        f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    )

    # 署名
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Authorization ヘッダー
    authorization = (
        f'AWS4-HMAC-SHA256 '
        f'Credential={access_key}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )

    headers = {
        'Content-Encoding': 'amz-1.0',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': host,
        'X-Amz-Date': amz_date,
        'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems',
        'Authorization': authorization,
    }

    print(f"=== PA-API 詳細デバッグ ===")
    print(f"Endpoint: {endpoint}")
    print(f"Access Key: {access_key}")
    print(f"Associate Tag: {tag}")
    print(f"Region: {region}")
    print(f"Date: {amz_date}")
    print(f"Payload: {payload}")
    print(f"---")

    req = urllib.request.Request(endpoint, data=payload.encode('utf-8'), headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            print(f"✓ 成功! HTTP {resp.status}")
            print(f"Response: {body[:500]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"✗ HTTP {e.code} {e.reason}")
        print(f"Response Headers:")
        for h, v in e.headers.items():
            print(f"  {h}: {v}")
        print(f"Response Body: {body}")
        
        # エラー解析
        try:
            err = json.loads(body)
            errors = err.get('Errors', err.get('errors', []))
            if isinstance(errors, list):
                for error in errors:
                    code = error.get('Code', error.get('code', ''))
                    msg = error.get('Message', error.get('message', ''))
                    print(f"\n  Error Code: {code}")
                    print(f"  Error Message: {msg}")
        except:
            pass
    except Exception as e:
        print(f"✗ エラー: {e}")

if __name__ == "__main__":
    test()
