#!/usr/bin/env python3
"""
ISBN-13からASINを取得してamazon_urlを更新するスクリプト

ISBN-13（978始まり）をISBN-10に変換し、ASINとして使用。
amazon_urlを直接商品ページURLに更新する。
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BOOKS_FILE = DATA_DIR / "books.json"
AMAZON_TRACKING_ID = "business-book-ranking02-22"


def isbn13_to_asin(isbn13: str) -> str | None:
    """ISBN-13をASIN(ISBN-10)に変換する"""
    # ハイフン除去と文字列化
    src = str(isbn13).replace("-", "")

    # バリデーション（978開始の13桁であること）
    if len(src) != 13 or not src.startswith("978"):
        return None

    # 先頭3桁(978)と末尾1桁(チェックデジット)を除外した9桁を取得
    core = src[3:12]

    # ISBN-10のチェックデジット計算 (モジュラス11 ウェイト10-2)
    total = 0
    for i, digit in enumerate(core):
        total += int(digit) * (10 - i)

    remainder = total % 11
    check_digit = 11 - remainder

    if check_digit == 11:
        cd_str = "0"
    elif check_digit == 10:
        cd_str = "X"
    else:
        cd_str = str(check_digit)

    return core + cd_str


def main():
    print("=== ISBN-13 → ASIN変換 ===")

    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        books = json.load(f)

    updated = 0
    skipped_no_isbn = 0
    skipped_non_978 = 0
    already_has_asin = 0

    for book in books:
        isbn = book.get("isbn")

        if not isbn:
            skipped_no_isbn += 1
            continue

        # 既に /dp/ 形式のURLがある場合、asinフィールドがなければ抽出
        current_url = book.get("amazon_url", "")
        if "/dp/" in current_url:
            if not book.get("asin"):
                import re
                m = re.search(r'/dp/([A-Z0-9]{10})', current_url)
                if m:
                    book["asin"] = m.group(1)
            already_has_asin += 1
            continue

        # ISBN-13 → ASIN変換
        asin = isbn13_to_asin(isbn)

        if not asin:
            skipped_non_978 += 1
            continue

        # amazon_urlを更新
        book["asin"] = asin
        book["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}"
        updated += 1

    # 保存
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"更新: {updated}件")
    print(f"既にASIN有り: {already_has_asin}件")
    print(f"ISBNなし: {skipped_no_isbn}件")
    print(f"非978 ISBN: {skipped_non_978}件")
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
