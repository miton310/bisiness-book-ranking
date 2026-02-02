#!/usr/bin/env python3
"""Amazonリンクから書籍情報を取得するスクリプト"""

import re
import time
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser


# YouTuber自身の著作を除外するための著者名・キーワードリスト
YOUTUBER_AUTHORS = [
    'アバタロー',
    'サラタメ',
    '本要約チャンネル',
    '学識サロン',
    'フェルミ',
    '中田敦彦',
    'オリエンタルラジオ',
    '三宅',  # 三宅書店
]

# YouTuberが自著を宣伝する際のキーワード
SELF_PROMOTION_KEYWORDS = [
    '新刊',
    '拙著',
    '著書',
    '僕の本',
    '私の本',
]


class AmazonTitleParser(HTMLParser):
    """Amazon商品ページからタイトルを抽出"""
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


def resolve_amzn_redirect(short_url, max_redirects=5):
    """amzn.to短縮URLをリダイレクト先に展開してASINを取得"""
    try:
        req = urllib.request.Request(
            short_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )

        # リダイレクトを手動で追跡
        for _ in range(max_redirects):
            try:
                response = urllib.request.urlopen(req, timeout=10)
                final_url = response.geturl()

                # ASINを抽出 (例: https://www.amazon.co.jp/dp/4478109680/ または /gp/product/...)
                asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', final_url)
                if asin_match:
                    return asin_match.group(1)

                return None

            except urllib.error.HTTPError as e:
                if e.code in [301, 302, 303, 307, 308]:
                    # リダイレクト先を取得
                    location = e.headers.get('Location')
                    if location:
                        req = urllib.request.Request(
                            location,
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                    else:
                        return None
                else:
                    return None

    except Exception as e:
        print(f"  [ERROR] リダイレクト解決失敗: {e}")
        return None


def fetch_amazon_title(asin):
    """ASINからAmazon商品ページのタイトルを取得"""
    url = f"https://www.amazon.co.jp/dp/{asin}"

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

            # HTMLパーサーでタイトル抽出
            parser = AmazonTitleParser()
            parser.feed(html)

            if parser.title:
                return parser.title

            # フォールバック: <title>タグから抽出
            title_match = re.search(r'<title>(.+?)</title>', html)
            if title_match:
                title = title_match.group(1)
                # Amazonの余計な部分を削除
                title = re.sub(r'\s*[:|｜]\s*Amazon.*$', '', title)
                title = re.sub(r'\s*\|.*$', '', title)
                return title.strip()

    except Exception as e:
        print(f"  [ERROR] Amazon取得失敗 (ASIN: {asin}): {e}")

    return None


def is_youtuber_book(title, author=None, context=None):
    """YouTuber自身の著作かどうかを判定

    Args:
        title: 書籍タイトル
        author: 著者名（あれば）
        context: 動画説明文などの文脈（自己宣伝キーワード検出用）
    """
    if not title:
        return False

    # タイトルや著者にYouTuber名が含まれているか
    for youtuber in YOUTUBER_AUTHORS:
        if youtuber in title or (author and youtuber in author):
            return True

    # 文脈に自己宣伝キーワードが含まれているか
    if context:
        for keyword in SELF_PROMOTION_KEYWORDS:
            if keyword in context:
                return True

    return False


def extract_books_from_amazon_links(amazon_urls, max_books=10, context=None):
    """Amazonリンクのリストから書籍情報を取得

    Args:
        amazon_urls: Amazonリンクのリスト
        max_books: 取得する最大書籍数
        context: 動画説明文などの文脈（自己宣伝検出用）
    """
    books = []

    for i, url in enumerate(amazon_urls[:max_books]):
        print(f"  [{i+1}/{min(len(amazon_urls), max_books)}] {url}...", end=" ")

        # ASINを取得
        asin = resolve_amzn_redirect(url)
        if not asin:
            print("ASIN取得失敗")
            continue

        # タイトルを取得
        title = fetch_amazon_title(asin)
        if not title:
            print("タイトル取得失敗")
            continue

        # YouTuber自身の本を除外
        if is_youtuber_book(title, context=context):
            print(f"スキップ (YouTuber著作): {title[:40]}")
            continue

        books.append({
            "title": title,
            "asin": asin,
            "amazon_url": f"https://www.amazon.co.jp/dp/{asin}",
        })

        print(f"OK: {title[:40]}")

        # レート制限対策
        time.sleep(1)

    return books


if __name__ == "__main__":
    # テスト
    test_url = "https://amzn.to/3ZqGxQH"  # 適当なテストURL
    print(f"テスト URL: {test_url}")

    asin = resolve_amzn_redirect(test_url)
    if asin:
        print(f"ASIN: {asin}")
        title = fetch_amazon_title(asin)
        if title:
            print(f"タイトル: {title}")
