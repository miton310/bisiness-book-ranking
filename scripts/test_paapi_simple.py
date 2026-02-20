#!/usr/bin/env python3
"""
Amazon PA-API python-amazon-paapi使用テスト
"""

import os
import sys
from amazon_paapi import AmazonApi

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

def test_paapi_with_python_amazon_paapi():
    """python-amazon-paapiライブラリを使った接続テスト"""
    
    # 環境変数読み込み
    env_vars = load_env()
    access_key = env_vars.get('AMAZON_ACCESS_KEY')
    secret_key = env_vars.get('AMAZON_SECRET_KEY')
    associate_tag = env_vars.get('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')
    
    if not access_key or not secret_key:
        print("ERROR: AMAZON_ACCESS_KEY または AMAZON_SECRET_KEY が設定されていません")
        return False
    
    print(f"PA-API python-amazon-paapi テスト中...")
    print(f"Access Key: {access_key[:8]}...")
    print(f"Associate Tag: {associate_tag}")
    
    try:
        # AmazonApiインスタンス作成（日本）
        amazon = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=associate_tag,
            country="JP"  # 日本
        )
        
        # 書籍検索テスト
        print("書籍検索テスト中...")
        print(f"国: {amazon.country}")
        print(f"リージョン: {amazon.region}")
        print(f"マーケットプレイス: {amazon.marketplace}")
        print("---")
        
        products = amazon.search_items(
            keywords="嫌われる勇気",
            search_index="Books",
            item_count=1
        )
        
        print("✓ PA-API接続成功！")
        
        if products:
            for product in products:
                print(f"  ASIN: {product.asin}")
                print(f"  タイトル: {product.title}")
                if product.images and product.images.primary:
                    print(f"  画像URL: {product.images.primary.large}")
                if product.prices and product.prices.price:
                    print(f"  価格: {product.prices.price}")
                if product.item_info and product.item_info.by_line_info:
                    authors = [author.name for author in product.item_info.by_line_info.contributors]
                    print(f"  著者: {', '.join(authors)}")
        else:
            print("  検索結果が空です")
        
        return True
        
    except Exception as e:
        print(f"✗ PA-API接続エラー:")
        print(f"  エラー: {e}")
        
        error_str = str(e).lower()
        
        # エラータイプの解析
        if "invalid signature" in error_str:
            print("  → 署名が無効です。認証情報を確認してください。")
        elif "invalid associate" in error_str or "associate tag" in error_str:
            print("  → アソシエイトタグが無効です。")
        elif "access denied" in error_str:
            print("  → アクセスが拒否されました。PA-API利用権限を確認してください。")
        elif "invalid parameter" in error_str:
            print("  → パラメータが無効です。設定を確認してください。")
        elif "too many requests" in error_str:
            print("  → リクエスト数制限に達しました。")
        elif "throttled" in error_str:
            print("  → リクエストレート制限に達しました。")
        
        return False

if __name__ == "__main__":
    success = test_paapi_with_python_amazon_paapi()
    sys.exit(0 if success else 1)