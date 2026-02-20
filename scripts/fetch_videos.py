#!/usr/bin/env python3
"""YouTube Data APIで全動画を取得し、書籍情報を抽出してJSONを生成するスクリプト

使用方法:
  python fetch_videos.py          # 差分更新（前回以降の新しい動画のみ）
  python fetch_videos.py --full   # 全件取得（初回実行時や完全リセット時）
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Amazonリンクから書籍情報取得
from fetch_amazon_info import extract_books_from_amazon_links

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
FETCH_STATE_FILE = os.path.join(DATA_DIR, "fetch_state.json")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    # .envファイルから読み込み
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("YOUTUBE_API_KEY="):
                    YOUTUBE_API_KEY = line.strip().split("=", 1)[1]

AMAZON_ASSOCIATE_TAG = "miton31003-22"
AMAZON_TRACKING_ID = "business-book-ranking02-22"

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


# =============================================================================
# YouTube Data API
# =============================================================================

def api_get(endpoint, params):
    """YouTube Data API にGETリクエスト"""
    params["key"] = YOUTUBE_API_KEY
    url = f"{YOUTUBE_API_BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_uploads_playlist_id(channel_id):
    """チャンネルのアップロード再生リストIDを取得"""
    data = api_get("channels", {
        "part": "contentDetails",
        "id": channel_id,
    })
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_video_ids(playlist_id, since=None):
    """再生リストから動画IDを取得（ページネーション対応）

    Args:
        playlist_id: YouTubeのプレイリストID
        since: この日時以降の動画のみ取得（ISO 8601形式）。Noneなら全件取得。
    """
    video_ids = []
    page_token = None
    stop_fetching = False

    while not stop_fetching:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get("playlistItems", params)

        for item in data.get("items", []):
            published = item["snippet"].get("publishedAt", "")
            vid = item["snippet"]["resourceId"]["videoId"]

            # 差分更新: sinceより古い動画が出たら停止
            if since and published and published <= since:
                stop_fetching = True
                break

            video_ids.append(vid)

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.1)

    return video_ids


def parse_iso8601_duration(duration_str):
    """ISO 8601のduration文字列を秒数に変換（例: PT1M30S → 90）"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str or '')
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def get_video_details(video_ids):
    """動画IDリストから詳細情報を取得（50件ずつバッチ処理）
    60秒以下のショート動画は除外する"""
    videos = []
    shorts_count = 0
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        data = api_get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch),
        })
        for item in data.get("items", []):
            # ショート動画を除外（60秒以下）
            duration_str = item.get("contentDetails", {}).get("duration", "")
            duration_sec = parse_iso8601_duration(duration_str)
            if duration_sec <= 60:
                shorts_count += 1
                continue
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            videos.append({
                "video_id": item["id"],
                "title": snippet["title"],
                "published": snippet["publishedAt"],
                "link": f"https://www.youtube.com/watch?v={item['id']}",
                "summary": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
            })
        time.sleep(0.1)
    if shorts_count > 0:
        print(f"  ショート動画を除外: {shorts_count}件")
    return videos


def fetch_all_channel_videos(channel_id, since=None):
    """チャンネルの動画を取得

    Args:
        channel_id: YouTubeチャンネルID
        since: この日時以降の動画のみ取得。Noneなら全件取得。
    """
    playlist_id = get_uploads_playlist_id(channel_id)
    if not playlist_id:
        print(f"  [ERROR] アップロード再生リストが見つかりません")
        return []
    video_ids = get_all_video_ids(playlist_id, since=since)
    if since:
        print(f"  新規動画ID取得: {len(video_ids)}件 (since: {since[:10]})")
    else:
        print(f"  動画ID取得: {len(video_ids)}件")
    if not video_ids:
        return []
    videos = get_video_details(video_ids)
    print(f"  動画詳細取得: {len(videos)}件")
    return videos


