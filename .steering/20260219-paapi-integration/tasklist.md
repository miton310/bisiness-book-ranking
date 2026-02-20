# PA-API統合 - タスクリスト

## 実装タスク

### Phase 1: PA-APIユーティリティ作成

- [x] `scripts/paapi_utils.py` 新規作成
  - [x] `PaapiClient` クラス実装
  - [x] `get_items()` メソッド（ASINから商品情報取得）
  - [x] `_is_book_binding()` メソッド（書籍判定）
  - [x] `resolve_amzn_redirect()` 関数（短縮URL解決）
  - [x] `extract_asins_from_text()` 関数（テキストからASIN抽出）
- [x] `python-amazon-paapi` パッケージインストール
- [x] インポートエラー修正（`Country`, `AmazonError`）

### Phase 2: fetch_videos.py 改修

- [x] `extract_book_info_list()` 簡略化
  - [x] パターンマッチング削除（パターン1〜7）
  - [x] Amazonリンク抽出 → PA-API呼び出しに変更
- [x] 不要な関数削除
  - [x] `clean_book_title()` 削除
  - [x] `is_valid_book_title()` 削除
- [x] コマンドラインオプション追加
  - [x] `--channel NAME` オプション
  - [x] `--list` オプション

### Phase 3: fetch_amazon_info.py 改修

- [x] PA-API使用に書き換え
- [x] `extract_books_from_amazon_links()` 更新
- [x] フォールバック処理（PA-API使用不可時）

### Phase 4: データ再取得

- [ ] 既存データ削除
  - [x] `data/books.json` 削除
  - [x] `data/rankings*.json` 削除
  - [x] `data/fetch_state.json` 削除
- [ ] チャンネルごとにデータ再取得
  - [x] サラタメさん
  - [x] 本要約チャンネル
  - [x] フェルミ漫画大学
  - [x] 学識サロン
  - [x] アバタロー
  - [ ] 七瀬アリーサ
  - [x] サムの本解説ch
  - [x] PIVOT
  - [x] flier
  - [x] 中田敦彦のYouTube大学
  - [x] TBS CROSS DIG
  - [ ] マナビジネス
  - [x] 新R25

### Phase 5: 検証・デプロイ

- [ ] データ品質確認
- [ ] フロントエンドにコピー
- [ ] ビルド・デプロイ

## 実行コマンド

### チャンネル一覧表示
```bash
python3 scripts/fetch_videos.py --list
```

### 1チャンネルずつ処理
```bash
# サラタメさん
python3 scripts/fetch_videos.py --channel "サラタメ" --full

# 本要約チャンネル
python3 scripts/fetch_videos.py --channel "本要約" --full

# 以降、同様に各チャンネルを処理
```

### 差分更新（全チャンネル一括）
```bash
python3 scripts/fetch_videos.py
```

### フロントエンド反映
```bash
cp data/*.json frontend/public/data/
cd frontend && npm run build && npx wrangler deploy
```

## 完了条件

- [ ] 全チャンネルのデータ取得完了
- [ ] 書籍以外の商品が除外されている
- [ ] タイトル・著者・出版社が正確に取得されている
- [ ] フロントエンドで正常に表示される
