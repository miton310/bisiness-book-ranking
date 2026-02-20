#!/usr/bin/env python3
"""PA-API (Product Advertising API 5.0) ユーティリティ

Amazonリンクから書籍情報を取得するためのPA-API wrapper。
書籍のみを抽出し、書籍以外の商品を除外する。
"""

import os
import re
import time
import urllib.request
import urllib.error
import warnings
from typing import Optional

# PA-API (python-amazon-paapi)
# DeprecationWarningを抑制
warnings.filterwarnings("ignore", category=DeprecationWarning, module="amazon_paapi")
from amazon_paapi import AmazonApi
from amazon_paapi.models import Country
from amazon_paapi.errors import AmazonError, TooManyRequests


# 書籍として認識するBinding (製本形態)
BOOK_BINDINGS = {
    # 日本語
    '単行本',
    '単行本（ソフトカバー）',
    '文庫',
    '新書',
    'ハードカバー',
    'ペーパーバック',
    'コミック',
    'ムック',
    # Kindle
    'Kindle版',
    'Kindle',
    # 英語
    'Paperback',
    'Hardcover',
    'Mass Market Paperback',
    'Library Binding',
    'Board book',
    'Spiral-bound',
}

# 除外するBinding (書籍以外)
EXCLUDED_BINDINGS = {
    'CD',
    'DVD',
    'Blu-ray',
    'Video Game',
    'Toy',
    'Electronics',
    'Kitchen',
    'Home',
    'Apparel',
    'Shoes',
    'Grocery',
    'Health and Beauty',
    'Sports',
    'Outdoors',
    'Tools & Hardware',
    'Automotive',
    'Software',
    'PC',
    'MP3 ダウンロード',
    'Prime Video',
    'Audible版',  # オーディオブックは除外
    'Audible Logo',
}


