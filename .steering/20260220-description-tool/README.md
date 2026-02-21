# 本の紹介文入力ツール

## 概要
Perplexity等のAIで生成した本の紹介文を入力・管理するツール。

## URL
- ローカル: http://localhost:5173/description-tool

※本番環境では除外されています（prerender: false）

## 使い方

### 1. 紹介文を入力

1. `/description-tool` にアクセス
2. 本をタイトルまたは著者で検索
3. 検索結果から本を選択
4. Perplexityで紹介文を生成（下記プロンプト参照）
5. 紹介文を貼り付けて「保存」
6. 繰り返し

### 2. JSONエクスポート

複数の紹介文を入力後、「JSONエクスポート」ボタンでダウンロード。

ファイル名例: `book-descriptions-2026-02-20.json`

### 3. books.jsonにマージ

```bash
python scripts/merge_descriptions.py ~/Downloads/book-descriptions-2026-02-20.json
```

このスクリプトは以下を実行：
- `data/books.json` に紹介文をマージ
- `frontend/public/data/books.json` にも同期

### 4. デプロイ

```bash
git add -A
git commit -m "本の紹介文を追加"
git push
```

Cloudflare Pagesが自動でビルド・デプロイ。

## Perplexity用プロンプト例

```
以下の本の紹介文を100〜150文字程度で書いてください。
どんな人におすすめか、どんな学びが得られるか含めてください。
宣伝的な表現は避け、客観的に書いてください。

タイトル: 〇〇
著者: 〇〇
```

## データ構造

### 入力ツールの保存形式（localStorage & エクスポート）

```json
[
  {
    "id": "abc123",
    "title": "本のタイトル",
    "description": "紹介文...",
    "savedAt": "2026-02-20T12:00:00.000Z"
  }
]
```

### books.jsonへのマージ後

```json
{
  "id": "abc123",
  "title": "本のタイトル",
  "author": "著者",
  ...
  "description": "紹介文..."
}
```

## 表示場所

- 書籍詳細ページ（/book/{id}）の「この本について」セクション

## 注意事項

- localStorageに保存されるため、ブラウザを変えるとデータが消える
- 定期的にJSONエクスポートしてバックアップを取ること
- 紹介文は著作権に配慮し、本の内容の要約ではなく「紹介」に留める

## 本番除外設定

`frontend/pages/description-tool/+config.ts` で `prerender: false` を設定し、本番ビルドから除外している。

```typescript
export default {
  prerender: false,
}
```

これにより：
- ローカル開発時: アクセス可能
- 本番環境: 404（ページが存在しない）
