import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchRankings, fetchRankingsViews, fetchRankingsLikes } from '../data'
import type { RankingEntry } from '../types'

type SortMode = 'count' | 'views' | 'likes'

const SORT_OPTIONS: { key: SortMode; label: string }[] = [
  { key: 'count', label: '紹介回数順' },
  { key: 'views', label: '再生回数順' },
  { key: 'likes', label: 'いいね順' },
]

export function RankingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sortMode = (searchParams.get('sort') as SortMode) || 'count'
  const [books, setBooks] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const fetcher =
      sortMode === 'views' ? fetchRankingsViews :
      sortMode === 'likes' ? fetchRankingsLikes :
      fetchRankings
    fetcher().then(data => {
      setBooks(data)
      setLoading(false)
    })
  }, [sortMode])

  const handleSort = (mode: SortMode) => {
    setSearchParams({ sort: mode })
  }

  return (
    <div>
      <h1>全ランキング</h1>
      <div className="sort-tabs">
        {SORT_OPTIONS.map(opt => (
          <button
            key={opt.key}
            className={`sort-tab ${sortMode === opt.key ? 'active' : ''}`}
            onClick={() => handleSort(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      {loading ? (
        <p>読み込み中...</p>
      ) : (
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
                  <span>紹介 {book.count}回</span>
                  <span>再生 {book.total_views.toLocaleString()}</span>
                  <span>いいね {book.total_likes.toLocaleString()}</span>
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
      )}
    </div>
  )
}
