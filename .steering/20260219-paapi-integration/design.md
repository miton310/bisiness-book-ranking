# PA-API統合 - 設計書

## 実装アプローチ

### アーキテクチャ変更

```
[従来]
概要欄テキスト → パターンマッチング → 書籍タイトル抽出 → NDL/openBD検索

[新方式]
概要欄テキスト → Amazonリンク抽出 → PA-API → 書籍情報取得（書籍以外は自動除外）
```

### 処理フロー

```
1. YouTube APIで動画取得
2. 概要欄からAmazonリンク抽出
   - amzn.to/xxxxx（短縮URL）
   - amazon.co.jp/dp/ASIN
   - amazon.co.jp/gp/product/ASIN
3. amzn.toはリダイレクト解決してASIN取得
4. PA-API GetItemsでASINから商品情報取得（10件ずつバッチ処理）
5. Bindingで書籍判定
   - 書籍: 単行本, 文庫, 新書, Kindle版, etc.
   - 除外: CD, DVD, Audible版, etc.
6. 書籍情報をJSONに保存
```

## 変更するコンポーネント

### 新規作成

| ファイル | 説明 |
|---------|------|
| `scripts/paapi_utils.py` | PA-APIユーティリティモジュール |

#### paapi_utils.py の主要機能

- `PaapiClient` クラス: PA-APIクライアント
  - `get_items(asins)`: ASINリストから商品情報取得
  - `_is_book_binding(binding)`: 書籍判定
- `resolve_amzn_redirect(url)`: 短縮URL → ASIN変換
- `extract_asins_from_text(text)`: テキストからASIN抽出

### 変更

| ファイル | 変更内容 |
|---------|---------|
| `scripts/fetch_videos.py` | パターンマッチング削除、PA-API連携 |
| `scripts/fetch_amazon_info.py` | PA-API使用に書き換え |

#### fetch_videos.py の変更点

1. `extract_book_info_list()` を大幅簡略化
   - パターンマッチング（パターン1〜7）を全て削除
   - Amazonリンク抽出 → PA-API呼び出しのみ
2. ヘルパー関数削除
   - `clean_book_title()` 削除（PA-APIから取得するデータは既にクリーン）
   - `is_valid_book_title()` 削除（PA-APIのBinding判定で代替）
3. コマンドラインオプション追加
   - `--channel NAME`: 指定チャンネルのみ処理
   - `--list`: チャンネル一覧表示

### 削除

| 項目 | 理由 |
|-----|------|
| パターンマッチングコード（約400行） | PA-APIで代替 |
| NGワードリスト（約300件） | Binding判定で代替 |
| `clean_book_title()` | 不要 |
| `is_valid_book_title()` | 不要 |

## データ構造

### PA-APIから取得する情報

```python
{
    "asin": "4478109680",
    "title": "嫌われる勇気",
    "author": "岸見一郎、古賀史健",
    "publisher": "ダイヤモンド社",
    "binding": "単行本（ソフトカバー）",
    "is_book": True,
    "image_url": "https://m.media-amazon.com/images/I/...",
    "publication_date": "2013/12/13",
    "amazon_url": "https://www.amazon.co.jp/dp/4478109680?tag=business-book-ranking02-22"
}
```

### 書籍判定ルール

#### 書籍として認識するBinding

- 単行本, 単行本（ソフトカバー）, 文庫, 新書, ハードカバー
- ペーパーバック, コミック, ムック
- Kindle版, Kindle
- Paperback, Hardcover, Mass Market Paperback

#### 除外するBinding

- CD, DVD, Blu-ray, Video Game
- Electronics, Kitchen, Home, Apparel
- Audible版, MP3 ダウンロード, Prime Video

## 影響範囲

### 影響を受けるファイル

- `scripts/fetch_videos.py` - 大幅変更
- `scripts/fetch_amazon_info.py` - PA-API対応
- `scripts/paapi_utils.py` - 新規作成

### 影響を受けないファイル

- `scripts/fetch_amazon.py` - NDL/openBD検索は維持（ISBN取得用）
- `data/*.json` - フォーマット変更なし
- `frontend/*` - 変更なし

## 依存パッケージ

```
python-amazon-paapi==6.1.0
```

インストール:
```bash
pip3 install --break-system-packages python-amazon-paapi
```

## 認証情報

`.env` に追加:
```
AMAZON_ACCESS_KEY=AKIA...
AMAZON_SECRET_KEY=...
```

アソシエイトタグ: `business-book-ranking02-22`（既存）
