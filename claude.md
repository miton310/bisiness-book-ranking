# ビジネス書ランキングサイト プロジェクト概要

## コンセプト

本要約系YouTuberが紹介した書籍を集計し、紹介回数でランキング化するサイト。

## 方針: 完全無料運営

バックエンド・DB不要。Python → JSON生成 → 静的サイトとして配信。

### ドキュメントの分類

#### 1. 永続的ドキュメント（`/docs`）

アプリケーション全体の「**何をやるか**」「どう作るか」を定義する恒久的なドキュメント。
アプリケーションの基本設計や方針が変わらない限り更新されません。

- **product-requirements.md** - プロダクト要求定義書
	- プロダクトビジョンと目的
	- 主要な機能一覧
	- 成功の定義
	- ビジネス要件
	- ユーザーストーリー
	- 受け入れ条件
	- 機能要件
	- 非機能要件

- **functional-design.md** - 機能設計書
	- 機能ごとのアーキテクチャ
	- システム構成図
	- データモデル定義（ER図含む）
	- コンポーネント設計
	- ユースケース図、画面遷移図、ワイヤーフレーム
	- API設計（将来的にバックエンドと連携する場合）

- **architecture.md** - 技術仕様書
	- テクノロジースタック
	- 開発ツールと手法
	- 技術製薬と要件
	- パフォーマンス要件

- **repository-structure.md** - リポジトリ構造定義書
	- フォルダ・ファイル構成
	- ディレクトリの役割
	- ファイル配置ルール

- **development-guidelines.md** - 開発ガイドライン
	- コーディング規約
	- 命名規則
	- スタイリング規約
	- テスト規約
	- Git規約

- **glossary.md** - ユビキタス言語定義
	- ドメイン用語
	- ビジネス用語の定義
	- UI/UX用語の定義
	- コード上の命名規則

#### 2. 作業単位のドキュメント（`.steering/[YYYMMDD]-[開発タイトル]`）

特定の開発作業における「**今回何をするか**」を定義する一時的なステアリングファイル
作業完了後は参照用として保持されますが、新しい作業では新しいディレクトリを作成

- **requirements.md** - 今回の作業の要求内容
	- 変更・追加する機能の説明
	- ユーザーストーリー
	- 受け入れ条件
	- 制約事項

- **design.md** - 変更内容の設計
	- 実装アプローチ
	- 変更するコンポーネント
	- データ構造の変更
	- 影響範囲の分析

- **tasklist.md** タスクリスト
	- 具体的な実装タスク
	- タスクの進行状況
	- 完了条件

### ステアリングディレクトリの命名規則

```
.steering/[YYYMMDDD]-[開発タイトル]/
```

**例：**
- `.steering/20250103-initial-implementation/`
- `.steering/20250103-add-tag-feature/`
- `.steering/20250103-fix-filter-bug/`
- `.steering/20250103-improve-performance/`

## 開発プロセス

### 初回セットアップ時の手順

#### 1. フォルダ作成
``` bash
mkdir -p docs
mkdir -p .steering
```

#### 2. 永続的ドキュメント作成（`docs/`）

アプリケーション全体の設計を定義します。
各ドキュメントを作成後、必ず確認・承認を得てから次に進みます。

1. `docs/product-requirements.md` - プロダクト要求定義書
2. `docs/functional-design.md` - 機能設計書
3. `docs/architecrure.md` - 技術仕様書
4. `docs/repository-strucrure.md` - リポジトリ構造定義書
5. `docs/development-guidelines.md` - 開発ガイドライン
6. `docs/glossay.md` - ユビキタス言語定義

**重要** 1ファイルごとに作成後、必ず確認・承認を得てから次のファイル作成を行う

### 3. 初回実装用のステアリングファイルの作成

```bash
mkdir -p .steering/[YYYYMMDD]20250103-initial-implementation
```

