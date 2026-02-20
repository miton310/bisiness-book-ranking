#!/usr/bin/env python3
"""既存書籍データに出版日とカテゴリーを追加取得するスクリプト

PA-APIを使用して、books.jsonの既存ASINから追加情報を取得する。
"""

import json
import time
from pathlib import Path

from paapi_utils import PaapiClient


def update_book_metadata():
    """books.jsonの書籍に出版日とカテゴリーを追加"""

    data_dir = Path(__file__).parent.parent / "data"
    books_path = data_dir / "books.json"

    # 現在のデータを読み込み
    with open(books_path, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"書籍数: {len(books)}")

    # ASINがある書籍を抽出
    books_with_asin = [(i, book) for i, book in enumerate(books) if book.get("asin")]
    print(f"ASIN付き書籍: {len(books_with_asin)}")

    # PA-APIクライアント初期化
    try:
        client = PaapiClient()
    except ValueError as e:
        print(f"[ERROR] PA-API 初期化失敗: {e}")
        return

    # 更新対象（出版日またはカテゴリーがない書籍）
    to_update = [
        (i, book) for i, book in books_with_asin
        if not book.get("publication_date") or not book.get("category")
    ]
    print(f"更新対象: {len(to_update)}")

    if not to_update:
        print("更新対象がありません")
        return

    updated_count = 0

    # 10件ずつバッチ処理
    for batch_start in range(0, len(to_update), 10):
        batch = to_update[batch_start:batch_start + 10]
        asins = [book["asin"] for _, book in batch]

        print(f"\nバッチ {batch_start // 10 + 1}: {len(asins)}件取得中...")

        items = client.get_items(asins)

        for idx, book in batch:
            asin = book["asin"]
            if asin not in items:
                print(f"  {asin}: 取得失敗")
                continue

            item = items[asin]

            # 出版日を更新
            if not book.get("publication_date") and item.get("publication_date"):
                books[idx]["publication_date"] = item["publication_date"]
                print(f"  {asin}: 出版日={item['publication_date']}")
                updated_count += 1

            # カテゴリーを更新
            if not book.get("category") and item.get("category"):
                books[idx]["category"] = item["category"]
                print(f"  {asin}: カテゴリー={item['category']}")
                updated_count += 1

        # レート制限対策
        if batch_start + 10 < len(to_update):
            print("  1秒待機...")
            time.sleep(1)

    # 保存
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {updated_count}件更新")
    print(f"保存先: {books_path}")


if __name__ == "__main__":
    update_book_metadata()
