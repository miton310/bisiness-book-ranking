#!/usr/bin/env python3
"""Google Books API で書籍情報（画像・著者・出版社・出版日）を取得するスクリプト"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

AMAZON_ASSOCIATE_TAG = "miton31003"
AMAZON_TRACKING_ID = "business-book-ranking02-22"


def search_google_books(title):
    """Google Books API でタイトル検索"""
    params = urllib.parse.urlencode({
        "q": f"intitle:{title}",
        "langRestrict": "ja",
        "maxResults": 1,
        "printType": "books",
    })
    url = f"{GOOGLE_BOOKS_API}?{params}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [ERROR] Google Books API {e.code}")
        return None


def extract_details(result):
    """Google Books API レスポンスから書籍情報を抽出"""
    if not result or result.get("totalItems", 0) == 0:
        return None

    items = result.get("items", [])
    if not items:
        return None

    volume = items[0].get("volumeInfo", {})

    # 画像URL (httpをhttpsに変換、zoom=1をzoom=3に変更して高解像度取得)
    image_url = None
    image_links = volume.get("imageLinks", {})
    for key in ("thumbnail", "smallThumbnail"):
        if key in image_links:
            image_url = image_links[key].replace("http://", "https://")
            image_url = image_url.replace("zoom=1", "zoom=3")
            break

    # 著者
    authors = volume.get("authors")

    # 出版社
    publisher = volume.get("publisher")

    # 出版日
    pub_date = volume.get("publishedDate")

    # ISBN
    isbn = None
    identifiers = volume.get("industryIdentifiers", [])
    for ident in identifiers:
        if ident.get("type") == "ISBN_13":
            isbn = ident.get("identifier")
            break
    if not isbn:
        for ident in identifiers:
            if ident.get("type") == "ISBN_10":
                isbn = ident.get("identifier")
                break

    return {
        "image_url": image_url,
        "authors": authors,
        "publisher": publisher,
        "publication_date": pub_date,
        "isbn": isbn,
    }


def generate_amazon_search_url(book_title):
    """書籍タイトルからAmazon検索URLを生成（アソシエイトタグ付き）"""
    query = urllib.parse.quote(book_title)
    return f"https://www.amazon.co.jp/s?k={query}&i=stripbooks&tag={AMAZON_ASSOCIATE_TAG}&linkId={AMAZON_TRACKING_ID}"


def main():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"書籍数: {len(books)}")
    updated = 0
    errors = 0

    for i, book in enumerate(books):
        # 既に画像取得済みならスキップ
        if book.get("image_url"):
            continue

        title = book["title"]
        print(f"  [{i+1}/{len(books)}] {title[:40]}...", end=" ")

        result = search_google_books(title)
        details = extract_details(result)

        if details:
            if details["image_url"]:
                book["image_url"] = details["image_url"]
            if details["authors"]:
                book["author"] = "、".join(details["authors"])
            if details["publisher"]:
                book["publisher"] = details["publisher"]
            if details["publication_date"]:
                book["publication_date"] = details["publication_date"]
            if details["isbn"]:
                book["isbn"] = details["isbn"]
            updated += 1
            print("OK")
        else:
            errors += 1
            print("NOT FOUND")

        # レート制限対策
        time.sleep(0.5)

        # 100件ごとに中間保存
        if updated > 0 and updated % 100 == 0:
            with open(BOOKS_FILE, "w", encoding="utf-8") as f:
                json.dump(books, f, ensure_ascii=False, indent=2)
            print(f"  --- 中間保存 ({updated}件更新済み) ---")

    # 最終保存
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    # rankings*.json も再生成（image_url を含める）
    def make_ranking_entry(b):
        return {
            "id": b["id"],
            "title": b["title"],
            "author": b.get("author"),
            "count": b["count"],
            "total_views": b["total_views"],
            "total_likes": b["total_likes"],
            "amazon_url": b["amazon_url"],
            "image_url": b.get("image_url"),
        }

    by_count = sorted(books, key=lambda x: x["count"], reverse=True)
    with open(os.path.join(DATA_DIR, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump([make_ranking_entry(b) for b in by_count], f, ensure_ascii=False, indent=2)

    by_views = sorted(books, key=lambda x: x["total_views"], reverse=True)
    with open(os.path.join(DATA_DIR, "rankings_views.json"), "w", encoding="utf-8") as f:
        json.dump([make_ranking_entry(b) for b in by_views], f, ensure_ascii=False, indent=2)

    by_likes = sorted(books, key=lambda x: x["total_likes"], reverse=True)
    with open(os.path.join(DATA_DIR, "rankings_likes.json"), "w", encoding="utf-8") as f:
        json.dump([make_ranking_entry(b) for b in by_likes], f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"更新: {updated}件 / エラー: {errors}件 / 合計: {len(books)}件")


if __name__ == "__main__":
    main()
