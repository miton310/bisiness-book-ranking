import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export default function Page() {
  const { categoryName, books } = useData<Data>()

  if (books.length === 0) {
    return (
      <div>
        <nav className="breadcrumb" aria-label="パンくず">
          <a href="/">トップ</a>
          <span className="breadcrumb-sep">›</span>
          <span className="breadcrumb-current">{categoryName}</span>
        </nav>
        <p>このジャンルの書籍はまだ登録されていません。</p>
      </div>
    )
  }

  return (
    <div>
      <nav className="breadcrumb" aria-label="パンくず">
        <a href="/">トップ</a>
        <span className="breadcrumb-sep">›</span>
        <span className="breadcrumb-current">{categoryName}</span>
      </nav>

      <section className="site-intro">
        <h1>{categoryName}のおすすめビジネス書ランキング</h1>
        <p>
          本要約チャンネル・サラタメさん・フェルミ漫画大学など人気YouTuberが動画で紹介した
          {categoryName}ジャンルの書籍を集計。紹介回数・再生回数をもとにランキング化した{books.length}冊です。
        </p>
      </section>

      <div className="ranking-list">
        {books.map((book, i) => (
          <div key={book.id} className="ranking-card">
            <span className="rank">{i + 1}</span>
            <a href={`/book/${book.id}`} className="book-title">
              {book.image_url && (
                <img
                  src={book.image_url}
                  alt={book.title}
                  className="book-cover"
                  loading="lazy"
                />
              )}
            </a>
            <div className="book-info">
              <a href={`/book/${book.id}`} className="book-title">
                {book.title}
              </a>
              {book.author && <span className="book-author">{book.author}</span>}
              {book.publisher && <span className="book-publisher">{book.publisher}</span>}
              <div className="book-stats">
                <span>📚 紹介: <span className="stat-value">{book.count}回</span></span>
                <span>▶️ 再生回数: <span className="stat-value">{book.total_views.toLocaleString()}</span></span>
                <span>👍 いいね: <span className="stat-value">{book.total_likes.toLocaleString()}</span></span>
              </div>
            </div>
            <a
              href={book.amazon_url}
              target="_blank"
              rel="noopener noreferrer"
              className="amazon-btn"
            >
              Amazonで購入する
            </a>
          </div>
        ))}
      </div>

      <div className="back-link-wrap">
        <a href="/" className="back-link">← 全ジャンルのランキングを見る</a>
      </div>
    </div>
  )
}
