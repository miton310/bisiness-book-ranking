#!/usr/bin/env python3
"""Amazonリンクから書籍情報を取得するスクリプト

PA-APIを使用して書籍情報を取得し、書籍以外の商品を除外する。
"""

import re
import time
import urllib.request

# PA-API ユーティリティ
from paapi_utils import (
    PaapiClient,
    resolve_amzn_redirect,
)


# YouTuber自身の著作を除外するための著者名・キーワードリスト
YOUTUBER_AUTHORS = [
    'アバタロー',
    'サラタメ',
    '本要約チャンネル',
    '学識サロン',
    'フェルミ',
    '中田敦彦',
    'オリエンタルラジオ',
]

def is_youtuber_book(title: str, author: str = None) -> bool:
    """YouTuber自身の著作かどうかを判定

    PA-APIから取得した著者名にYouTuber名が含まれていたら除外。
    """
    if not title:
        return False

    # タイトルや著者にYouTuber名が含まれているか
    for youtuber in YOUTUBER_AUTHORS:
        if youtuber in title or (author and youtuber in author):
            return True

    return False


def extract_books_from_amazon_links(amazon_urls: list[str], max_books: int = 10) -> list[dict]:
    """Amazonリンクのリストから書籍情報を取得（PA-API使用）

    Args:
        amazon_urls: Amazonリンクのリスト
        max_books: 取得する最大書籍数

    Returns:
        書籍情報のリスト
    """
    if not amazon_urls:
        return []

    # ASINを取得
    asins = []
    for url in amazon_urls[:max_books * 2]:  # 余裕を持って取得
        # 直接ASINを含むURL
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
        if asin_match:
            asins.append(asin_match.group(1))
        # 短縮URL
        elif 'amzn.to' in url:
            print(f"  短縮URL解決中: {url}...", end=" ")
            asin = resolve_amzn_redirect(url)
            if asin:
                print(f"ASIN: {asin}")
                asins.append(asin)
            else:
                print("失敗")
            time.sleep(0.5)

    if not asins:
        return []

    # 重複排除
    asins = list(dict.fromkeys(asins))

    # PA-APIで書籍情報を取得
    try:
        client = PaapiClient()
    except ValueError as e:
        print(f"  [ERROR] PA-API 初期化失敗: {e}")
        # フォールバック: 従来の方式（Webスクレイピング）
        return _extract_books_fallback(asins)

    books = []

    # 10件ずつバッチ処理
    for i in range(0, len(asins), 10):
        batch = asins[i:i+10]
        print(f"  PA-API取得中: {len(batch)}件...")

        items = client.get_items(batch)

        for asin in batch:
            if asin not in items:
                continue

            item = items[asin]

            # 書籍以外は除外
            if not item.get("is_book"):
                print(f"    スキップ (書籍以外): {item.get('binding', 'unknown')}")
                continue

            title = item.get("title")
            author = item.get("author")

            # YouTuber自身の本を除外
            if is_youtuber_book(title, author):
                print(f"    スキップ (YouTuber著作): {title[:40]}")
                continue

            books.append({
                "title": title,
                "asin": asin,
                "author": author,
                "publisher": item.get("publisher"),
                "image_url": item.get("image_url"),
                "publication_date": item.get("publication_date"),
                "amazon_url": item.get("amazon_url"),
            })

            print(f"    OK: {title[:50]}")

            if len(books) >= max_books:
                break

        if len(books) >= max_books:
            break

    return books


def _extract_books_fallback(asins: list[str]) -> list[dict]:
    """PA-APIが使えない場合のフォールバック（Webスクレイピング）

    注意: この方法は不安定で、Amazonの利用規約違反の可能性がある。
    """
    from html.parser import HTMLParser

    class AmazonTitleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.title = None
            self.in_title = False

        def handle_starttag(self, tag, attrs):
            if tag == 'span' and ('id', 'productTitle') in attrs:
                self.in_title = True

        def handle_data(self, data):
            if self.in_title and data.strip():
                self.title = data.strip()

        def handle_endtag(self, tag):
            if tag == 'span' and self.in_title:
                self.in_title = False

    books = []
    print("  [WARN] PA-API使用不可。Webスクレイピングにフォールバック...")

    for asin in asins:
        url = f"https://www.amazon.co.jp/dp/{asin}"

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')

                parser = AmazonTitleParser()
                parser.feed(html)

                title = parser.title
                if not title:
                    title_match = re.search(r'<title>(.+?)</title>', html)
                    if title_match:
                        title = title_match.group(1)
                        title = re.sub(r'\s*[:|｜]\s*Amazon.*$', '', title)
                        title = re.sub(r'\s*\|.*$', '', title)
                        title = title.strip()

                if title:
                    if not is_youtuber_book(title):
                        books.append({
                            "title": title,
                            "asin": asin,
                            "amazon_url": f"https://www.amazon.co.jp/dp/{asin}",
                        })

        except Exception as e:
            print(f"  [ERROR] ASIN {asin}: {e}")

        time.sleep(1)

    return books


if __name__ == "__main__":
    # テスト
    print("Amazonリンク書籍抽出テスト")
    print("=" * 50)

    test_urls = [
        "https://amzn.to/3ZqGxQH",  # 嫌われる勇気
        "https://www.amazon.co.jp/dp/4478109680",
    ]

    print(f"\nテストURL: {test_urls}")
    books = extract_books_from_amazon_links(test_urls, max_books=5)

    print(f"\n結果: {len(books)}件")
    for book in books:
        print(f"  - {book.get('title')}")
        print(f"    著者: {book.get('author')}")
        print(f"    ASIN: {book.get('asin')}")
