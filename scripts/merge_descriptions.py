#!/usr/bin/env python3
"""紹介文をbooks.jsonにマージするスクリプト

使い方:
  python scripts/merge_descriptions.py <ダウンロードしたJSONファイル>

例:
  python scripts/merge_descriptions.py ~/Downloads/book-descriptions-2026-02-20.json
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("使い方: python scripts/merge_descriptions.py <紹介文JSONファイル>")
        print("例: python scripts/merge_descriptions.py ~/Downloads/book-descriptions-2026-02-20.json")
        sys.exit(1)

    descriptions_file = Path(sys.argv[1])
    if not descriptions_file.exists():
        print(f"エラー: ファイルが見つかりません: {descriptions_file}")
        sys.exit(1)

    # パス設定
    data_dir = Path(__file__).parent.parent / "data"
    books_path = data_dir / "books.json"
    frontend_books_path = Path(__file__).parent.parent / "frontend" / "public" / "data" / "books.json"

    # 紹介文データを読み込み
    with open(descriptions_file, "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    print(f"紹介文データ: {len(descriptions)}件")

    # books.jsonを読み込み
    with open(books_path, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"書籍データ: {len(books)}件")

    # マージ
    desc_map = {d["id"]: d for d in descriptions}
    updated_count = 0

    for book in books:
        if book["id"] in desc_map:
            d = desc_map[book["id"]]
            book["description"] = d["description"]
            if d.get("keywords"):
                book["keywords"] = d["keywords"]
            updated_count += 1
            print(f"  更新: {book['title'][:40]}")

    print(f"\n{updated_count}件の紹介文をマージしました")

    # 保存
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"保存: {books_path}")

    # フロントエンドにもコピー
    with open(frontend_books_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"保存: {frontend_books_path}")

    print("\n完了！")


if __name__ == "__main__":
    main()
