# ビジネス書ランキングサイト プロジェクト概要

## コンセプト

本要約系YouTuberが紹介した書籍を集計し、紹介回数でランキング化するサイト。

## 方針: 完全無料運営

バックエンド・DB不要。Python → JSON生成 → 静的サイトとして配信。

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

| 要素 | 選択 | 費用 | 理由 |
|------|------|------|------|
| Frontend | Vike + React + Cloudflare Workers | 無料 | SSR。SEO対応 |
| フレームワーク | Vike (vike-react + vike-photon) | 無料 | SSR/SSGフレームワーク |
| データ収集 | Python (GitHub Actions) | 無料 | YouTube Data APIで全動画取得 |
| 書籍情報取得 | NDLサーチ + openBD（フォールバック: Google Books API） | 無料 | ISBN→画像・著者・出版社取得 |
| データ保存 | JSON ファイル (git管理) | 無料 | DB不要。シンプル |
| 定期実行 | GitHub Actions Cron | 無料 | Pythonで JSON生成 → auto commit |
| ホスティング | Cloudflare Workers | 無料 | SSR対応。wrangler deployでデプロイ |
| DNS | Cloudflare DNS | 無料 | ムームードメインからネームサーバーを移管済み |

## 対象チャンネル

| チャンネル | channel_id | 抽出パターン |
|------------|-----------|-------------|
| 本要約チャンネル | UCEixleMT76xDzoiEb9ZA7XA | パターン1: 「タイトル：」「著者：」「出版社：」 |
| サラタメさん | UCaG7jufgiw4p5mphPPVbqhw | パターン1: 同上 |
| フェルミ漫画大学 | UC9V4eJBNx_hOieGG51NZ6nA | パターン2: 「参考：書名 著者名 さま」 |
| 学識サロン | UCC4NkFV-L-vVYD5z_Ei5dUA | パターン3: 「【amazonリンク】\n『書名』著者 / 出版社」 |
| アバタロー | UCduDJ6s3mMchYMy2HvqalxQ | パターン7: 「書籍の購入」セクション |
| 七瀬アリーサ【大人の勉強ch】 | UCHk4PXQ2hSGT_B9lqH-redQ | パターン6: amzn.toリンクベースの汎用抽出 |
| サムの本解説ch | UCcdd3kS52T9Zyo-SWfj86bA | パターン4: 「【今回の参考書籍📚】」セクション |
| PIVOT | UC8yHePe_RgUBE-waRWy6olw | パターン5: 「＜参考書籍＞」セクション |

### 追加予定チャンネル
- 三宅書店
- 出版区

## スクリプト

### scripts/fetch_videos.py
YouTube Data APIで全チャンネルの動画を取得し、概要欄から書籍情報を抽出してJSONを生成。

#### 書籍抽出パターン（優先順）
1. **パターン1**: 本要約チャンネル/サラタメ — `タイトル：` `著者：` `出版社：`
2. **パターン2**: フェルミ漫画大学 — `参考：書名 著者名 さま`
3. **パターン3**: 学識サロン — `【amazonリンク】` + `『書名』著者 / 出版社`
4. **パターン4**: サムの本解説ch — `【今回の参考書籍📚】` セクション（タイトル行と著者行を分離、`(著)` `(編集)` を解析）
5. **パターン5**: PIVOT — `＜参考書籍＞` セクション（`『タイトル』` を抽出、`「」` の場合は後続テキストも含める、`『』` がない行はスキップ）
6. **パターン6**: 七瀬アリーサ/汎用 — amzn.toリンクベース抽出（同一行 or 前行のテキストをタイトルとして取得）
7. **パターン7**: アバタロー — `【書籍の購入】` `▼書籍の購入` セクション

#### NGワード（is_valid_book_title）
タイトルに以下が含まれる場合は除外:
- セクションヘッダー系: おすすめ動画, チャンネル登録, 関連動画, 動画一覧, SNS, Twitter, Instagram, LINE
- 非書籍系: Audible, Kindle, エッセンシャル版, 簡易版, 本を聴く, 分解説, 要約, 解説, まとめ
- 宣伝系: プレゼント, キャンペーン, 無料, プロフィール, お問い合わせ, メンバーシップ, サブチャンネル
- 七瀬アリーサ宣伝: 七瀬制作, 商品紹介, メッセージカード, Success Book, Your Success, 購入ページ, 特典, 概要欄, デジタル版, 冊子版
- YouTuber自著: OUTPUT読書術
- パターン6のNG（amzn.to抽出時）: TOEIC, 勉強本, 手帳, プランナー, オンライン英会話, AQUES, 金フレ, キクタン, でる1000問, 公式問題集, 精選問題集, 精選模試, タイマー, トレーナー, ボードゲーム, かっさ, テラヘルツ, イヤホン, キーボード, マウス, ディスプレイ, モニター, チェア, ライト付き, Meta Quest, Kindle端末, 本棚デスク 等

