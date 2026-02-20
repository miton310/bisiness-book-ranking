#!/usr/bin/env python3
"""amzn.toリンクからASINを取得し、書籍判定・情報更新を行うスクリプト

処理フロー:
1. books.json からISBNなしの書籍を抽出
2. 各書籍に保存されたamzn_url、またはYouTube APIで概要欄からamzn.toリンクを取得
3. amzn.to → リダイレクト → ASIN取得
4. ASINがISBN-10形式（数字10桁）→ ISBN-13変換 → openBDで正式書籍情報を取得
5. ASINがB始まり → 非書籍商品として報告/削除

判定ロジック:
- 書籍のASIN = ISBN-10（日本書籍は4始まりの10桁数字）
- 非書籍のASIN = B始まり（Kindle版、家電、日用品等）

使用方法:
  python resolve_amazon_books.py                # amzn_url付きの書籍のみ処理
  python resolve_amazon_books.py --refetch      # YouTube APIで概要欄を再取得して処理
  python resolve_amazon_books.py --delete       # 非書籍を自動削除
  python resolve_amazon_books.py --limit 20     # 最大20件だけ処理（テスト用）
  python resolve_amazon_books.py --force        # ISBN取得済みでも再処理
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
CACHE_FILE = os.path.join(DATA_DIR, "asin_cache.json")
AMAZON_TRACKING_ID = "business-book-ranking02-22"
OPENBD_API = "https://api.openbd.jp/v1/get"

# YouTube API設定
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("YOUTUBE_API_KEY="):
                    YOUTUBE_API_KEY = line.strip().split("=", 1)[1]


# =============================================================================
# キャッシュ管理
# =============================================================================

def load_asin_cache():
    """amzn.to → ASIN 解決結果のキャッシュを読み込み"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_asin_cache(cache):
    """キャッシュを保存"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# =============================================================================
# ASIN / ISBN 判定・変換
# =============================================================================

def is_isbn10(asin):
    """ASINがISBN-10形式（= 書籍）かどうかを判定

    - 書籍のASIN = ISBN-10（10桁、最初の9桁は数字、末尾は数字かX）
    - 非書籍のASIN = B始まり（B0XXXXXXXX）
    """
    if not asin or len(asin) != 10:
        return False
    if asin[0] == 'B':
        return False
    # 最初の9文字が数字、最後が数字かX
    return asin[:9].isdigit() and (asin[9].isdigit() or asin[9] == 'X')


def isbn10_to_isbn13(isbn10):
    """ISBN-10をISBN-13に変換"""
    if not isbn10 or len(isbn10) != 10:
        return None
    core = '978' + isbn10[:9]
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
    check = (10 - total % 10) % 10
    return core + str(check)


# =============================================================================
# amzn.to → ASIN 解決
# =============================================================================

def resolve_amzn_redirect(short_url, max_redirects=5):
    """amzn.to短縮URLをリダイレクト先に展開してASINを取得"""
    try:
        req = urllib.request.Request(
            short_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36'
            }
        )

        for _ in range(max_redirects):
            try:
                response = urllib.request.urlopen(req, timeout=10)
                final_url = response.geturl()
                asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', final_url)
                if asin_match:
                    return asin_match.group(1)
                return None

            except urllib.error.HTTPError as e:
                if e.code in [301, 302, 303, 307, 308]:
                    location = e.headers.get('Location')
                    if location:
                        # リダイレクト先URLからASINを抽出してみる
                        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', location)
                        if asin_match:
                            return asin_match.group(1)
                        req = urllib.request.Request(
                            location,
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                    else:
                        return None
                elif e.code == 503:
                    # Amazon rate limit
                    time.sleep(3)
                    continue
                else:
                    return None

    except Exception as e:
        print(f"    [ERROR] リダイレクト解決失敗 ({short_url}): {e}")
    return None


# =============================================================================
# openBD API
# =============================================================================

def fetch_openbd(isbn):
    """openBD APIでISBNから書籍情報を取得"""
    url = f"{OPENBD_API}?isbn={isbn}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                return data[0]
    except Exception as e:
        print(f"    [ERROR] openBD: {e}")
    return None


# =============================================================================
# NDLサーチ（B始まりASIN＝Kindle版の書籍判定用）
# =============================================================================

def normalize_title_for_search(title):
    """NDL検索用にタイトルを正規化"""
    t = title
    t = t.strip('『』')
    t = re.sub(r'[―—]{1,2}.+$', '', t)
    t = re.sub(r'[:：].+$', '', t)
    t = re.sub(r'^新版\s*', '', t)
    t = re.sub(r'^改訂版\s*', '', t)
    t = re.sub(r'【.*?】', '', t)
    t = re.sub(r'[（(][^）)]*文庫[^）)]*[）)]', '', t)
    # 全角数字を半角に変換
    fullwidth = '０１２３４５６７８９'
    for i, fw in enumerate(fullwidth):
        t = t.replace(fw, str(i))
    # 末尾の巻数を除去（「1」「①」「第1巻」等）
    t = re.sub(r'[\s　]*[①②③④⑤⑥⑦⑧⑨⑩]$', '', t)
    t = re.sub(r'[\s　]*[0-9]+$', '', t)
    t = re.sub(r'[\s　]*第[0-9]+[巻部章編]$', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def search_ndl(title, retry=2):
    """国立国会図書館サーチAPIでタイトルからISBNを検索

    長いタイトルの場合、短縮版でも再検索する"""
    normalized_title = normalize_title_for_search(title)

    # 検索候補: 正規化タイトル → 短縮版（先頭20文字）→ さらに短縮（先頭10文字）
    search_titles = [normalized_title]
    if len(normalized_title) > 20:
        search_titles.append(normalized_title[:20])
    if len(normalized_title) > 10:
        # 「」『』内のテキストだけ抽出して検索
        bracket_match = re.search(r'[「『](.+?)[」』]', title)
        if bracket_match:
            search_titles.append(bracket_match.group(1))

    for search_title in search_titles:
        params = urllib.parse.urlencode({"title": search_title, "cnt": 10})
        url = f"https://ndlsearch.ndl.go.jp/api/opensearch?{params}"

        for attempt in range(retry):
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read().decode("utf-8")
                    isbns = re.findall(
                        r'<dc:identifier xsi:type="dcndl:ISBN">([^<]+)</dc:identifier>', data
                    )
                    for isbn in isbns:
                        cleaned = isbn.replace("-", "")
                        if len(cleaned) == 13:
                            return cleaned
                    for isbn in isbns:
                        cleaned = isbn.replace("-", "")
                        if len(cleaned) == 10:
                            return cleaned
                    break  # ISBNなし → 次の検索候補へ
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(3 * (attempt + 1))
                    continue
                break
        time.sleep(0.3)

    return None


def title_similarity(title1, title2):
    """2つのタイトルの簡易類似度（0.0〜1.0）を計算"""
    if not title1 or not title2:
        return 0.0
    # 正規化: 記号除去、小文字化
    def normalize(t):
        t = re.sub(r'[\s　：:―—\-「」『』（）()\[\]【】]', '', t)
        t = t.lower()
        return t
    n1 = normalize(title1)
    n2 = normalize(title2)
    if not n1 or not n2:
        return 0.0
    # 短い方が長い方に含まれているか
    short, long = (n1, n2) if len(n1) <= len(n2) else (n2, n1)
    if short in long:
        return len(short) / len(long)
    # 共通文字数ベースの簡易類似度
    common = sum(1 for c in short if c in long)
    return common / max(len(n1), len(n2))


def extract_openbd_details(openbd_data):
    """openBDレスポンスから書籍詳細を抽出"""
    if not openbd_data:
        return None
    summary = openbd_data.get("summary", {})
    return {
        "title": summary.get("title"),
        "image_url": summary.get("cover"),
        "author": summary.get("author"),
        "publisher": summary.get("publisher"),
        "publication_date": summary.get("pubdate"),
        "isbn": summary.get("isbn"),
    }


# =============================================================================
# YouTube API（概要欄の再取得）
# =============================================================================

def fetch_video_descriptions(video_ids):
    """YouTube APIで動画の概要欄を一括取得（50件ずつバッチ）"""
    if not YOUTUBE_API_KEY:
        print("WARNING: YOUTUBE_API_KEY未設定。--refetchは使用できません。")
        return {}

    descriptions = {}
    total_batches = (len(video_ids) + 49) // 50

    for batch_idx in range(0, len(video_ids), 50):
        batch = video_ids[batch_idx:batch_idx + 50]
        batch_num = batch_idx // 50 + 1
        print(f"  YouTube API バッチ {batch_num}/{total_batches} ({len(batch)}件)...")

        params = {
            "part": "snippet",
            "id": ",".join(batch),
            "key": YOUTUBE_API_KEY,
        }
        url = f"{YOUTUBE_API_BASE}/videos?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    vid = item["id"]
                    desc = item["snippet"].get("description", "")
                    descriptions[vid] = desc
        except Exception as e:
            print(f"    [ERROR] YouTube API: {e}")

        time.sleep(0.5)

    return descriptions


def find_amzn_urls_in_description(description):
    """概要欄から全amzn.toリンクを抽出"""
    if not description:
        return []
    return re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', description)


def find_amzn_urls_near_title(description, book_title):
    """概要欄の中で書籍タイトル付近のamzn.toリンクを優先的に返す"""
    if not description:
        return []

    lines = description.split('\n')
    amzn_urls = []

    # 書籍タイトルが含まれる行を探す
    title_line_idx = None
    normalized_title = re.sub(r'[\s　]+', '', book_title.lower())
    for i, line in enumerate(lines):
        normalized_line = re.sub(r'[\s　]+', '', line.lower())
        # タイトルの最初の10文字が行に含まれているか
        if len(normalized_title) >= 5 and normalized_title[:min(10, len(normalized_title))] in normalized_line:
            title_line_idx = i
            break

    if title_line_idx is not None:
        # タイトル行の前後5行以内のamzn.toを探す
        for i in range(max(0, title_line_idx - 2), min(len(lines), title_line_idx + 6)):
            urls = re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', lines[i])
            amzn_urls.extend(urls)

    # タイトル付近で見つからない場合、全amzn.toリンクを返す
    if not amzn_urls:
        amzn_urls = find_amzn_urls_in_description(description)

    return amzn_urls[:5]  # 最大5つ


# =============================================================================
# メイン処理
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="amzn.toリンクから書籍情報を解決")
    parser.add_argument("--refetch", action="store_true",
                        help="YouTube APIで概要欄を再取得してamzn.toリンクを探す")
    parser.add_argument("--delete", action="store_true",
                        help="非書籍商品を自動削除")
    parser.add_argument("--limit", type=int, default=0,
                        help="処理する最大書籍数 (0=全件)")
    parser.add_argument("--force", action="store_true",
                        help="ISBN取得済みでも再処理")
    args = parser.parse_args()

    # books.json を読み込み
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        books = json.load(f)

    # ASINキャッシュを読み込み
    asin_cache = load_asin_cache()

    # 処理対象を抽出
    if args.force:
        target_books = books
    else:
        target_books = [b for b in books if not b.get("isbn")]

    print(f"総書籍数: {len(books)} / ISBNなし: {sum(1 for b in books if not b.get('isbn'))}")
    print(f"処理対象: {len(target_books)}件")

    if args.limit:
        target_books = target_books[:args.limit]
        print(f"  → --limit により {args.limit}件に制限")

    # --refetch: YouTube APIで概要欄を再取得
    video_descriptions = {}
    if args.refetch:
        # 対象書籍の全video_idを収集（各書籍の最初の動画のみ）
        video_ids = []
        video_to_book = {}  # video_id → book_id
        for book in target_books:
            if book.get("amzn_url"):
                continue  # amzn_url がある場合はAPIコール不要
            for v in book.get("videos", [])[:1]:
                vid = v["video_id"]
                video_ids.append(vid)
                video_to_book[vid] = book["id"]

        if video_ids:
            print(f"\nYouTube APIで{len(video_ids)}件の概要欄を取得中...")
            video_descriptions = fetch_video_descriptions(video_ids)
            print(f"  取得完了: {len(video_descriptions)}件")
        else:
            print("\n概要欄の再取得が必要な書籍はありません")

    # --- 処理開始 ---
    print(f"\n=== amzn.to → ASIN → 書籍判定 ===")
    updated = 0
    non_books = []
    skipped = 0
    no_amzn = 0
    resolved_count = 0

    for i, book in enumerate(target_books):
        title = book["title"]
        book_id = book["id"]

        print(f"  [{i+1}/{len(target_books)}] {title[:50]}...", end=" ")

        # --- amzn_url を探す ---
        amzn_url = book.get("amzn_url")

        if not amzn_url and args.refetch:
            # 概要欄からamzn.toを探す
            for v in book.get("videos", [])[:1]:
                desc = video_descriptions.get(v["video_id"])
                if desc:
                    urls = find_amzn_urls_near_title(desc, title)
                    if urls:
                        amzn_url = urls[0]
                        book["amzn_url"] = amzn_url  # 今後のために保存
                        break

        if not amzn_url:
            no_amzn += 1
            print("amzn_urlなし → スキップ")
            continue

        # --- キャッシュチェック ---
        cached = amzn_url in asin_cache
        if cached:
            asin = asin_cache[amzn_url]
        else:
            # amzn.to → ASIN解決
            asin = resolve_amzn_redirect(amzn_url)
            asin_cache[amzn_url] = asin  # Noneもキャッシュ（再試行防止）
            resolved_count += 1
            time.sleep(0.8)  # レート制限

        cache_label = "(cache) " if cached else ""

        if not asin:
            print(f"{cache_label}ASIN取得失敗")
            continue

        # --- ISBN-10 判定 ---
        if is_isbn10(asin):
            isbn13 = isbn10_to_isbn13(asin)
            print(f"{cache_label}ASIN:{asin} → ISBN-13:{isbn13}", end=" ")

            # openBDで詳細取得
            openbd_data = fetch_openbd(isbn13)
            details = extract_openbd_details(openbd_data)

            if details and details.get("title"):
                # タイトル類似度チェック（amzn.toリンクが別の本を指している場合を排除）
                sim = title_similarity(title, details["title"])
                if sim < 0.3:
                    print(f"→ タイトル不一致 (類似度{sim:.2f}): "
                          f"『{details['title'][:30]}』 → ASIN/ISBNのみ保存")
                    # リンク先は別の本だが、ISBN/ASINは正確なのでリンク情報として保存
                    book["asin"] = asin
                    book["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}"
                    updated += 1
                else:
                    # 正式な書籍情報で更新
                    old_title = book["title"]
                    book["title"] = details["title"]
                    book["isbn"] = details["isbn"] or isbn13
                    book["asin"] = asin
                    book["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}"
                    if details.get("image_url"):
                        book["image_url"] = details["image_url"]
                    if details.get("author"):
                        book["author"] = details["author"]
                    if details.get("publisher"):
                        book["publisher"] = details["publisher"]
                    if details.get("publication_date"):
                        book["publication_date"] = details["publication_date"]
                    updated += 1
                    print(f"→ 『{details['title'][:30]}』")
                    if old_title != details["title"]:
                        print(f"    (旧タイトル: {old_title[:50]})")
            else:
                # openBDになくてもISBN-10なら書籍の可能性が高い → ISBN情報だけ保存
                book["isbn"] = isbn13
                book["asin"] = asin
                book["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}"
                updated += 1
                print(f"→ openBDになし（ISBN保存のみ）")

            time.sleep(0.3)  # openBDレート制限

        else:
            # B始まり等 → Kindle版 or 非書籍
            # NDLサーチでタイトル検索して書籍かどうか確認
            print(f"{cache_label}ASIN:{asin} (Kindle/非書籍)", end=" ")

            ndl_isbn = search_ndl(title)
            if ndl_isbn:
                # NDLで見つかった → openBDでタイトル照合
                openbd_data = fetch_openbd(ndl_isbn)
                details = extract_openbd_details(openbd_data)

                # openBDのタイトルと元タイトルの類似度をチェック（誤マッチ防止）
                if details and details.get("title"):
                    sim = title_similarity(title, details["title"])
                    if sim < 0.3:
                        # タイトルが大きく異なる → 誤マッチの可能性
                        print(f"→ NDLヒット(ISBN:{ndl_isbn})だがタイトル不一致 "
                              f"(類似度{sim:.2f}): 『{details['title'][:30]}』 → スキップ")
                        time.sleep(0.5)
                        continue

                    # 書籍確定（Kindle版リンク）
                    print(f"→ NDLでISBN発見: {ndl_isbn}", end=" ")
                    old_title = book["title"]
                    book["title"] = details["title"]
                    book["isbn"] = details["isbn"] or ndl_isbn
                    # Kindle ASINではなくISBN-10をASINとして使用
                    phys_asin = None
                    if ndl_isbn and len(ndl_isbn) == 13 and ndl_isbn.startswith("978"):
                        core = ndl_isbn[3:12]
                        total = sum(int(d) * (10 - idx) for idx, d in enumerate(core))
                        remainder = total % 11
                        cd = 11 - remainder
                        cd_str = "0" if cd == 11 else ("X" if cd == 10 else str(cd))
                        phys_asin = core + cd_str

                    if phys_asin:
                        book["asin"] = phys_asin
                        book["amazon_url"] = f"https://www.amazon.co.jp/dp/{phys_asin}?tag={AMAZON_TRACKING_ID}"
                    if details.get("image_url"):
                        book["image_url"] = details["image_url"]
                    if details.get("author"):
                        book["author"] = details["author"]
                    if details.get("publisher"):
                        book["publisher"] = details["publisher"]
                    if details.get("publication_date"):
                        book["publication_date"] = details["publication_date"]
                    updated += 1
                    print(f"→ 『{details['title'][:30]}』")
                    if old_title != details["title"]:
                        print(f"    (旧タイトル: {old_title[:50]})")
                else:
                    # openBDになかったがISBNはある → ISBN保存
                    book["isbn"] = ndl_isbn
                    updated += 1
                    print(f"→ NDLでISBN発見: {ndl_isbn} (openBDになし、ISBN保存のみ)")

                time.sleep(0.5)
            else:
                # NDLでも見つからない → 非書籍の可能性が高い
                non_books.append({
                    "id": book_id,
                    "title": title,
                    "asin": asin,
                    "amzn_url": amzn_url,
                    "count": book.get("count", 0),
                })
                print(f"→ NDLでも見つからず → 非書籍の可能性")
                time.sleep(0.5)

        # 50件ごとにキャッシュ中間保存
        if resolved_count > 0 and resolved_count % 50 == 0:
            save_asin_cache(asin_cache)
            print(f"    --- キャッシュ中間保存 ({resolved_count}件解決済み) ---")

    # --- キャッシュ最終保存 ---
    save_asin_cache(asin_cache)

    # --- 非書籍の報告 ---
    if non_books:
        print(f"\n=== 非書籍の可能性がある商品 ({len(non_books)}件) ===")
        for nb in sorted(non_books, key=lambda x: x["count"], reverse=True):
            print(f"  [{nb['count']}回紹介] {nb['title'][:60]} (ASIN: {nb['asin']})")

        if args.delete:
            delete_ids = {nb["id"] for nb in non_books}
            before = len(books)
            books = [b for b in books if b["id"] not in delete_ids]
            print(f"\n  → {before - len(books)}件を削除しました")

    # --- books.json 保存 ---
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    # --- rankings*.json も再生成 ---
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
            "publisher": b.get("publisher"),
            "publication_date": b.get("publication_date"),
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

    # --- サマリー ---
    print(f"\n=== 完了 ===")
    print(f"処理対象: {len(target_books)}件")
    print(f"  更新: {updated}件")
    print(f"  非書籍: {len(non_books)}件")
    print(f"  amzn_urlなし: {no_amzn}件")
    print(f"  ASIN新規解決: {resolved_count}件")


if __name__ == "__main__":
    main()
