#!/usr/bin/env python3
"""ISBNなしの書籍をCSV出力するスクリプト"""

import json
import csv
from pathlib import Path

def main():
    data_dir = Path(__file__).parent.parent / "data"
    books_path = data_dir / "books.json"
    output_path = data_dir / "books_no_isbn_edit.csv"

    with open(books_path, "r", encoding="utf-8") as f:
        books = json.load(f)

    # ISBNなしの書籍を抽出
    no_isbn_books = [b for b in books if not b.get("isbn")]

    # 既存CSVを読み込み（手動入力済みデータを保持）
    existing = {}
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["id"]] = row

    # 既存データを保持しつつ新規分を追加
    new_count = 0
    rows = []
    for book in no_isbn_books:
        book_id = book.get("id", "")
        if book_id in existing:
            rows.append(existing[book_id])
        else:
            title = book.get("title", "").replace("『", "").replace("』", "")
            rows.append({
                "id": book_id,
                "title": title,
                "search_title": "",
                "delete": "",
                "isbn": "",
                "count": "",
            })
            new_count += 1

    print(f"=== ISBNなし書籍のCSV出力 ===")
    print(f"全書籍: {len(books)}件")
    print(f"ISBNなし: {len(no_isbn_books)}件")
    print(f"既存: {len(existing)}件")
    print(f"新規追加: {new_count}件")

    # CSV出力
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "search_title", "delete", "isbn", "count"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"出力: {output_path}")
    print("=== 完了 ===")

if __name__ == "__main__":
    main()