作成するドキュメント
1. `.steering/[YYYYMMDD]-initial-implementation/requirements.md` - 初回実装の要求
2. `.steering/[YYYYMMDD]-initial-implementation/design.md` - 実装設計
3. `.steering/[YYYYMMDD]-initial-implementation/tasklist.md` - 実装タスク

## アーキテクチャ

```
[GitHub Actions (Cron: 毎日1回)]
  └→ Python スクリプト
       ├→ YouTube Data API で全動画 + 再生回数取得
       ├→ 書籍情報抽出（チャンネル別パターン対応）
       └→ JSON ファイル生成 → git commit & push

[Vike + React SSR (Cloudflare Workers)]
  └→ ビルド時に public/data/*.json を同梱
       ├ rankings.json       (紹介回数ランキング)
       ├ rankings_views.json (再生回数ランキング)
       ├ rankings_likes.json (いいね数ランキング)
       └ books.json          (全書籍データ)
```

## 技術スタック

| 要素           | 選択                                                   | 費用 | 理由                                         |
| -------------- | ------------------------------------------------------ | ---- | -------------------------------------------- |
| Frontend       | Vike + React + Cloudflare Workers                      | 無料 | SSR。SEO対応                                 |
| フレームワーク | Vike (vike-react + vike-photon)                        | 無料 | SSR/SSGフレームワーク                        |
| データ収集     | Python (GitHub Actions)                                | 無料 | YouTube Data APIで全動画取得                 |
| 書籍情報取得   | Amazon PA-API                                          | 無料 | Amazonリンク→書籍情報取得（書籍以外は自動除外）|
| データ保存     | JSON ファイル (git管理)                                | 無料 | DB不要。シンプル                             |
| 定期実行       | GitHub Actions Cron                                    | 無料 | Pythonで JSON生成 → auto commit              |
| ホスティング   | Cloudflare Workers                                     | 無料 | SSR対応。wrangler deployでデプロイ           |
| DNS            | Cloudflare DNS                                         | 無料 | ムームードメインからネームサーバーを移管済み |

## 対象チャンネル

| チャンネル                   | channel_id               | 抽出パターン                                           |
| ---------------------------- | ------------------------ | ------------------------------------------------------ |
| 本要約チャンネル             | UCEixleMT76xDzoiEb9ZA7XA | パターン1: 「タイトル：」「著者：」「出版社：」        |
| サラタメさん                 | UCaG7jufgiw4p5mphPPVbqhw | パターン1: 同上                                        |
| フェルミ漫画大学             | UC9V4eJBNx_hOieGG51NZ6nA | パターン2: 「参考：書名 著者名 さま」                  |
| 学識サロン                   | UCC4NkFV-L-vVYD5z_Ei5dUA | パターン3: 「【amazonリンク】\n『書名』著者 / 出版社」 |
| アバタロー                   | UCduDJ6s3mMchYMy2HvqalxQ | パターン7: 「書籍の購入」セクション                    |
| 七瀬アリーサ【大人の勉強ch】 | UCHk4PXQ2hSGT_B9lqH-redQ | パターン6: amzn.toリンクベースの汎用抽出               |
| サムの本解説ch               | UCcdd3kS52T9Zyo-SWfj86bA | パターン4: 「【今回の参考書籍📚】」セクション          |
| PIVOT                        | UC8yHePe_RgUBE-waRWy6olw | パターン5: 「＜参考書籍＞」セクション                  |

### 追加予定チャンネル

- 三宅書店
- 出版区

## スクリプト

### scripts/fetch_videos.py

YouTube Data APIで全チャンネルの動画を取得し、概要欄のAmazonリンクからPA-APIで書籍情報を取得してJSONを生成。

#### 処理フロー

1. YouTube APIで動画取得（概要欄含む）
2. 概要欄からAmazonリンク抽出（amzn.to, amazon.co.jp/dp/）
3. amzn.to短縮URLはリダイレクト解決してASIN取得
4. PA-API GetItemsでASINから商品情報取得
5. Binding（製本形態）で書籍判定、書籍以外は除外
6. 書籍情報（タイトル、著者、出版社、画像URL、ASIN）をJSONに保存

