#!/usr/bin/env python3
"""
ISBNでタイトルを統一するスクリプト

ISBNがある書籍について、openBD API から正式タイトルを取得してタイトルを統一する。

使用方法:
    python scripts/unify_titles_by_isbn.py [--dry-run]
"""

import json
import time
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FRONTEND_DATA_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data"
BOOKS_FILE = DATA_DIR / "books.json"
RANKINGS_FILE = DATA_DIR / "rankings.json"
RANKINGS_VIEWS_FILE = DATA_DIR / "rankings_views.json"
RANKINGS_LIKES_FILE = DATA_DIR / "rankings_likes.json"

OPENBD_API = "https://api.openbd.jp/v1/get"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_openbd(isbn):
    """openBD API でISBNから書籍情報を取得"""
    url = f"{OPENBD_API}?isbn={isbn}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                return data[0]
            return None
    except Exception as e:
        print(f"  [ERROR] openBD API: {e}")
        return None


def get_official_title(openbd_data):
    """openBDデータから正式タイトルを取得"""
    if not openbd_data:
        return None
    
    summary = openbd_data.get("summary", {})
    title = summary.get("title")
    
    # サブタイトルがあれば結合
    # volume = summary.get("volume")
    # if volume:
    #     title = f"{title} {volume}"
    
    return title


def update_rankings(rankings_file, books):
    """ランキングファイルのタイトルを更新"""
    if not rankings_file.exists():
        return
    
    rankings = load_json(rankings_file)
    book_map = {b["id"]: b for b in books}
    
    for entry in rankings:
        book = book_map.get(entry["id"])
        if book:
            entry["title"] = book["title"]
    
    save_json(rankings_file, rankings)


def main():
    import sys
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("=== DRY RUN モード ===\n")
    
    print("=== ISBNでタイトル統一 ===\n")
    
    books = load_json(BOOKS_FILE)
    print(f"総書籍数: {len(books)}")
    
    # ISBNがある書籍を抽出
    with_isbn = [b for b in books if b.get("isbn")]
    print(f"ISBN取得済み: {len(with_isbn)}\n")
    
    updated_count = 0
    
    for i, book in enumerate(with_isbn):
        isbn = book["isbn"]
        old_title = book["title"]
        
        # openBDからタイトル取得
        openbd_data = fetch_openbd(isbn)
        official_title = get_official_title(openbd_data)
        
        if not official_title:
            continue
        
        # タイトルが異なる場合のみ更新
        if old_title != official_title:
            updated_count += 1
            print(f"[{updated_count}] ISBN: {isbn}")
            print(f"  旧: {old_title}")
            print(f"  新: {official_title}")
            print()
            
            if not dry_run:
                book["title"] = official_title
                book["openbd_title"] = official_title
        
        # API制限回避
        if (i + 1) % 10 == 0:
            time.sleep(0.5)
    
    print(f"\n更新対象: {updated_count}件")
    
    if dry_run:
        print("\n=== DRY RUN 完了 ===")
        print("実際に更新するには --dry-run を外して実行してください。")
        return
    
    if updated_count == 0:
        print("更新対象がありませんでした。")
        return
    
    # 保存
    save_json(BOOKS_FILE, books)
    print(f"\n{BOOKS_FILE.name} を更新しました")
    
    # ランキングも更新
    for rankings_file in [RANKINGS_FILE, RANKINGS_VIEWS_FILE, RANKINGS_LIKES_FILE]:
        update_rankings(rankings_file, books)
        print(f"{rankings_file.name} を更新しました")
    
    # フロントエンド用にコピー
    for src, name in [
        (BOOKS_FILE, "books.json"),
        (RANKINGS_FILE, "rankings.json"),
        (RANKINGS_VIEWS_FILE, "rankings_views.json"),
        (RANKINGS_LIKES_FILE, "rankings_likes.json"),
    ]:
        dst = FRONTEND_DATA_DIR / name
        if src.exists():
            save_json(dst, load_json(src))
            print(f"{dst} にコピーしました")
    
    print("\n=== 完了 ===")


if __name__ == "__main__":
    main()
