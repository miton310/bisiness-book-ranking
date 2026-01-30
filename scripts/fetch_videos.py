#!/usr/bin/env python3
"""YouTube Data APIで全動画を取得し、書籍情報を抽出してJSONを生成するスクリプト"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    # .envファイルから読み込み
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("YOUTUBE_API_KEY="):
                    YOUTUBE_API_KEY = line.strip().split("=", 1)[1]

AMAZON_ASSOCIATE_TAG = "miton31003"
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


def get_all_video_ids(playlist_id):
    """再生リストから全動画IDを取得（ページネーション対応）"""
    video_ids = []
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get("playlistItems", params)
        for item in data.get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            video_ids.append(vid)
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.1)
    return video_ids


def get_video_details(video_ids):
    """動画IDリストから詳細情報を取得（50件ずつバッチ処理）"""
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        data = api_get("videos", {
            "part": "snippet,statistics",
            "id": ",".join(batch),
        })
        for item in data.get("items", []):
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
    return videos


def fetch_all_channel_videos(channel_id):
    """チャンネルの全動画を取得"""
    playlist_id = get_uploads_playlist_id(channel_id)
    if not playlist_id:
        print(f"  [ERROR] アップロード再生リストが見つかりません")
        return []
    video_ids = get_all_video_ids(playlist_id)
    print(f"  動画ID取得: {len(video_ids)}件")
    videos = get_video_details(video_ids)
    print(f"  動画詳細取得: {len(videos)}件")
    return videos


# =============================================================================
# 書籍抽出ロジック（チャンネル別パターン対応）
# =============================================================================

def extract_book_info_list(summary):
    """概要欄から書籍情報を抽出（複数冊対応）"""
    results = []

    amazon_urls = re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', summary)

    # パターン1: 本要約チャンネル / サラタメさん「タイトル：」「著者：」「出版社：」
    title_match = re.search(r'タイトル[：:](.+)', summary)
    if title_match:
        info = {
            "title": title_match.group(1).strip(),
            "author": None,
            "publisher": None,
        }
        author_match = re.search(r'著者[：:](.+)', summary)
        if author_match:
            info["author"] = author_match.group(1).strip()
        publisher_match = re.search(r'出版社[：:](.+)', summary)
        if publisher_match:
            info["publisher"] = publisher_match.group(1).strip()
        results.append(info)
        return results

    # パターン2: フェルミ漫画大学「参考：書名 著者名 さま」
    ref_match = re.search(r'参考[：:](.+?)(?:\s+さま|\s*$)', summary, re.MULTILINE)
    if ref_match:
        results.append({
            "title": ref_match.group(1).strip(),
            "author": None,
            "publisher": None,
        })
        return results

    # パターン3: 学識サロン「【amazonリンク】\n『書名』著者 / 出版社」
    if "【amazonリンク】" in summary:
        gakushiki_match = re.search(r'『(.+?)』(.+?)(?:\s*/\s*(.+))?$', summary, re.MULTILINE)
        if gakushiki_match:
            info = {
                "title": gakushiki_match.group(1).strip(),
                "author": None,
                "publisher": None,
            }
            if gakushiki_match.group(2):
                info["author"] = gakushiki_match.group(2).strip()
            if gakushiki_match.group(3):
                info["publisher"] = gakushiki_match.group(3).strip()
            results.append(info)
            return results

    # パターン4: アバタロー「書籍の購入」セクション
    abataro_section = re.search(
        r'(?:【書籍の購入】|▼書籍の購入)\s*\n?(.*?)(?=\n▼|\n\n\n|\Z)', summary, re.DOTALL
    )
    if abataro_section:
        section_text = abataro_section.group(1)
        lines = section_text.strip().split('\n')
        seen_titles = set()
        is_first = True
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 非書籍行をスキップ
            if not line or line.startswith('http') or 'エッセンシャル版' in line or '簡易版' in line:
                i += 1
                continue
            # セクションヘッダー・サービス宣伝・ハッシュタグ・絵文字付き動画タイトルをスキップ
            if (line.startswith('【') or line.startswith('#') or
                'Audible' in line or 'Kindle' in line or 'amzn.to' in line or
                line.startswith('📗') or line.startswith('📕') or
                '本を聴く' in line or '関連動画' in line or
                '分解説' in line or 'チャンネル登録' in line or
                'SNS' in line or 'Twitter' in line or 'Instagram' in line):
                i += 1
                continue
            line = re.sub(r'^・\s*', '', line)
            book_match = re.match(r'(.+?)(?:[｜|](.+?))?(?:[（(](.+?)[）)])?$', line)
            if book_match:
                title = book_match.group(1).strip()
                author = book_match.group(2).strip() if book_match.group(2) else None
                publisher = book_match.group(3).strip() if book_match.group(3) else None
                if title not in seen_titles:
                    seen_titles.add(title)
                    results.append({
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "_is_first": is_first,
                    })
                is_first = False
            i += 1
        if results:
            return results

    return results


def generate_amazon_search_url(book_title):
    """書籍タイトルからAmazon検索URLを生成（アソシエイトタグ付き）"""
    query = urllib.parse.quote(book_title)
    return f"https://www.amazon.co.jp/s?k={query}&i=stripbooks&tag={AMAZON_ASSOCIATE_TAG}&linkId={AMAZON_TRACKING_ID}"


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
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY が設定されていません。.env または環境変数で設定してください。")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    channels = load_channels()
    all_books = {}

    for ch in channels:
        channel_name = ch["name"]
        channel_id = ch["channel_id"]
        print(f"\n=== {channel_name} (ID: {channel_id}) ===")

        videos = fetch_all_channel_videos(channel_id)

        for video in videos:
            summary = video.get("summary", "")
            book_info_list = extract_book_info_list(summary)

            if not book_info_list:
                continue

            for book_info in book_info_list:
                book_title = book_info.get("title")
                if not book_title:
                    continue
                # 自著宣伝スキップ
                if book_info.get("_is_first") and len(book_info_list) > 1:
                    continue

                amazon_url = generate_amazon_search_url(book_title)

                if book_title not in all_books:
                    all_books[book_title] = {
                        "id": generate_book_id(book_title),
                        "title": book_title,
                        "author": book_info.get("author"),
                        "publisher": book_info.get("publisher"),
                        "amazon_url": amazon_url,
                        "count": 0,
                        "total_views": 0,
                        "total_likes": 0,
                        "videos": [],
                    }

                all_books[book_title]["count"] += 1
                all_books[book_title]["total_views"] += video.get("view_count", 0)
                all_books[book_title]["total_likes"] += video.get("like_count", 0)
                all_books[book_title]["videos"].append({
                    "video_id": video["video_id"],
                    "video_title": video["title"],
                    "channel": channel_name,
                    "link": video["link"],
                    "published": video["published"],
                    "view_count": video.get("view_count", 0),
                    "like_count": video.get("like_count", 0),
                })

    # --- 結果表示 ---
    books_list = list(all_books.values())
    print(f"\n=== 抽出結果 ===")
    print(f"書籍数: {len(books_list)}")

    # --- JSON生成 ---

    # books.json（紹介回数順）
    books_by_count = sorted(books_list, key=lambda x: x["count"], reverse=True)
    with open(os.path.join(DATA_DIR, "books.json"), "w", encoding="utf-8") as f:
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

    print(f"\nデータを {DATA_DIR} に保存しました。")


if __name__ == "__main__":
    main()
