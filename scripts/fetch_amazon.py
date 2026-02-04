#!/usr/bin/env python3
"""openBD + Google Books API で書籍情報（画像・著者・出版社・出版日）を取得するスクリプト"""

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
CSV_FILE = os.path.join(DATA_DIR, "books_no_isbn_edit.csv")

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
OPENBD_API = "https://api.openbd.jp/v1/get"

AMAZON_ASSOCIATE_TAG = "miton31003"
AMAZON_TRACKING_ID = "business-book-ranking02-22"


def isbn13_to_asin(isbn13: str) -> str | None:
    """ISBN-13をASIN(ISBN-10)に変換する"""
    src = str(isbn13).replace("-", "")
    if len(src) != 13 or not src.startswith("978"):
        return None
    core = src[3:12]
    total = sum(int(d) * (10 - i) for i, d in enumerate(core))
    remainder = total % 11
    check_digit = 11 - remainder
    if check_digit == 11:
        cd_str = "0"
    elif check_digit == 10:
        cd_str = "X"
    else:
        cd_str = str(check_digit)
    return core + cd_str

# Google Books APIキーを取得（.envから）
# 環境変数で明示的に空文字が設定された場合はGoogle Books APIを無効化
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")
if GOOGLE_BOOKS_API_KEY is None:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_BOOKS_API_KEY="):
                    GOOGLE_BOOKS_API_KEY = line.strip().split("=", 1)[1]
    if not GOOGLE_BOOKS_API_KEY:
        GOOGLE_BOOKS_API_KEY = ""


def fetch_openbd(isbn):
    """openBD API でISBNから書籍情報を取得"""
    url = f"{OPENBD_API}?isbn={isbn}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # openBDは配列を返す。存在しない場合は[null]
            if data and data[0]:
                return data[0]
            return None
    except Exception as e:
        print(f"  [ERROR] openBD API: {e}")
        return None


def search_google_books(title, retry=3):
    """Google Books API でタイトル検索（リトライ機能付き）"""
    params = {
        "q": f"intitle:{title}",
        "langRestrict": "ja",
        "maxResults": 1,
        "printType": "books",
    }

    # APIキーがあれば追加（レート制限緩和）
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    url = f"{GOOGLE_BOOKS_API}?{urllib.parse.urlencode(params)}"

    for attempt in range(retry):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # レート制限
                if attempt < retry - 1:
                    wait_time = 10 * (attempt + 1)  # 10秒、20秒、30秒と増やす
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  [ERROR] Google Books API {e.code}")
                    return None
            else:
                print(f"  [ERROR] Google Books API {e.code}")
                return None
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    return None


def extract_openbd_details(openbd_data):
    """openBD API レスポンスから書籍情報を抽出"""
    if not openbd_data:
        return None

    summary = openbd_data.get("summary", {})
    onix = openbd_data.get("onix", {})

    # タイトル（正式タイトル）
    title = summary.get("title")

    # 画像URL
    image_url = summary.get("cover")

    # 著者
    authors = None
    author_str = summary.get("author")
    if author_str:
        authors = [author_str]

    # 出版社
    publisher = summary.get("publisher")

    # 出版日
    pub_date = summary.get("pubdate")

    # ISBN
    isbn = summary.get("isbn")

    return {
        "title": title,
        "image_url": image_url,
        "authors": authors,
        "publisher": publisher,
        "publication_date": pub_date,
        "isbn": isbn,
    }


def extract_google_books_details(result):
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
    return f"https://www.amazon.co.jp/s?k={query}&i=stripbooks&tag={AMAZON_TRACKING_ID}"


def normalize_title_for_search(title: str) -> str:
    """NDL検索用にタイトルを正規化"""
    import re
    t = title

    # 『』を除去
    t = t.strip('『』')

    # サブタイトルを除去（――  ―  —  :  ： 以降）
    t = re.sub(r'[―—]{1,2}.+$', '', t)
    t = re.sub(r'[:：].+$', '', t)

    # 版表記・形態プレフィックスを除去
    t = re.sub(r'^新版\s*', '', t)
    t = re.sub(r'^改訂版\s*', '', t)
    t = re.sub(r'^新書[：:]\s*', '', t)
    t = re.sub(r'^文庫[：:]\s*', '', t)
    t = re.sub(r'\[第.版\]', '', t)
    t = re.sub(r'【.*?】', '', t)

    # 余計な注釈を除去
    t = re.sub(r'[（(][^）)]*文庫[^）)]*[）)]', '', t)
    t = re.sub(r'[（(]ソフトカバー[）)]', '', t)
    t = re.sub(r'\s*–\s*\d{4}/\d{1,2}/\d{1,2}', '', t)

    # 連続スペースを整理
    t = re.sub(r'\s+', ' ', t).strip()

    return t