class PaapiClient:
    """PA-API クライアント"""

    def __init__(self, access_key: str = None, secret_key: str = None,
                 associate_tag: str = None):
        """
        Args:
            access_key: AWS Access Key (環境変数 AMAZON_ACCESS_KEY からも読み込み)
            secret_key: AWS Secret Key (環境変数 AMAZON_SECRET_KEY からも読み込み)
            associate_tag: アソシエイトタグ (環境変数 AWS_ASSOCIATE_TAG からも読み込み)
        """
        # 認証情報を取得
        self.access_key = access_key or self._get_env('AMAZON_ACCESS_KEY')
        self.secret_key = secret_key or self._get_env('AMAZON_SECRET_KEY')
        self.associate_tag = associate_tag or self._get_env('AWS_ASSOCIATE_TAG', 'business-book-ranking02-22')

        if not self.access_key or not self.secret_key:
            raise ValueError("AMAZON_ACCESS_KEY と AMAZON_SECRET_KEY が必要です")

        # API クライアント初期化 (Japan)
        self.api = AmazonApi(
            key=self.access_key,
            secret=self.secret_key,
            tag=self.associate_tag,
            country=Country.JP,
            throttling=1.0  # 1秒間隔
        )

    def _get_env(self, key: str, default: str = None) -> str:
        """環境変数または.envファイルから値を取得"""
        value = os.environ.get(key)
        if value:
            return value

        # .envファイルから読み込み
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        return line.strip().split("=", 1)[1]

        return default

    def get_items(self, asins: list[str], retry: int = 3) -> dict:
        """ASINのリストから商品情報を取得

        Args:
            asins: ASINのリスト（最大10件）
            retry: リトライ回数

        Returns:
            dict: {asin: item_info} の辞書。取得できなかったASINは含まれない
        """
        if not asins:
            return {}

        # 最大10件に制限
        asins = asins[:10]

        for attempt in range(retry):
            try:
                items = self.api.get_items(asins)

                results = {}
                for item in items:
                    results[item.asin] = self._parse_item(item)

                return results

            except AmazonError as e:
                if "TooManyRequests" in str(e):
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"  [WARN] レート制限。{wait_time}秒待機...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  [ERROR] PA-API: {e}")
                    if attempt == retry - 1:
                        return {}
            except Exception as e:
                print(f"  [ERROR] 予期しないエラー: {e}")
                if attempt == retry - 1:
                    return {}

        return {}

    def _parse_item(self, item) -> dict:
        """PA-APIのItemオブジェクトを解析"""
        result = {
            "asin": item.asin,
            "is_book": False,
            "binding": None,
        }

        # タイトル
        if hasattr(item, 'item_info') and item.item_info:
            if hasattr(item.item_info, 'title') and item.item_info.title:
                result["title"] = item.item_info.title.display_value

            # 著者
            if hasattr(item.item_info, 'by_line_info') and item.item_info.by_line_info:
                by_line = item.item_info.by_line_info
                if hasattr(by_line, 'contributors') and by_line.contributors:
                    authors = []
                    for c in by_line.contributors:
                        if hasattr(c, 'role') and c.role in ("著", "Author", "著者"):
                            if hasattr(c, 'name'):
                                authors.append(c.name)
                    if authors:
                        result["author"] = "、".join(authors)

                # 出版社
                if hasattr(by_line, 'manufacturer') and by_line.manufacturer:
                    if hasattr(by_line.manufacturer, 'display_value'):
                        result["publisher"] = by_line.manufacturer.display_value

            # 製本形態 (Binding)
            if hasattr(item.item_info, 'classifications') and item.item_info.classifications:
                classifications = item.item_info.classifications
                if hasattr(classifications, 'binding') and classifications.binding:
                    if hasattr(classifications.binding, 'display_value'):
                        result["binding"] = classifications.binding.display_value
                        result["is_book"] = self._is_book_binding(result["binding"])

            # 出版日
            if hasattr(item.item_info, 'content_info') and item.item_info.content_info:
                content_info = item.item_info.content_info
                if hasattr(content_info, 'publication_date') and content_info.publication_date:
                    if hasattr(content_info.publication_date, 'display_value'):
                        result["publication_date"] = content_info.publication_date.display_value

        # 画像URL
        if hasattr(item, 'images') and item.images:
            if hasattr(item.images, 'primary') and item.images.primary:
                if hasattr(item.images.primary, 'large') and item.images.primary.large:
                    result["image_url"] = item.images.primary.large.url
                elif hasattr(item.images.primary, 'medium') and item.images.primary.medium:
                    result["image_url"] = item.images.primary.medium.url

        # 商品URL
        result["amazon_url"] = f"https://www.amazon.co.jp/dp/{item.asin}?tag={self.associate_tag}"

        # カテゴリー (BrowseNodeInfo) - 階層パスを取得
        if hasattr(item, 'browse_node_info') and item.browse_node_info:
            if hasattr(item.browse_node_info, 'browse_nodes') and item.browse_node_info.browse_nodes:
                category_path = self._extract_category_path(item.browse_node_info.browse_nodes)
                if category_path:
                    result["category"] = category_path

        return result

    def _extract_category_path(self, browse_nodes) -> Optional[str]:
        """BrowseNodesから有用なカテゴリーパスを抽出

        許可リスト方式で、実際のジャンルカテゴリーのみを取得。
        例: "ビジネス・経済 > 自己啓発"
        """
        # 有効なジャンルカテゴリー（これらを含むパスのみ許可）
        valid_categories = {
            # ビジネス系
            'ビジネス・経済', '経営学・キャリア・MBA', 'マネジメント・人材管理',
            '投資・金融・会社経営', '自己啓発', 'ビジネス実用',
            # 人文系
            '人文・思想', '哲学・思想', '心理学', '倫理学・道徳',
            '宗教', '社会・政治', '社会学', '歴史・地理',
            # 科学系
            '科学・テクノロジー', 'コンピュータ・IT', 'サイエンス',
            # その他
            'ノンフィクション', '趣味・実用', '暮らし・健康・子育て',
            '教育・学参・受験', '語学・辞事典・年鑑', '文学・評論',
            'アート・建築・デザイン', 'スポーツ・アウトドア',
            '医学・薬学', '資格・検定・就職',
        }

        best_category = None

        for node in browse_nodes:
            # ancestorを辿って有効なカテゴリーを探す
            category = self._find_valid_category(node, valid_categories)
            if category:
                # より具体的なカテゴリーを優先
                if best_category is None or len(category) > len(best_category):
                    best_category = category

        return best_category

    def _find_valid_category(self, node, valid_categories: set) -> Optional[str]:
        """ノードから有効なカテゴリーを探す"""
        path = []
        current = node

        while current:
            if hasattr(current, 'display_name') and current.display_name:
                name = current.display_name

                # 有効なカテゴリーかチェック
                if name in valid_categories:
                    path.insert(0, name)

            # 親ノードへ
            if hasattr(current, 'ancestor') and current.ancestor:
                current = current.ancestor
            else:
                break

        if path:
            return ' > '.join(path)
        return None

    def _is_book_binding(self, binding: str) -> bool:
        """製本形態が書籍かどうかを判定"""
        if not binding:
            return False

        # 除外リストをチェック
        for excluded in EXCLUDED_BINDINGS:
            if excluded.lower() in binding.lower():
                return False

        # 書籍リストをチェック
        for book_binding in BOOK_BINDINGS:
            if book_binding.lower() in binding.lower():
                return True

        # デフォルトは書籍でないとする
        return False

    def get_book(self, asin: str) -> Optional[dict]:
        """単一のASINから書籍情報を取得（書籍でない場合はNone）"""
        items = self.get_items([asin])
        if asin not in items:
            return None

        item = items[asin]
        if not item.get("is_book"):
            return None

        return item


