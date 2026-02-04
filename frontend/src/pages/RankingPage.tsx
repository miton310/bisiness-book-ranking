import { useEffect, useState, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchBooks } from '../data'
import type { Book } from '../types'

type SortMode = 'count' | 'views' | 'likes'

const SORT_OPTIONS: { key: SortMode; label: string }[] = [
  { key: 'count', label: '紹介回数順' },
  { key: 'views', label: '再生回数順' },
  { key: 'likes', label: 'いいね順' },
]

const ITEMS_PER_PAGE = 20

// 書籍から紹介年のリストを取得
function getYearsFromBooks(books: Book[]): number[] {
  const years = new Set<number>()
  for (const book of books) {
    for (const video of book.videos || []) {
      if (video.published) {
        const year = new Date(video.published).getFullYear()
        if (year >= 2015 && year <= new Date().getFullYear()) {
          years.add(year)
        }
      }
    }
  }
  return Array.from(years).sort((a, b) => b - a) // 降順
}

// 書籍を指定年でフィルタリングし、その年の統計を再計算
function filterBooksByYear(books: Book[], year: number | null): Book[] {
  if (!year) return books

  return books
    .map(book => {
      const filteredVideos = (book.videos || []).filter(v => {
        if (!v.published) return false
        return new Date(v.published).getFullYear() === year
      })
      if (filteredVideos.length === 0) return null

      return {
        ...book,
        videos: filteredVideos,
        count: filteredVideos.length,
        total_views: filteredVideos.reduce((sum, v) => sum + (v.view_count || 0), 0),
        total_likes: filteredVideos.reduce((sum, v) => sum + (v.like_count || 0), 0),
      }
    })
    .filter((b): b is Book => b !== null)
}

export function RankingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sortMode = (searchParams.get('sort') as SortMode) || 'count'
  const currentPage = parseInt(searchParams.get('page') || '1', 10)
  const searchQuery = searchParams.get('q') || ''
  const yearParam = searchParams.get('year')
  const selectedYear = yearParam ? parseInt(yearParam, 10) : null

  const [allBooks, setAllBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [inputValue, setInputValue] = useState(searchQuery)

  useEffect(() => {
    setLoading(true)
    fetchBooks()
      .then(data => {
        setAllBooks(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch books:', err)
        setLoading(false)
      })
  }, [])

  // 利用可能な年のリスト
  const availableYears = useMemo(() => getYearsFromBooks(allBooks), [allBooks])

  // 年でフィルタリング → ソート
  const books = useMemo(() => {
    const filtered = filterBooksByYear(allBooks, selectedYear)
    const sorted = [...filtered].sort((a, b) => {
      if (sortMode === 'views') return b.total_views - a.total_views
      if (sortMode === 'likes') return b.total_likes - a.total_likes
      return b.count - a.count
    })
    return sorted
  }, [allBooks, selectedYear, sortMode])

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

  const buildParams = (overrides: Partial<{ sort: string; page: string; q: string; year: string }>) => {
    const params: Record<string, string> = {}
    const sort = overrides.sort ?? sortMode
    const page = overrides.page ?? '1'
    const q = overrides.q ?? searchQuery
    const year = overrides.year !== undefined ? overrides.year : (selectedYear?.toString() || '')

    params.sort = sort
    params.page = page
    if (q) params.q = q
    if (year) params.year = year
    return params
  }

  const handleSort = (mode: SortMode) => {
    setSearchParams(buildParams({ sort: mode, page: '1' }))
  }

  const handlePageChange = (page: number) => {
    setSearchParams(buildParams({ page: page.toString() }))
    window.scrollTo(0, 0)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams(buildParams({ q: inputValue.trim(), page: '1' }))
  }

  const handleClearSearch = () => {
    setInputValue('')
    setSearchParams(buildParams({ q: '', page: '1' }))
  }

  const handleYearChange = (year: number | null) => {
    setSearchParams(buildParams({ year: year?.toString() || '', page: '1' }))
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
      <div className="filter-row">
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
        <div className="year-filter">
          <select
            className="year-select"
            value={selectedYear || ''}
            onChange={(e) => handleYearChange(e.target.value ? parseInt(e.target.value, 10) : null)}
          >
            <option value="">全期間</option>
            {availableYears.map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
        </div>
      </div>
      {selectedYear && (
        <p className="filter-result">{selectedYear}年に紹介された書籍: {filteredBooks.length}件</p>
      )}
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
