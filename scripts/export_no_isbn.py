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

    print(f"=== ISBNなし書籍のCSV出力 ===")
    print(f"全書籍: {len(books)}件")
    print(f"ISBNなし: {len(no_isbn_books)}件")

    # CSV出力
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "search_title", "delete", "isbn", "count"])

        for book in no_isbn_books:
            title = book.get("title", "")
            # 『』を削除
            title = title.replace("『", "").replace("』", "")
            writer.writerow([
                book.get("id", ""),
                title,
                "",  # search_title（空欄、手動入力用）
                "",  # delete（1を入力すると削除）
                "",  # isbn（手動入力用）
                ""   # count
            ])

    print(f"出力: {output_path}")
    print("=== 完了 ===")

if __name__ == "__main__":
    main()