#### YouTuber名がタイトルに含まれる場合も除外
アバタロー, サラタメ, 本要約チャンネル, 学識サロン, フェルミ, 三宅, 七瀬, アリーサ

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

### scripts/fetch_amazon_info.py
Amazonリンクから書籍情報を取得（現在未使用、将来PA-API対応時に活用予定）

## データ運用手順

### データ更新（手動）
```bash
# 1. YouTube APIで動画取得 → 書籍抽出 → JSON生成
python3 scripts/fetch_videos.py

# 2. 書籍情報（画像・ISBN等）取得
python3 scripts/fetch_amazon.py
# または Google Books APIクォータ切れの場合（NDL+openBDのみ）:
GOOGLE_BOOKS_API_KEY="" python3 scripts/fetch_amazon.py

# 3. ISBN-13 → ASIN変換
python3 scripts/add_asin_from_isbn.py

# 4. ISBN重複統合
python3 scripts/merge_by_isbn.py

# 5. フロントエンドにコピー
cp data/*.json frontend/public/data/

# 6. ビルド＆デプロイ
cd frontend && npm run build && npx wrangler deploy
```

### デプロイのみ（データ更新なし）
```bash
cd frontend && npm run build && npx wrangler deploy
```

### 表記ゆれ統合
`fetch_amazon.py` 実行後、ISBNベースで同一書籍を統合する。
- ISBNが同じ書籍は自動統合（動画をマージ、count/views/likes を合算）
- `『』` で囲まれたタイトルは外して統合
- ISBNがない表記ゆれは手動対応が必要

## ページ構成（Vike + React）

- `/` — トップ（総合ランキング）  → `pages/index/+Page.tsx`
- `/book/:id` — 書籍詳細（書籍カバー画像、紹介動画一覧）  → `pages/book/@id/+Page.tsx`
- `/channels` — チャンネル一覧  → `pages/channels/+Page.tsx`

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

### data/rankings*.json（軽量版）
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
GOOGLE_BOOKS_API_KEY=AIzaSy...
```

## 収益化

| 収益源 | 単価目安 |
|--------|---------|
| Amazonアソシエイト（書籍） | 3%（100〜200円/冊） |
| 忍者AdMax | RPM 200〜400円 |
| Google AdSense | RPM 300〜500円 |

### Amazonアソシエイト注意事項
- タグは `business-book-ranking02-22` を使用（`miton31003` ではない）
- アソシエイト管理画面でサイトのドメインを登録する必要あり
- localhost からのクリックはトラッキング対象外

## 将来対応

### Amazon PA-API対応（アソシエイト売上実績後）
- ISBNまたはタイトル → PA-API SearchItems → ASIN + 書籍情報 + 正式アフィリエイトリンク
- amzn.toのリダイレクト変換は不要（ISBN/タイトル検索で代替可能）
- 現在のNDL+openBDで取れない洋書・新刊もカバー可能

### その他
- [ ] カテゴリの自動分類
- [ ] SEO対策
- [ ] 追加チャンネル: 三宅書店, 出版区

- [ ] ISBNで重複統一 → 同一ISBNの書籍をマージ、ランキング反映
python3 scripts/merge_by_isbn.py 

- [ ] ISBNでタイトルを統一 ※fetch_amazon.py に統合済み
- [ ] ISBN-13 → ISBN-10変換 = ASIN取得 ※fetch_amazon.py に統合済み

- [ ] フロントエンドに反映
cp data/*.json frontend/public/data/

- [ ] ISBNが取得できているものとできていないものを分ける
- [ ] ISBNを取得できていないものの一覧を取得
- [ ] amzn.toリンクありの場合 → リンクからASIN抽出（リダイレクト先URLに含まれる） 
- [ ] どちらもない場合 → タイトルでAmazon検索

- [ ] 出版社別、出版年別、チャンネル別、紹介年別、ジャンル別
