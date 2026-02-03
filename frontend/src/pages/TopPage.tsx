import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchRankings } from '../data'
import type { RankingEntry } from '../types'

export function TopPage() {
  const [books, setBooks] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRankings().then(data => {
      setBooks(data.slice(0, 20))
      setLoading(false)
    })
  }, [])

  if (loading) return <p>読み込み中...</p>

  return (
    <div>
      <h1>ビジネス書ランキング TOP20</h1>
      <p className="subtitle">本要約系YouTuberが紹介した書籍を紹介回数でランキング</p>
      <div className="ranking-list">
        {books.map((book, i) => (
          <div key={book.id} className="ranking-card">
            <span className="rank">{i + 1}</span>
            {book.image_url && (
              <img
                src={book.image_url}
                alt={book.title}
                className="book-cover"
                loading="lazy"
              />
            )}
            <div className="book-info">
              <Link to={`/book/${book.id}`} className="book-title">
                {book.title}
              </Link>
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
              Amazon
            </a>
          </div>
        ))}
      </div>
      <div className="more-link">
        <Link to="/ranking">全ランキングを見る →</Link>
      </div>
    </div>
  )
}
