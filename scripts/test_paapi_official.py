#!/usr/bin/env python3
"""
Amazon PA-API公式SDK使用テスト
"""

import os
import sys
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException

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

def test_paapi_with_official_sdk():
    """PA-API公式SDKを使った接続テスト"""
    
    # 環境変数読み込み
    env_vars = load_env()
    access_key = env_vars.get('AMAZON_ACCESS_KEY')
    secret_key = env_vars.get('AMAZON_SECRET_KEY')
    associate_tag = env_vars.get('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')
    
    if not access_key or not secret_key:
        print("ERROR: AMAZON_ACCESS_KEY または AMAZON_SECRET_KEY が設定されていません")
        return False
    
    print(f"PA-API公式SDKテスト中...")
    print(f"Access Key: {access_key[:8]}...")
    print(f"Associate Tag: {associate_tag}")
    
    # PA-API設定（日本）
    host = "webservices.amazon.co.jp"
    region = "us-west-2"
    marketplace = "A1VC38T7YXB528"
    
    # API設定
    default_api = DefaultApi(
        access_key=access_key,
        secret_key=secret_key,
        host=host,
        region=region
    )
    
    # 検索リクエスト作成
    search_items_request = SearchItemsRequest(
        partner_tag=associate_tag,
        partner_type=PartnerType.ASSOCIATES,
        marketplace=marketplace,
        keywords="嫌われる勇気",
        search_index="Books",
        item_count=1,
        resources=[
            SearchItemsResource.IMAGES_PRIMARY_MEDIUM,
            SearchItemsResource.ITEMINFO_TITLE,
            SearchItemsResource.ITEMINFO_BY_LINE_INFO,
            SearchItemsResource.OFFERS_LISTINGS_PRICE
        ]
    )
    
    try:
        # API実行
        response = default_api.search_items(search_items_request)
        
        print("✓ PA-API接続成功！")
        
        if response.search_result is not None:
            for item in response.search_result.items:
                title = item.item_info.title.display_value if item.item_info and item.item_info.title else "N/A"
                asin = item.asin
                print(f"  ASIN: {asin}")
                print(f"  タイトル: {title}")
        else:
            print("  検索結果が空です")
        
        return True
        
    except ApiException as e:
        print(f"✗ PA-API接続エラー:")
        print(f"  HTTP Status: {e.status}")
        print(f"  Reason: {e.reason}")
        print(f"  Body: {e.body}")
        
        # エラータイプの解析
        if "InvalidSignature" in str(e.body):
            print("  → 署名が無効です。認証情報を確認してください。")
        elif "InvalidAssociate" in str(e.body):
            print("  → アソシエイトタグが無効です。")
        elif "AccessDenied" in str(e.body):
            print("  → アクセスが拒否されました。PA-API利用権限を確認してください。")
        elif "InvalidParameterValue" in str(e.body):
            print("  → パラメータが無効です。マーケットプレイスやリージョンを確認してください。")
        elif "TooManyRequests" in str(e.body):
            print("  → リクエスト数制限に達しました。")
            
        return False
    
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_paapi_with_official_sdk()
    sys.exit(0 if success else 1)