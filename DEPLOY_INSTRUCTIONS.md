# Cloudflare Pages デプロイ手順

## 1. Cloudflare Pages プロジェクトを作成

### 手動で作成する場合:
1. [Cloudflare Dashboard](https://dash.cloudflare.com) にログイン
2. Workers & Pages → Create application → Pages → Connect to Git
3. GitHubリポジトリを選択（またはDirect Uploadを選択）
4. プロジェクト名: `business-book-ranking`
5. ビルド設定:
   - Framework preset: Vite
   - Build command: `cd frontend && npm run build`
   - Build output directory: `frontend/dist`
   - Root directory: `/`

### または、Wrangler CLIで作成:
```bash
# Wrangler インストール（まだの場合）
npm install -g wrangler

# Cloudflareにログイン
wrangler login

# プロジェクト作成（初回のみ）
cd frontend
npm run build
npx wrangler pages deploy dist --project-name=business-book-ranking
```

## 2. カスタムドメイン設定

1. Cloudflare Dashboard → Workers & Pages
2. business-book-ranking プロジェクトを選択
3. Custom domains → Set up a custom domain
4. 取得済みのドメインを入力
5. DNSレコードが自動設定されます

## 3. GitHub Secrets 設定

リポジトリの Settings → Secrets and variables → Actions で以下を追加:

### CLOUDFLARE_API_TOKEN
1. Cloudflare Dashboard → My Profile → API Tokens
2. Create Token → Edit Cloudflare Workers
3. または、カスタムトークンを作成:
   - Permissions: Account - Cloudflare Pages: Edit
   - Account Resources: Include - 自分のアカウント

### CLOUDFLARE_ACCOUNT_ID
1. Cloudflare Dashboard → Workers & Pages
2. 右側のAccount IDをコピー

### YOUTUBE_API_KEY
1. Google Cloud Console
2. YouTube Data API v3のAPIキー

## 4. 手動デプロイ（テスト）

```bash
# ローカルでビルド
cd frontend
npm install
npm run build

# Cloudflare Pagesにデプロイ
npx wrangler pages deploy dist --project-name=business-book-ranking
```

## 5. 自動デプロイの確認

GitHub Actions の workflow_dispatch で手動実行してテスト:
1. GitHub リポジトリ → Actions
2. "Update Book Rankings" workflow を選択
3. Run workflow

成功すると、Cloudflare Pagesに自動デプロイされます。