def load_fetch_state():
    """前回の取得状態を読み込む"""
    if os.path.exists(FETCH_STATE_FILE):
        with open(FETCH_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_fetch_state(state):
    """取得状態を保存"""
    with open(FETCH_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# =============================================================================
# 書籍抽出ロジック（Amazonリンクからのみ取得）
# =============================================================================

def extract_book_info_list(summary):
    """概要欄のAmazonリンクから書籍情報を抽出（PA-API使用）

    パターンマッチングによる書籍タイトル抽出は行わず、
    Amazonリンク（amzn.to, amazon.co.jp/dp/）からPA-APIで書籍情報を取得する。
    """
    results = []

    # amzn.to と amazon.co.jp/dp/ の両方を抽出
    amazon_urls = re.findall(
        r'https?://(?:amzn\.to/[A-Za-z0-9]+|(?:www\.)?amazon\.co\.jp/(?:dp|gp/product)/[A-Z0-9]{10})',
        summary
    )

    if not amazon_urls:
        return results

    # PA-APIで書籍情報を取得
    amazon_books = extract_books_from_amazon_links(amazon_urls, max_books=5)

    for book in amazon_books:
        results.append({
            "title": book.get("title"),
            "author": book.get("author"),
            "publisher": book.get("publisher"),
            "asin": book.get("asin"),
            "amazon_url": book.get("amazon_url"),
            "image_url": book.get("image_url"),
        })

    return results


def normalize_title_key(title):
    """表記揺れ統一用の正規化キーを生成"""
    t = title
    t = re.sub(r'[『』「」]', '', t)
    t = re.sub(r'[（(](単行本|文庫|新書|ハードカバー|Kindle版)[）)]', '', t)
    t = re.sub(r'^(改訂版|新版|新装版|増補版|決定版|完全版)\s*', '', t)
    t = re.sub(r'(改訂版です|改訂版)$', '', t)
    t = re.sub(r'[\s　、,：:]+', '', t)
    t = t.lower()
    return t


def merge_similar_books(all_books):
    """短いキーが長いキーの先頭に含まれる場合、同一書籍として統合"""
    keys = sorted(all_books.keys(), key=len)
    merge_map = {}  # short_key -> long_key (統合先)
    for i, short_key in enumerate(keys):
        if short_key in merge_map or len(short_key) < 5:
            continue
        for long_key in keys[i+1:]:
            if long_key in merge_map:
                continue
            if long_key.startswith(short_key):
                merge_map[short_key] = long_key
                break  # 最短の統合先に統合

    for src_key, dst_key in merge_map.items():
        src = all_books.pop(src_key, None)
        if not src or dst_key not in all_books:
            continue
        dst = all_books[dst_key]
        dst["count"] += src["count"]
        dst["total_views"] += src["total_views"]
        dst["total_likes"] += src["total_likes"]
        dst["videos"].extend(src["videos"])
        dst["_title_variants"].extend(src.get("_title_variants", [src["title"]]))
        if not dst.get("author") and src.get("author"):
            dst["author"] = src["author"]
        if not dst.get("publisher") and src.get("publisher"):
            dst["publisher"] = src["publisher"]


def choose_canonical_title(titles):
    """複数の表記揺れタイトルから最も正式なタイトルを選択"""
    cleaned = [re.sub(r'\s*[（(](単行本|文庫|新書|ハードカバー|Kindle版)[）)]', '', t) for t in titles]
    with_subtitle = [t for t in cleaned if '：' in t or ':' in t or '―' in t or '—' in t]
    candidates = with_subtitle if with_subtitle else cleaned
    return max(candidates, key=len)


def generate_amazon_search_url(book_title):
    """書籍タイトルからAmazon検索URLを生成（アソシエイトタグ付き）"""
    query = urllib.parse.quote(book_title)
    return f"https://www.amazon.co.jp/s?k={query}&i=stripbooks&tag={AMAZON_TRACKING_ID}"


def generate_book_id(title):
    """書籍タイトルからユニークIDを生成"""
    return hashlib.md5(title.encode()).hexdigest()[:12]


# =============================================================================
# メイン処理
# =============================================================================

def load_channels():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["channels"]


def main():
    parser = argparse.ArgumentParser(description="YouTube動画から書籍情報を抽出（PA-API使用）")
    parser.add_argument("--full", action="store_true", help="全件取得（差分更新ではなく）")
    parser.add_argument("--channel", type=str, metavar="NAME",
                        help="指定したチャンネルのみ処理（部分一致）")
    parser.add_argument("--list", action="store_true", help="チャンネル一覧を表示")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    channels = load_channels()

    # チャンネル一覧表示
    if args.list:
        print("=== チャンネル一覧 ===")
        for i, ch in enumerate(channels, 1):
            print(f"  {i}. {ch['name']}")
        sys.exit(0)

    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY が設定されていません。.env または環境変数で設定してください。")
        sys.exit(1)

    # チャンネル指定
    if args.channel:
        filtered = [ch for ch in channels if args.channel in ch["name"]]
        if not filtered:
            print(f"ERROR: '{args.channel}' に一致するチャンネルがありません")
            print("--list でチャンネル一覧を確認してください")
            sys.exit(1)
        channels = filtered
        print(f"=== 対象チャンネル: {', '.join(ch['name'] for ch in channels)} ===")

    # 差分更新の状態を読み込み
    fetch_state = load_fetch_state()
    new_fetch_state = dict(fetch_state)  # コピーして保持

    # --full + --channel の場合: 指定チャンネルのみfetch_stateをリセット
    if args.full and args.channel:
        for ch in channels:
            if ch["channel_id"] in new_fetch_state:
                del new_fetch_state[ch["channel_id"]]
    elif args.full:
        new_fetch_state = {}

    # 既存の書籍データを読み込み
    books_file = os.path.join(DATA_DIR, "books.json")
    all_books = {}

    if os.path.exists(books_file):
        with open(books_file, "r", encoding="utf-8") as f:
            existing_books = json.load(f)
        # 正規化キーでマップ化
        for b in existing_books:
            norm_key = normalize_title_key(b["title"])
            b["_title_variants"] = [b["title"]]
            all_books[norm_key] = b
        print(f"既存データ読み込み: {len(all_books)}件")

        # --full + --channel の場合: 指定チャンネルの動画データを削除
        if args.full and args.channel:
            target_channels = {ch["name"] for ch in channels}
            for book in all_books.values():
                book["videos"] = [v for v in book["videos"] if v["channel"] not in target_channels]
                # count/views/likesを再計算
                book["count"] = len(book["videos"])
                book["total_views"] = sum(v.get("view_count", 0) for v in book["videos"])
                book["total_likes"] = sum(v.get("like_count", 0) for v in book["videos"])
            # 動画が0件になった書籍を削除
            all_books = {k: v for k, v in all_books.items() if v["videos"]}
            print(f"対象チャンネルのデータをリセット: 残り{len(all_books)}件")

    if args.full:
        print("=== 全件取得モード ===")
    else:
        print("=== 差分更新モード ===")

    for ch in channels:
        channel_name = ch["name"]
        channel_id = ch["channel_id"]
        print(f"\n=== {channel_name} (ID: {channel_id}) ===")

        # 差分更新: 前回の最新動画日時以降のみ取得
        since = fetch_state.get(channel_id) if not args.full else None
        videos = fetch_all_channel_videos(channel_id, since=since)

        # このチャンネルの最新動画日時を記録
        if videos:
            latest = max(v["published"] for v in videos)
            new_fetch_state[channel_id] = latest
        elif channel_id in fetch_state:
            new_fetch_state[channel_id] = fetch_state[channel_id]

        for video in videos:
            summary = video.get("summary", "")
            book_info_list = extract_book_info_list(summary)

            if not book_info_list:
                continue

            for book_info in book_info_list:
                book_title = book_info.get("title")
                if not book_title:
                    continue

                # PA-APIから取得したamazon_urlを使用
                amazon_url = book_info.get("amazon_url") or generate_amazon_search_url(book_title)

                # 表記揺れ統一: 正規化キーで同一書籍をグループ化
                norm_key = normalize_title_key(book_title)

                if norm_key not in all_books:
                    all_books[norm_key] = {
                        "id": generate_book_id(norm_key),
                        "title": book_title,
                        "_title_variants": [book_title],
                        "author": book_info.get("author"),
                        "publisher": book_info.get("publisher"),
                        "amazon_url": amazon_url,
                        "amzn_url": book_info.get("amzn_url"),
                        "asin": book_info.get("asin"),
                        "image_url": book_info.get("image_url"),
                        "count": 0,
                        "total_views": 0,
                        "total_likes": 0,
                        "videos": [],
                    }
                else:
                    # 新しいバリエーションを記録
                    if book_title not in all_books[norm_key]["_title_variants"]:
                        all_books[norm_key]["_title_variants"].append(book_title)
                    # 著者・出版社が未設定なら補完
                    if not all_books[norm_key]["author"] and book_info.get("author"):
                        all_books[norm_key]["author"] = book_info["author"]
                    if not all_books[norm_key]["publisher"] and book_info.get("publisher"):
                        all_books[norm_key]["publisher"] = book_info["publisher"]
                    # amzn_urlが未設定なら補完
                    if not all_books[norm_key].get("amzn_url") and book_info.get("amzn_url"):
                        all_books[norm_key]["amzn_url"] = book_info["amzn_url"]
                    # PA-APIからのASIN・画像URLが未設定なら補完
                    if not all_books[norm_key].get("asin") and book_info.get("asin"):
                        all_books[norm_key]["asin"] = book_info["asin"]
                    if not all_books[norm_key].get("image_url") and book_info.get("image_url"):
                        all_books[norm_key]["image_url"] = book_info["image_url"]

                all_books[norm_key]["count"] += 1
                all_books[norm_key]["total_views"] += video.get("view_count", 0)
                all_books[norm_key]["total_likes"] += video.get("like_count", 0)
                all_books[norm_key]["videos"].append({
                    "video_id": video["video_id"],
                    "video_title": video["title"],
                    "channel": channel_name,
                    "link": video["link"],
                    "published": video["published"],
                    "view_count": video.get("view_count", 0),
                    "like_count": video.get("like_count", 0),
                })

    # --- 表記揺れ統一 ---
    # 1. 短いキーが長いキーに含まれる場合を統合
    merge_similar_books(all_books)
    # 2. 各グループから正規タイトルを選択
    for book in all_books.values():
        variants = book.pop("_title_variants", [book["title"]])
        if len(variants) > 1:
            canonical = choose_canonical_title(variants)
            book["title"] = canonical
            book["amazon_url"] = generate_amazon_search_url(canonical)

    # --- 結果表示 ---
    books_list = list(all_books.values())
    print(f"\n=== 抽出結果 ===")
    print(f"書籍数: {len(books_list)}")

    # --- 既存データとのマージ（ISBN等を保持） ---
    books_file = os.path.join(DATA_DIR, "books.json")
    if os.path.exists(books_file):
        with open(books_file, "r", encoding="utf-8") as f:
            existing_books = json.load(f)
        # idでマップ化
        existing_map = {b["id"]: b for b in existing_books}
        # タイトル正規化キーでもマップ化（IDが変わった場合に対応）
        existing_by_title = {normalize_title_key(b["title"]): b for b in existing_books}
        # 新データに既存のISBN/ASIN/image_url等をマージ
        for book in books_list:
            # IDでマッチ、またはタイトル正規化キーでマッチ
            existing = existing_map.get(book["id"])
            if not existing:
                norm_key = normalize_title_key(book["title"])
                existing = existing_by_title.get(norm_key)
            if existing:
                for key in ["isbn", "asin", "image_url", "publication_date", "openbd_title", "amzn_url"]:
                    if existing.get(key) and not book.get(key):
                        book[key] = existing[key]
                # amazon_urlはASIN付きのものを優先
                if existing.get("asin") and "/dp/" in existing.get("amazon_url", ""):
                    book["amazon_url"] = existing["amazon_url"]
                    book["asin"] = existing["asin"]

    # --- JSON生成 ---

    # books.json（紹介回数順）
    books_by_count = sorted(books_list, key=lambda x: x["count"], reverse=True)
    with open(books_file, "w", encoding="utf-8") as f:
        json.dump(books_by_count, f, ensure_ascii=False, indent=2)

    # ランキング用の軽量データを生成する関数
    def make_ranking_entry(book):
        return {
            "id": book["id"],
            "title": book["title"],
            "author": book.get("author"),
            "count": book["count"],
            "total_views": book["total_views"],
            "total_likes": book["total_likes"],
            "amazon_url": book["amazon_url"],
        }

    # rankings.json（紹介回数順）
    rankings_count = [make_ranking_entry(b) for b in books_by_count]
    with open(os.path.join(DATA_DIR, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_count, f, ensure_ascii=False, indent=2)

    # rankings_views.json（再生回数合計順）
    books_by_views = sorted(books_list, key=lambda x: x["total_views"], reverse=True)
    rankings_views = [make_ranking_entry(b) for b in books_by_views]
    with open(os.path.join(DATA_DIR, "rankings_views.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_views, f, ensure_ascii=False, indent=2)

    # rankings_likes.json（いいね合計順）
    books_by_likes = sorted(books_list, key=lambda x: x["total_likes"], reverse=True)
    rankings_likes = [make_ranking_entry(b) for b in books_by_likes]
    with open(os.path.join(DATA_DIR, "rankings_likes.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_likes, f, ensure_ascii=False, indent=2)

    print(f"\n--- TOP20（紹介回数順）---")
    for i, book in enumerate(books_by_count[:20], 1):
        print(f"  {i}. 『{book['title']}』 (紹介{book['count']}回 / 再生{book['total_views']:,} / いいね{book['total_likes']:,})")

    print(f"\n--- TOP10（再生回数順）---")
    for i, book in enumerate(books_by_views[:10], 1):
        print(f"  {i}. 『{book['title']}』 (再生{book['total_views']:,} / 紹介{book['count']}回)")

    print(f"\n--- TOP10（いいね順）---")
    for i, book in enumerate(books_by_likes[:10], 1):
        print(f"  {i}. 『{book['title']}』 (いいね{book['total_likes']:,} / 紹介{book['count']}回)")

    # --- 取得状態を保存 ---
    save_fetch_state(new_fetch_state)

    print(f"\nデータを {DATA_DIR} に保存しました。")


if __name__ == "__main__":
    main()
