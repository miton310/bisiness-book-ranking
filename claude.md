# ビジネス書ランキングサイト プロジェクト概要

## コンセプト

本要約系YouTuberが紹介した書籍を集計し、紹介回数でランキング化するサイト。

## 仕様

### データ収集
1. 本要約系YouTuberの動画説明文をRSSで取得
2. 説明文から書籍タイトルを抽出（「『』」「「」」内のテキスト）
3. 書籍タイトルからAmazon検索リンクを生成
4. 紹介回数をカウントしてランキング化

### 対象チャンネル（候補）

| チャンネル | 登録者数 | 特徴 |
|------------|---------|------|
| 本要約チャンネル | 約180万人 | 毎日更新、幅広いジャンル |
| サラタメさん | 約70万人 | ビジネス書中心、サラリーマン目線 |
| フェルミ漫画大学 | 約120万人 | 漫画形式で解説 |
| 学識サロン | 約60万人 | ビジネス・自己啓発 |
| アバタロー | 約50万人 | 古典・名著中心 |

### 出力
- 総合ランキング（紹介回数順）
- カテゴリ別ランキング（ビジネス、自己啓発、お金、etc.）
- 新着紹介書籍一覧

## 技術スタック

- **静的サイト生成**: Hugo
- **ホスティング**: Cloudflare Pages（無料）
- **自動更新**: GitHub Actions（6時間ごと）
- **データ取得**: Python + feedparser
- **データ保存**: JSON

## ディレクトリ構成案

```
business-book-ranking/
├── hugo.toml
├── data/
│   ├── channels.json      # 監視チャンネル一覧
│   ├── books.json         # 書籍データ（自動生成）
│   └── ranking.json       # ランキングデータ（自動生成）
├── content/
│   ├── books/             # 書籍個別ページ
│   └── ranking.md         # ランキングページ
├── layouts/
│   ├── _default/
│   ├── index.html
│   └── partials/
├── static/css/
├── scripts/
│   ├── fetch_videos.py    # 動画情報取得
│   ├── extract_books.py   # 書籍タイトル抽出
│   └── generate_ranking.py # ランキング生成
├── .github/workflows/
│   └── update.yml
└── CLAUDE.md
```

## 実装ステップ

### Phase 1: 検証
1. 1チャンネル（本要約チャンネル）で動画説明文を取得
2. 書籍タイトルの抽出精度を検証
3. Amazon検索リンク生成のテスト

### Phase 2: 基本機能
1. Hugo雛形作成
2. 複数チャンネル対応
3. ランキングページ実装
4. GitHub Actions設定

### Phase 3: 拡張
1. カテゴリ分類
2. 書籍詳細ページ
3. デザイン改善
4. SEO対策

## 収益化

| 収益源 | 単価目安 |
|--------|---------|
| Amazonアソシエイト（書籍） | 3%（100〜200円/冊） |
| 忍者AdMax | RPM 200〜400円 |
| Google AdSense | RPM 300〜500円 |

## 課題メモ

- [ ] 説明文にAmazonリンクがない場合の対応
- [ ] 書籍タイトルの表記ゆれ対策（同じ本が別カウントにならないように）
- [ ] カテゴリの自動分類方法

## 参考

- [技術書ランキングをQiita記事の集計から作成したテック・ブック・ランク](https://techbookrank.com/)
- [技術書ランキングサイトをQiita記事の集計から作ったら、約4000冊の技術本がいい感じに並んだ](https://qiita.com/jabba/items/edefda09121877b79760)
- YouTube RSS: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`

## 追加予定チャンネル
三宅書店 出版区


# 技術変更

## 方針: 完全無料運営

バックエンド・DB不要。Python → JSON生成 → 静的サイトとして配信。

## アーキテクチャ

```
[GitHub Actions (Cron: 毎日1回)]
  └→ Python スクリプト
       ├→ YouTube Data API で全動画 + 再生回数取得
       ├→ 書籍情報抽出（チャンネル別パターン対応）
       └→ JSON ファイル生成 → git commit & push

[Vite + React SPA (Cloudflare Pages)]
  └→ ビルド時に public/data/*.json を同梱
       ├ rankings.json       (紹介回数ランキング)
       ├ rankings_views.json (再生回数ランキング)
       └ books.json          (全書籍データ)
```

## 技術スタック

| 要素 | 選択 | 費用 | 理由 |
|------|------|------|------|
| Frontend | Vite + React + Cloudflare Pages | 無料 | SPA。静的配信で高速 |
| データ収集 | Python (GitHub Actions) | 無料 | 既存の抽出ロジック流用。YouTube Data APIで全動画取得 |
| データ保存 | JSON ファイル (git管理) | 無料 | DB不要。シンプル |
| 定期実行 | GitHub Actions Cron | 無料 | Pythonで JSON生成 → auto commit |
| ホスティング | Cloudflare Pages | 無料 | GitHub連携で自動デプロイ |

## コンポーネント役割

| コンポーネント | 言語 | 担当 |
|----------------|------|------|
| `scripts/fetch_videos.py` | Python | YouTube API → 書籍抽出 → JSON生成 |
| React SPA | TypeScript | JSON読み込み → ランキング表示・UI |

## JSONデータ設計

### data/books.json
```json
[
  {
    "id": "book_001",
    "title": "嫌われる勇気",
    "author": "岸見一郎、古賀史健",
    "publisher": "ダイヤモンド社",
    "amazon_url": "https://...",
    "count": 8,
    "total_views": 12500000,
    "total_likes": 85000,
    "videos": [
      {
        "video_id": "xxx",
        "video_title": "...",
        "channel": "本要約チャンネル",
        "published": "2024-01-01",
        "view_count": 500000,
        "like_count": 12000
      }
    ]
  }
]
```

### data/rankings.json（紹介回数順）
### data/rankings_views.json（再生回数合計順）
### data/rankings_likes.json（いいね合計順）
→ books.json のソート順違い。軽量化のためid + title + count + total_views + total_likes のみ。

## ページ構成（React）

- `/` — トップ（総合ランキング TOP20）
- `/ranking/` — 全ランキング（紹介回数順 / 再生回数順 / いいね順 切り替え）
- `/book/:id` — 書籍詳細（紹介動画一覧）

## 認証情報

- YouTube Data API Key: `.env` に保存（git管理外）
- Amazon アソシエイトID: `miton31003`
- Amazon トラッキングID: `business-book-ranking02-22`