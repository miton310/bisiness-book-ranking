#!/usr/bin/env python3
"""
タイトルのUnicode正規化で重複書籍をマージするスクリプト

全角/半角の違い（「１％の努力」vs「1%の努力」）で別エントリになっている
紙書籍とKindle版などの重複を統合する。
"""

import json
import shutil
import unicodedata
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
FRONTEND_DATA_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data"
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


def normalize_title(title):
    """タイトルをNFKC正規化して比較用の文字列を返す"""
    return unicodedata.normalize("NFKC", title).strip()


def pick_best(field, group):
    """グループ内で最初に見つかった非空の値を返す"""
    for book in group:
        val = book.get(field)
        if val:
            return val
    return None


def select_primary(group):
    """統合先のprimary書籍を選択"""
    return max(group, key=lambda b: (
        bool(b.get("description")),
        bool(b.get("keywords")),
        b.get("count", 0),
        bool(b.get("image_url")),
        bool(b.get("isbn")),
        bool(b.get("publication_date")),
        bool(b.get("category")),
        len(b.get("videos", [])),
    ))


def merge_books_by_normalized_title(books):
    """NFKC正規化タイトルで書籍をマージ"""
    # 正規化タイトルでグループ化
    title_groups = defaultdict(list)
    for book in books:
        key = normalize_title(book.get("title", ""))
        title_groups[key].append(book)

    merged_books = []
    id_mapping = {}  # old_id -> new_id
    merge_log = []

    for norm_title, group in title_groups.items():
        if len(group) == 1:
            merged_books.append(group[0])
            continue

        # 重複あり: マージ
        primary = select_primary(group)

        # 動画リストをマージ（重複排除）
        all_videos = []
        seen_video_ids = set()
        for book in group:
            for video in book.get("videos", []):
                vid = video.get("video_id")
                if vid and vid not in seen_video_ids:
                    seen_video_ids.add(vid)
                    all_videos.append(video)

        # 統合
        merged = {
            "id": primary["id"],
            "title": primary["title"],
            "author": pick_best("author", group),
            "publisher": pick_best("publisher", group),
            "amazon_url": pick_best("amazon_url", group),
            "amzn_url": pick_best("amzn_url", group),
            "asin": pick_best("asin", group),
            "image_url": pick_best("image_url", group),
            "count": len(all_videos),
            "total_views": sum(v.get("view_count", 0) for v in all_videos),
            "total_likes": sum(v.get("like_count", 0) for v in all_videos),
            "videos": all_videos,
        }

        # オプショナルフィールドを追加（存在する場合のみ）
        for field in ["isbn", "publication_date", "category", "description", "keywords", "openbd_title"]:
            val = pick_best(field, group)
            if val:
                merged[field] = val

        merged_books.append(merged)

        # IDマッピングを記録
        old_ids = []
        for book in group:
            if book["id"] != primary["id"]:
                id_mapping[book["id"]] = primary["id"]
                old_ids.append(book["id"])

        merge_log.append({
            "title": primary["title"],
            "normalized": norm_title,
            "primary_id": primary["id"],
            "merged_ids": old_ids,
            "titles": [b["title"] for b in group],
        })

    return merged_books, id_mapping, merge_log


def update_rankings(rankings, id_mapping, book_map, sort_key="count"):
    """ランキングのIDを更新し、重複を排除してソート"""
    updated = []
    seen_ids = set()

    for entry in rankings:
        book_id = entry.get("id")
        new_id = id_mapping.get(book_id, book_id)

        if new_id in seen_ids:
            continue
        seen_ids.add(new_id)

        book = book_map.get(new_id)
        if book:
            entry_data = {
                "id": new_id,
                "title": book["title"],
                "author": book.get("author"),
                "count": book.get("count", 0),
                "total_views": book.get("total_views", 0),
                "total_likes": book.get("total_likes", 0),
            }
            if book.get("amazon_url"):
                entry_data["amazon_url"] = book["amazon_url"]
            updated.append(entry_data)
        else:
            # book_mapにない場合はそのまま保持
            entry["id"] = new_id
            updated.append(entry)

    # ソート（降順）
    updated.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    return updated


def main():
    print("=== タイトルNFKC正規化による重複マージ ===\n")

    # 読み込み
    books = load_json(BOOKS_FILE)
    print(f"マージ前: {len(books)}件")

    # マージ
    merged_books, id_mapping, merge_log = merge_books_by_normalized_title(books)
    print(f"マージ後: {len(merged_books)}件")
    print(f"統合された組数: {len(merge_log)}組\n")

    if merge_log:
        print("--- 統合された書籍 ---")
        for entry in merge_log:
            print(f"  [{entry['primary_id']}] {entry['title']}")
            for t in entry["titles"]:
                if t != entry["title"]:
                    print(f"    <- {t}")
        print()

    if not id_mapping:
        print("統合対象はありませんでした。")
        return

    # books.json 保存
    save_json(BOOKS_FILE, merged_books)
    print(f"books.json を更新しました")

    # ランキング更新（各ファイルの基準でソート）
    book_map = {b["id"]: b for b in merged_books}
    rankings_config = [
        (RANKINGS_FILE, "count"),
        (RANKINGS_VIEWS_FILE, "total_views"),
        (RANKINGS_LIKES_FILE, "total_likes"),
    ]
    for rankings_file, sort_key in rankings_config:
        if rankings_file.exists():
            rankings = load_json(rankings_file)
            updated = update_rankings(rankings, id_mapping, book_map, sort_key)
            save_json(rankings_file, updated)
            print(f"{rankings_file.name} を更新しました ({len(rankings)} -> {len(updated)}件)")

    # フロントエンドにコピー
    if FRONTEND_DATA_DIR.exists():
        for json_file in DATA_DIR.glob("*.json"):
            shutil.copy2(json_file, FRONTEND_DATA_DIR / json_file.name)
        print(f"\nfrontend/public/data/ にコピーしました")

    print("\n=== 完了 ===")


if __name__ == "__main__":
    main()
