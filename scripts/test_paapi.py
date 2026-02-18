#!/usr/bin/env python3
"""
Amazon PA-API接続テスト用スクリプト
"""

import os
import sys
from datetime import datetime
import hashlib
import hmac
import urllib.parse
import urllib.request
import json

# 環境変数から認証情報を読み込み
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        return env_vars
    except FileNotFoundError:
        print("ERROR: .envファイルが見つかりません")
        return {}

def create_signature(method, host, path, query_string, headers, secret_key):
    """PA-API用の署名を作成"""
    # 正規化されたクエリ文字列を作成
    sorted_params = sorted(query_string.split('&'))
    canonical_query_string = '&'.join(sorted_params)
    
    # 正規化されたヘッダーを作成
    signed_headers = ';'.join(sorted([h.lower() for h in headers.keys()]))
    canonical_headers = '\n'.join([f"{k.lower()}:{v}" for k, v in sorted(headers.items())]) + '\n'
    
    # 正規化されたリクエスト
    canonical_request = f"{method}\n{path}\n{canonical_query_string}\n{canonical_headers}\n{signed_headers}\n{hashlib.sha256(b'').hexdigest()}"
    
    # 署名文字列を作成（日本リージョン用）
    timestamp = headers.get('X-Amz-Date', '')
    date_stamp = timestamp[:8]
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/us-west-2/ProductAdvertisingAPI/aws4_request"
    string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    # 署名キーを作成
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, 'us-west-2')
    k_service = sign(k_region, 'ProductAdvertisingAPI')
    k_signing = sign(k_service, 'aws4_request')
    
    # 最終署名
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    return signature, signed_headers

def test_paapi_connection():
    """PA-API接続テスト"""
    
    # 環境変数読み込み
    env_vars = load_env()
    access_key = env_vars.get('AMAZON_ACCESS_KEY')
    secret_key = env_vars.get('AMAZON_SECRET_KEY')
    associate_tag = env_vars.get('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')
    
    if not access_key or not secret_key:
        print("ERROR: AMAZON_ACCESS_KEY または AMAZON_SECRET_KEY が設定されていません")
        return False
    
    # API設定（日本のマーケットプレイス用）
    host = 'webservices.amazon.co.jp'
    path = '/paapi5/searchitems'
    method = 'POST'
    
    # タイムスタンプ
    now = datetime.utcnow()
    timestamp = now.strftime('%Y%m%dT%H%M%SZ')
    
    # ヘッダー
    headers = {
        'Authorization': '',  # 後で設定
        'Content-Encoding': 'amz-1.0',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': host,
        'X-Amz-Date': timestamp,
        'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'
    }
    
    # リクエストボディ（日本のマーケットプレイス用）
    payload = {
        "Keywords": "嫌われる勇気",
        "Resources": [
            "Images.Primary.Medium",
            "ItemInfo.Title",
            "ItemInfo.ByLineInfo",
            "Offers.Listings.Price"
        ],
        "SearchIndex": "Books",
        "ItemCount": 1,
        "PartnerTag": associate_tag,
        "PartnerType": "Associates",
        "Marketplace": "A1VC38T7YXB528"
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # クエリ文字列（POSTなので空）
    query_string = ''
    
    try:
        # 署名を作成
        signature, signed_headers = create_signature(method, host, path, query_string, headers, secret_key)
        
        # Authorization ヘッダーを作成（日本リージョン用）
        credential = f"{access_key}/{timestamp[:8]}/us-west-2/ProductAdvertisingAPI/aws4_request"
        headers['Authorization'] = f"AWS4-HMAC-SHA256 Credential={credential}, SignedHeaders={signed_headers}, Signature={signature}"
        
        # リクエスト送信
        url = f"https://{host}{path}"
        req = urllib.request.Request(url, data=payload_json.encode('utf-8'), headers=headers)
        
        print(f"PA-API接続テスト中...")
        print(f"URL: {url}")
        print(f"Access Key: {access_key[:8]}...")
        print(f"Associate Tag: {associate_tag}")
        print(f"Marketplace: A1VC38T7YXB528")
        print(f"Region: us-west-2")
        print("---")
        print(f"Request Headers:")
        for key, value in headers.items():
            if 'Authorization' not in key:
                print(f"  {key}: {value}")
        print(f"Request Body: {payload_json}")
        print("---")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("✓ PA-API接続成功！")
            
            if 'SearchResult' in result and 'Items' in result['SearchResult']:
                items = result['SearchResult']['Items']
                if items:
                    item = items[0]
                    title = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'N/A')
                    print(f"  テスト取得書籍: {title}")
                    return True
            
            print("  検索結果が取得できませんでした")
            print(f"  Response: {result}")
            return False
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ PA-API接続エラー: HTTP {e.code}")
        print(f"  Error: {error_body}")
        
        try:
            error_json = json.loads(error_body)
            if '__type' in error_json:
                error_type = error_json['__type']
                print(f"  Error Type: {error_type}")
                
                if 'InvalidSignature' in error_type:
                    print("  → 署名が無効です。認証情報を確認してください。")
                elif 'InvalidAssociate' in error_type:
                    print("  → アソシエイトタグが無効です。")
                elif 'AccessDenied' in error_type:
                    print("  → アクセスが拒否されました。権限を確認してください。")
                elif 'TooManyRequests' in error_type:
                    print("  → リクエスト数制限に達しました。")
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"✗ 接続エラー: {e}")
        return False

if __name__ == "__main__":
    success = test_paapi_connection()
    sys.exit(0 if success else 1)