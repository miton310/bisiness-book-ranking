#!/usr/bin/env python3
"""
ISBNで重複書籍をマージするスクリプト

同一ISBNの書籍エントリを統合し、ランキングデータを合算する。
タイトルはNDL/openBDから取得した正式タイトルに統一。
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
BOOKS_FILE = DATA_DIR / "books.json"
RANKINGS_FILE = DATA_DIR / "rankings.json"
RANKINGS_VIEWS_FILE = DATA_DIR / "rankings_views.json"
RANKINGS_LIKES_FILE = DATA_DIR / "rankings_likes.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_books_by_isbn(books):
    """ISBNで書籍をマージ"""
    # ISBNなしの書籍はそのまま保持
    no_isbn = [b for b in books if not b.get("isbn")]
    with_isbn = [b for b in books if b.get("isbn")]

    # ISBNでグループ化
    isbn_groups = defaultdict(list)
    for book in with_isbn:
        isbn_groups[book["isbn"]].append(book)

    merged_books = []
    id_mapping = {}  # old_id -> new_id

    for isbn, group in isbn_groups.items():
        if len(group) == 1:
            # 重複なし
            merged_books.append(group[0])
            continue

        # 重複あり: マージ
        # 正式タイトルを持つものを優先（openBDタイトルがあれば使用）
        primary = max(group, key=lambda b: (
            b.get("openbd_title") is not None,  # openBDタイトル優先
            b.get("count", 0),  # count多い方を優先
            len(b.get("videos", [])),  # 動画数多い方を優先
        ))

        # 動画リストをマージ（重複排除）
        all_videos = []
        seen_video_ids = set()
        for book in group:
            for video in book.get("videos", []):
                vid = video.get("video_id")
                if vid and vid not in seen_video_ids:
                    seen_video_ids.add(vid)
                    all_videos.append(video)

        # 統計を再計算
        merged = {
            "id": primary["id"],
            "title": primary.get("openbd_title") or primary["title"],
            "author": primary.get("author"),
            "publisher": primary.get("publisher"),
            "isbn": isbn,
            "amazon_url": primary.get("amazon_url"),
            "count": len(all_videos),
            "total_views": sum(v.get("view_count", 0) for v in all_videos),
            "total_likes": sum(v.get("like_count", 0) for v in all_videos),
            "videos": all_videos,
        }

        # openBDタイトルがあれば保持
        if primary.get("openbd_title"):
            merged["openbd_title"] = primary["openbd_title"]

        merged_books.append(merged)

        # IDマッピングを記録
        for book in group:
            if book["id"] != primary["id"]:
                id_mapping[book["id"]] = primary["id"]

    # ISBNなしの書籍を追加
    merged_books.extend(no_isbn)

    return merged_books, id_mapping


def update_rankings(rankings, id_mapping, books):
    """ランキングのIDを更新し、重複を排除"""
    # books から id -> book のマップを作成
    book_map = {b["id"]: b for b in books}

    updated = []
    seen_ids = set()

    for entry in rankings:
        book_id = entry.get("id")
        # IDマッピングがあれば新IDに変換
        new_id = id_mapping.get(book_id, book_id)

        if new_id in seen_ids:
            continue
        seen_ids.add(new_id)

        # 書籍データから最新の値を取得
        book = book_map.get(new_id)
        if book:
            entry_data = {
                "id": new_id,
                "title": book["title"],
                "count": book.get("count", entry.get("count", 0)),
                "total_views": book.get("total_views", entry.get("total_views", 0)),
                "total_likes": book.get("total_likes", entry.get("total_likes", 0)),
            }
            # amazon_url, image_url, author, publisher があれば追加
            if book.get("amazon_url"):
                entry_data["amazon_url"] = book["amazon_url"]
            if book.get("image_url"):
                entry_data["image_url"] = book["image_url"]
            if book.get("author"):
                entry_data["author"] = book["author"]
            if book.get("publisher"):
                entry_data["publisher"] = book["publisher"]
            updated.append(entry_data)

    return updated


def main():
    print("=== ISBN重複マージ ===")

    # 読み込み
    books = load_json(BOOKS_FILE)
    print(f"マージ前: {len(books)}件")

    # ISBNでマージ
    merged_books, id_mapping = merge_books_by_isbn(books)
    print(f"マージ後: {len(merged_books)}件")
    print(f"マージされたエントリ: {len(id_mapping)}件")

    # 保存
    save_json(BOOKS_FILE, merged_books)
    print(f"books.json を更新しました")

    # ランキングも更新
    for rankings_file in [RANKINGS_FILE, RANKINGS_VIEWS_FILE, RANKINGS_LIKES_FILE]:
        if rankings_file.exists():
            rankings = load_json(rankings_file)
            updated = update_rankings(rankings, id_mapping, merged_books)
            save_json(rankings_file, updated)
            print(f"{rankings_file.name} を更新しました ({len(rankings)} -> {len(updated)}件)")

    print("=== 完了 ===")


if __name__ == "__main__":
    main()
