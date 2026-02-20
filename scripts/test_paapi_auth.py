#!/usr/bin/env python3
"""
Amazon PA-APIの基本認証テスト（GetItems使用）
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

def test_paapi_basic_auth():
    """PA-APIの基本認証テスト（GetItemsでASIN検索）"""
    
    # 環境変数読み込み
    env_vars = load_env()
    access_key = env_vars.get('AMAZON_ACCESS_KEY')
    secret_key = env_vars.get('AMAZON_SECRET_KEY')
    associate_tag = env_vars.get('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')
    
    if not access_key or not secret_key:
        print("ERROR: AMAZON_ACCESS_KEY または AMAZON_SECRET_KEY が設定されていません")
        return False
    
    print(f"PA-API基本認証テスト中...")
    print(f"Access Key: {access_key[:8]}...")
    print(f"Associate Tag: {associate_tag}")
    print("---")
    
    try:
        # AmazonApiインスタンス作成（日本）
        amazon = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=associate_tag,
            country="JP"
        )
        
        # 既知のASIN（『嫌われる勇気』）でGetItemsテスト
        known_asin = "4478025819"  # 嫌われる勇気のISBN-10
        print(f"GetItems テスト中... (ASIN: {known_asin})")
        
        # シンプルな形式で試す
        products = amazon.get_items(known_asin)
        
        print("✓ PA-API基本認証成功！")
        
        if products:
            for product in products:
                print(f"  ASIN: {getattr(product, 'asin', None)}")
                # デバッグ: productの属性一覧を表示
                print("  product属性一覧:", dir(product))
                print("  product内容:", vars(product))
                # title属性があれば表示、なければ候補を列挙
                if hasattr(product, 'title'):
                    print(f"  タイトル: {product.title}")
                else:
                    print("  タイトル属性なし。候補:")
                    for k in vars(product):
                        if 'title' in k.lower():
                            print(f"    {k}: {getattr(product, k)}")
                if hasattr(product, 'images') and product.images and hasattr(product.images, 'primary') and product.images.primary:
                    print(f"  画像URL: {product.images.primary.medium}")
        else:
            print("  商品情報が空です")
        
        print("---")
        print("次にSearchItemsテストを実行...")
        
        # SearchItemsテスト
        try:
            search_products = amazon.search_items(
                keywords="Python プログラミング",
                search_index="Books",
                item_count=1
            )
            print("✓ SearchItems も成功！")
            print(f"検索結果数: {len(search_products) if search_products else 0}")
            
        except Exception as search_error:
            print(f"✗ SearchItems エラー: {search_error}")
            print("  → GetItemsは成功したがSearchItemsは失敗（制限の可能性）")
        
        return True
        
    except Exception as e:
        print(f"✗ PA-API基本認証エラー:")
        print(f"  エラー: {e}")
        
        error_str = str(e).lower()
        
        # 詳細なエラー分析
        if "forbidden" in error_str:
            print("  → アクセス拒否:")
            print("    1. アソシエイトタグが無効")
            print("    2. PA-API利用条件未満（売上実績不足）")
            print("    3. 認証キーの権限不足")
        elif "invalid signature" in error_str:
            print("  → 署名エラー: 認証キーまたはシークレットが無効")
        elif "not found" in error_str:
            print("  → リソースが見つかりません: ASINまたは設定に問題")
        elif "throttled" in error_str or "too many" in error_str:
            print("  → リクエスト制限: レート制限に達しました")
        else:
            print(f"  → 不明なエラー: {e}")
        
        print("\n診断:")
        print(f"  1. アソシエイト・セントラルでタグを確認: {associate_tag}")
        print(f"  2. AWS IAMでPA-API権限を確認: {access_key[:8]}")
        print("  3. 売上実績（過去30日間で3件以上の売上）を確認")
        
        return False

if __name__ == "__main__":
    success = test_paapi_basic_auth()
    sys.exit(0 if success else 1)