#### 書籍判定（Binding）

**書籍として認識:**
- 単行本, 文庫, 新書, ハードカバー, ペーパーバック, コミック, ムック
- Kindle版, Paperback, Hardcover

**除外:**
- CD, DVD, Blu-ray, Audible版, Video Game, Electronics など

### scripts/fetch_amazon.py

書籍情報（画像・著者・出版社・出版日・ISBN）を取得するスクリプト。

#### タイトル正規化（NDL検索前）

`normalize_title_for_search()` で以下を除去してからNDL検索:

- サブタイトル: `――` `―` `—` `:` `：` 以降
- 版表記: `新版` `改訂版` `[第〇版]` `【...】`
- 形態プレフィックス: `新書：` `文庫：`
- 括弧注釈: `（新潮文庫）` `(ソフトカバー)`
- `『』` の囲み

#### 取得フロー

1. **NDLサーチ**（国立国会図書館）でタイトル → ISBN取得
2. **openBD** でISBN → 画像・著者・出版社・出版日取得（正式タイトルで統一）
3. 取れなかった場合 → **Google Books API** にフォールバック（クォータ制限あり: 1日1,000リクエスト）
4. ISBNが取得できた書籍は `https://www.amazon.co.jp/dp/{ISBN}?tag=business-book-ranking02-22` に変換

#### CSV連携（books_no_isbn_edit.csv）

- `search_title` 列: NDL検索用の別タイトルを指定
- `delete` 列: `1` で書籍を削除
- `isbn` 列: 手動入力のISBN

#### 実行方法

```bash
# 通常
python3 scripts/fetch_amazon.py

# Google Books APIクォータ切れの場合（NDL+openBDのみ）
GOOGLE_BOOKS_API_KEY="" python3 scripts/fetch_amazon.py
```

### scripts/paapi_utils.py

PA-API（Product Advertising API）ユーティリティモジュール。

- `PaapiClient`: PA-APIクライアント（認証、商品情報取得、書籍判定）
- `resolve_amzn_redirect()`: amzn.to短縮URL → ASIN変換
- `extract_asins_from_text()`: テキストからAmazonリンクのASIN抽出

### scripts/fetch_amazon_info.py

PA-APIを使用してAmazonリンクから書籍情報を取得。fetch_videos.pyから呼び出される。

- `extract_books_from_amazon_links()`: URLリストから書籍情報取得（書籍以外は自動除外）

## データ運用手順

### 定期更新（差分のみ）

```bash
# 1. YouTube動画取得 → Amazonリンク抽出 → PA-APIで書籍情報取得 → JSON生成
python3 scripts/fetch_videos.py

# 2. フロントエンドにコピー
cp data/*.json frontend/public/data/

# 3. ビルド＆デプロイ
cd frontend && npm run build && npx wrangler deploy
```

### 初回・リセット時（全件取得）

```bash
# チャンネルごとに処理（時間がかかるため）
python3 scripts/fetch_videos.py --channel "サラタメ" --full
python3 scripts/fetch_videos.py --channel "本要約" --full
# ... 全チャンネル完了後 ...

# フロントエンドに反映
cp data/*.json frontend/public/data/
cd frontend && npm run build && npx wrangler deploy
```

### fetch_videos.py オプション

| オプション | 用途 |
|-----------|------|
| なし | 差分更新（前回以降の新動画のみ） |
| `--full` | 全件取得（初回・リセット時） |
| `--channel "名前"` | 指定チャンネルのみ処理（部分一致） |
| `--list` | チャンネル一覧を表示 |

### デプロイのみ（データ更新なし）

```bash
cd frontend && npm run build && npx wrangler deploy
```

## ページ構成（Vike + React）

- `/` — トップ（総合ランキング） → `pages/index/+Page.tsx`
- `/book/:id` — 書籍詳細（書籍カバー画像、紹介動画一覧） → `pages/book/@id/+Page.tsx`
- `/channels` — チャンネル一覧 → `pages/channels/+Page.tsx`