def resolve_amzn_redirect(short_url: str, max_redirects: int = 5) -> Optional[str]:
    """amzn.to短縮URLをリダイレクト先に展開してASINを取得"""
    try:
        req = urllib.request.Request(
            short_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )

        for _ in range(max_redirects):
            try:
                response = urllib.request.urlopen(req, timeout=10)
                final_url = response.geturl()

                # ASINを抽出
                asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', final_url)
                if asin_match:
                    return asin_match.group(1)

                return None

            except urllib.error.HTTPError as e:
                if e.code in [301, 302, 303, 307, 308]:
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


def extract_asins_from_text(text: str) -> list[str]:
    """テキストからAmazonリンクのASINを抽出

    対応形式:
    - https://amzn.to/xxxxx (短縮URL)
    - https://www.amazon.co.jp/dp/ASIN
    - https://www.amazon.co.jp/gp/product/ASIN
    - https://amazon.co.jp/dp/ASIN
    """
    asins = []

    # 直接ASINを含むURL
    direct_patterns = [
        r'https?://(?:www\.)?amazon\.co\.jp/(?:dp|gp/product)/([A-Z0-9]{10})',
    ]

    for pattern in direct_patterns:
        matches = re.findall(pattern, text)
        asins.extend(matches)

    # 短縮URL（amzn.to）はリダイレクト解決が必要
    short_urls = re.findall(r'https?://amzn\.to/[A-Za-z0-9]+', text)
    for url in short_urls:
        asin = resolve_amzn_redirect(url)
        if asin:
            asins.append(asin)
        time.sleep(0.5)  # レート制限対策

    # 重複排除（順序維持）
    seen = set()
    unique_asins = []
    for asin in asins:
        if asin not in seen:
            seen.add(asin)
            unique_asins.append(asin)

    return unique_asins


def get_books_from_amazon_links(text: str, max_books: int = 10) -> list[dict]:
    """テキスト内のAmazonリンクから書籍情報を取得

    Args:
        text: 検索対象のテキスト（動画説明文など）
        max_books: 取得する最大書籍数

    Returns:
        書籍情報のリスト（書籍以外は除外済み）
    """
    # ASINを抽出
    asins = extract_asins_from_text(text)
    if not asins:
        return []

    print(f"  Amazon リンク検出: {len(asins)}件")

    # PA-APIで書籍情報を取得
    try:
        client = PaapiClient()
    except ValueError as e:
        print(f"  [ERROR] PA-API 初期化失敗: {e}")
        return []

    books = []

    # 10件ずつバッチ処理
    for i in range(0, len(asins), 10):
        batch = asins[i:i+10]
        items = client.get_items(batch)

        for asin in batch:
            if asin not in items:
                print(f"    ASIN {asin}: 取得失敗")
                continue

            item = items[asin]

            if not item.get("is_book"):
                print(f"    ASIN {asin}: 書籍以外 ({item.get('binding', 'unknown')})")
                continue

            books.append(item)
            print(f"    ASIN {asin}: {item.get('title', 'N/A')[:40]}")

            if len(books) >= max_books:
                break

        if len(books) >= max_books:
            break

    return books


if __name__ == "__main__":
    # テスト
    print("PA-API ユーティリティ テスト")
    print("=" * 50)

    # 認証情報確認
    try:
        client = PaapiClient()
        print(f"認証OK: {client.access_key[:8]}...")
    except ValueError as e:
        print(f"認証エラー: {e}")
        exit(1)

    # テスト: 単一ASIN取得
    test_asin = "4478109680"  # 嫌われる勇気
    print(f"\nASIN {test_asin} のテスト:")
    items = client.get_items([test_asin])
    if test_asin in items:
        item = items[test_asin]
        print(f"  タイトル: {item.get('title')}")
        print(f"  著者: {item.get('author')}")
        print(f"  製本: {item.get('binding')}")
        print(f"  書籍判定: {item.get('is_book')}")
    else:
        print("  取得失敗")

    # テスト: テキストからAmazonリンク抽出
    test_text = """
    今回紹介する本:
    「嫌われる勇気」 https://www.amazon.co.jp/dp/4478109680
    """

    print(f"\nテキストからの抽出テスト:")
    books = get_books_from_amazon_links(test_text, max_books=5)
    print(f"  抽出された書籍: {len(books)}件")
    for book in books:
        print(f"    - {book.get('title')}")
