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

const ITEMS_PER_PAGE = 20

export function RankingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sortMode = (searchParams.get('sort') as SortMode) || 'count'
  const currentPage = parseInt(searchParams.get('page') || '1', 10)
  const searchQuery = searchParams.get('q') || ''
  const [books, setBooks] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [inputValue, setInputValue] = useState(searchQuery)

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

  // 検索フィルタ
  const filteredBooks = searchQuery
    ? books.filter(book =>
        book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (book.author && book.author.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : books

  const totalPages = Math.ceil(filteredBooks.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const currentBooks = filteredBooks.slice(startIndex, startIndex + ITEMS_PER_PAGE)

  const handleSort = (mode: SortMode) => {
    const params: Record<string, string> = { sort: mode, page: '1' }
    if (searchQuery) params.q = searchQuery
    setSearchParams(params)
  }

  const handlePageChange = (page: number) => {
    const params: Record<string, string> = { sort: sortMode, page: page.toString() }
    if (searchQuery) params.q = searchQuery
    setSearchParams(params)
    window.scrollTo(0, 0)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const params: Record<string, string> = { sort: sortMode, page: '1' }
    if (inputValue.trim()) params.q = inputValue.trim()
    setSearchParams(params)
  }

  const handleClearSearch = () => {
    setInputValue('')
    setSearchParams({ sort: sortMode, page: '1' })
  }

  const renderPagination = () => {
    const pages: (number | string)[] = []

    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push('...')

      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      for (let i = start; i <= end; i++) pages.push(i)

      if (currentPage < totalPages - 2) pages.push('...')
      pages.push(totalPages)
    }

    return (
      <div className="pagination">
        <button
          className="page-btn"
          disabled={currentPage === 1}
          onClick={() => handlePageChange(currentPage - 1)}
        >
          ←
        </button>
        {pages.map((page, i) =>
          typeof page === 'number' ? (
            <button
              key={i}
              className={`page-btn ${page === currentPage ? 'active' : ''}`}
              onClick={() => handlePageChange(page)}
            >
              {page}
            </button>
          ) : (
            <span key={i} className="page-ellipsis">{page}</span>
          )
        )}
        <button
          className="page-btn"
          disabled={currentPage === totalPages}
          onClick={() => handlePageChange(currentPage + 1)}
        >
          →
        </button>
      </div>
    )
  }

  return (
    <div>
      <h1>全ランキング</h1>
      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          className="search-input"
          placeholder="タイトル・著者で検索..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <button type="submit" className="search-btn">検索</button>
        {searchQuery && (
          <button type="button" className="search-clear" onClick={handleClearSearch}>✕</button>
        )}
      </form>
      {searchQuery && (
        <p className="search-result">「{searchQuery}」の検索結果: {filteredBooks.length}件</p>
      )}
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
        <>
          <div className="ranking-list">
            {currentBooks.map((book, i) => (
              <div key={book.id} className="ranking-card">
                <span className="rank">{startIndex + i + 1}</span>
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
          {renderPagination()}
        </>
      )}
    </div>
  )
}