def search_ndl(title, retry=3):
    """国立国会図書館サーチAPIでタイトルからISBNを検索"""
    import re as _re

    # タイトルを正規化して検索
    normalized_title = normalize_title_for_search(title)
    params = urllib.parse.urlencode({"title": normalized_title, "cnt": 3})
    url = f"https://ndlsearch.ndl.go.jp/api/opensearch?{params}"

    for attempt in range(retry):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode("utf-8")
                isbns = _re.findall(
                    r'<dc:identifier xsi:type="dcndl:ISBN">([^<]+)</dc:identifier>', data
                )
                # ISBN-13を優先
                for isbn in isbns:
                    cleaned = isbn.replace("-", "")
                    if len(cleaned) == 13:
                        return cleaned
                # ISBN-10でもOK
                for isbn in isbns:
                    cleaned = isbn.replace("-", "")
                    if len(cleaned) == 10:
                        return cleaned
                return None
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(3 * (attempt + 1))
                continue
            print(f"  [ERROR] NDL API: {e}")
            return None

    return None


def load_csv_overrides():
    """books_no_isbn_edit.csv から search_title, delete, isbn を読み込む"""
    overrides = {}  # id -> {"search_title": ..., "delete": bool, "isbn": ...}
    if not os.path.exists(CSV_FILE):
        return overrides

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book_id = row.get("id", "").strip()
            if not book_id:
                continue
            search_title = row.get("search_title", "").strip()
            delete_flag = row.get("delete", "").strip() == "1"
            manual_isbn = row.get("isbn", "").strip().replace("-", "")
            overrides[book_id] = {
                "search_title": search_title,
                "delete": delete_flag,
                "isbn": manual_isbn,
            }
    return overrides


def main():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        books = json.load(f)

    # CSVから検索タイトルと削除フラグを読み込む
    csv_overrides = load_csv_overrides()

    # delete=1 のものを削除
    delete_ids = {bid for bid, info in csv_overrides.items() if info["delete"]}
    if delete_ids:
        before_count = len(books)
        books = [b for b in books if b["id"] not in delete_ids]
        print(f"CSVのdelete=1により {before_count - len(books)}件を削除")
        # 削除後すぐに保存
        with open(BOOKS_FILE, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"書籍数: {len(books)}")
    updated = 0
    errors = 0

    skipped = 0
    for i, book in enumerate(books):
        # 既にISBN取得済みならスキップ
        if book.get("isbn"):
            skipped += 1
            continue

        # CSVのsearch_titleがあればそれを使う
        book_id = book["id"]
        override = csv_overrides.get(book_id, {})
        search_title = override.get("search_title") or book["title"]

        print(f"  [{i+1}/{len(books)}] {book['title'][:40]}...", end=" ")

        details = None
        isbn = None

        # 0. CSVに手動入力されたISBNがあればそれを使う
        manual_isbn = override.get("isbn")
        if manual_isbn:
            isbn = manual_isbn
            print(f"(手動ISBN: {isbn})", end=" ")
        else:
            if override.get("search_title"):
                print(f"(検索: {search_title[:20]})", end=" ")
            # 1. NDLサーチでISBNを取得
            isbn = search_ndl(search_title)

        # 2. ISBNが取れたらopenBDで詳細取得
        if isbn:
            openbd_data = fetch_openbd(isbn)
            openbd_details = extract_openbd_details(openbd_data)
            if openbd_details:
                details = openbd_details
                print(f"OK (NDL→openBD, ISBN:{isbn})", end="")

        # 3. openBDで取れなかったらGoogle Books APIにフォールバック
        # ※Google Books APIのクォータが切れている場合はスキップ
        if not details and GOOGLE_BOOKS_API_KEY:
            google_result = search_google_books(search_title, retry=1)
            google_details = extract_google_books_details(google_result)
            if google_details:
                # Google BooksでISBNが取れたらopenBDも試す
                g_isbn = google_details.get("isbn")
                if g_isbn and not isbn:
                    openbd_data = fetch_openbd(g_isbn)
                    openbd_details = extract_openbd_details(openbd_data)
                    if openbd_details:
                        details = {
                            "image_url": openbd_details.get("image_url") or google_details.get("image_url"),
                            "authors": openbd_details.get("authors") or google_details.get("authors"),
                            "publisher": openbd_details.get("publisher") or google_details.get("publisher"),
                            "publication_date": openbd_details.get("publication_date") or google_details.get("publication_date"),
                            "isbn": openbd_details.get("isbn") or g_isbn,
                        }
                        print(f"OK (Google→openBD)", end="")
                if not details:
                    details = google_details
                    print("OK (Google Books)", end="")

        if details:
            # openBDの正式タイトルで統一
            if details.get("title"):
                book["title"] = details["title"]
            if details.get("image_url"):
                book["image_url"] = details["image_url"]
            if details.get("authors"):
                book["author"] = "、".join(details["authors"])
            if details.get("publisher"):
                book["publisher"] = details["publisher"]
            if details.get("publication_date"):
                book["publication_date"] = details["publication_date"]
            if details.get("isbn"):
                book["isbn"] = details["isbn"]
                # ISBN-13 → ASIN(ISBN-10)に変換して商品ページURLに
                asin = isbn13_to_asin(details["isbn"])
                if asin:
                    book["asin"] = asin
                    book["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}"
            updated += 1
            print()
        else:
            errors += 1
            print(" NOT FOUND")

        # NDL + openBD はレート制限が緩いので短めでOK
        time.sleep(1)

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
    print(f"更新: {updated}件 / エラー: {errors}件 / スキップ: {skipped}件 / 合計: {len(books)}件")


if __name__ == "__main__":
    main()