### Vike設定

- `pages/+config.ts` — グローバル設定（`ssr: true`, `prerender: false`）
- `pages/+Layout.tsx` — 共通レイアウト
- `pages/+Head.tsx` — HTML head

## JSONデータ設計

### data/books.json

```json
{
  "id": "abc123def456",
  "title": "嫌われる勇気",
  "author": "岸見一郎、古賀史健",
  "publisher": "ダイヤモンド社",
  "amazon_url": "https://www.amazon.co.jp/dp/9784478025819?tag=business-book-ranking02-22",
  "image_url": "https://cover.openbd.jp/9784478025819.jpg",
  "isbn": "9784478025819",
  "publication_date": "20130101",
  "count": 8,
  "total_views": 12500000,
  "total_likes": 85000,
  "videos": [
    {
      "video_id": "xxx",
      "video_title": "...",
      "channel": "本要約チャンネル",
      "link": "https://www.youtube.com/watch?v=xxx",
      "published": "2024-01-01T00:00:00Z",
      "view_count": 500000,
      "like_count": 12000
    }
  ]
}
```

### data/rankings\*.json（軽量版）

id, title, author, count, total_views, total_likes, amazon_url, image_url, publisher, publication_date のみ。

## 認証情報

- YouTube Data API Key: `.env` の `YOUTUBE_API_KEY`（git管理外）
- Google Books API Key: `.env` の `GOOGLE_BOOKS_API_KEY`（YouTube APIキーと同じでOK）
- Amazon アソシエイトタグ: `business-book-ranking02-22`（全リンクのtagパラメータで使用）
- Cloudflare Workers プロジェクト名: `bisiness-book-ranking`
- Cloudflare Workers URL: `bisiness-book-ranking.shinsuke-mito.workers.dev`
- カスタムドメイン: `business.douga-summary.jp`
- DNS: Cloudflare DNS（ムームードメインからネームサーバー移管済み）
  - ネームサーバー: `benedict.ns.cloudflare.com`, `lorna.ns.cloudflare.com`

### .env の形式

```
YOUTUBE_API_KEY=AIzaSy...
AMAZON_ACCESS_KEY=AKIA...
AMAZON_SECRET_KEY=...
```

## 収益化

| 収益源                     | 単価目安            |
| -------------------------- | ------------------- |
| Amazonアソシエイト（書籍） | 3%（100〜200円/冊） |
| 忍者AdMax                  | RPM 200〜400円      |
| Google AdSense             | RPM 300〜500円      |

### Amazonアソシエイト注意事項

- タグは `business-book-ranking02-22` を使用（`miton31003-22` ではない）
- アソシエイト管理画面でサイトのドメインを登録する必要あり
- localhost からのクリックはトラッキング対象外

## 将来対応

- [ ] カテゴリの自動分類
- [ ] SEO対策
- [ ] 追加チャンネル: 三宅書店, 出版区

- [ ] ISBNで重複統一 → 同一ISBNの書籍をマージ、ランキング反映
      python3 scripts/merge_by_isbn.py

- [ ] ISBNでタイトルを統一 ※fetch_amazon.py に統合済み
- [ ] ISBN-13 → ISBN-10変換 = ASIN取得 ※fetch_amazon.py に統合済み

- [] サイトマップを作成
  cd /Users/miton/workspace/bisiness-book-ranking
  python3 scripts/generate_sitemap.py

- [ ] フロントエンドに反映
      cp data/\*.json frontend/public/data/

- [ ] ISBNが取得できているものとできていないものを分ける
- [ ] ISBNを取得できていないものの一覧を取得
- [ ] amzn.toリンクありの場合 → リンクからASIN抽出（リダイレクト先URLに含まれる）
- [ ] どちらもない場合 → タイトルでAmazon検索

- [ ] 出版社別、出版年別、チャンネル別、紹介年別、ジャンル別
