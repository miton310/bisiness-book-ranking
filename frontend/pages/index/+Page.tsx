import { useEffect, useState, useMemo } from 'react'
import { useData } from 'vike-react/useData'
import { fetchBooks } from '../../src/data'
import type { Data } from './+data'
import type { Book, RankingEntry } from '../../src/types'

type SortMode = 'point' | 'count' | 'views' | 'likes'

const SORT_OPTIONS: { key: SortMode; label: string }[] = [
  { key: 'point', label: 'ポイント順' },
  { key: 'count', label: '紹介回数順' },
  { key: 'views', label: '再生回数順' },
  { key: 'likes', label: 'いいね順' },
]

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function calcPoint(book: Book): { point: number; channels: number } {
  const channelVideos = new Map<string, number>()
  for (const v of book.videos || []) {
    if (v.channel) {
      channelVideos.set(v.channel, (channelVideos.get(v.channel) || 0) + 1)
    }
  }
  let point = 0
  for (const count of channelVideos.values()) {
    point += 5 + (count - 1)
  }
  return { point, channels: channelVideos.size }
}

const ITEMS_PER_PAGE = 20

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
  return Array.from(years).sort((a, b) => b - a)
}

function getChannelsFromBooks(books: Book[]): { name: string; count: number }[] {
  const channelCounts = new Map<string, number>()
  for (const book of books) {
    for (const video of book.videos || []) {
      if (video.channel) {
        channelCounts.set(video.channel, (channelCounts.get(video.channel) || 0) + 1)
      }
    }
  }
  return Array.from(channelCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}

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

function filterBooksByChannel(books: Book[], channel: string | null): Book[] {
  if (!channel) return books

  return books
    .map(book => {
      const filteredVideos = (book.videos || []).filter(v => v.channel === channel)
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

// 書籍から出版年のリストを取得
function getPublicationYearsFromBooks(books: Book[]): number[] {
  const years = new Set<number>()
  for (const book of books) {
    if (book.publication_date) {
      const year = new Date(book.publication_date).getFullYear()
      if (year >= 1990 && year <= new Date().getFullYear()) {
        years.add(year)
      }
    }
  }
  return Array.from(years).sort((a, b) => b - a)
}

// 書籍から出版社のリストを取得（冊数順）
function getPublishersFromBooks(books: Book[]): { name: string; count: number }[] {
  const publisherCounts = new Map<string, number>()
  for (const book of books) {
    if (book.publisher) {
      publisherCounts.set(book.publisher, (publisherCounts.get(book.publisher) || 0) + 1)
    }
  }
  return Array.from(publisherCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}

// 書籍からカテゴリのリストを取得（冊数順）
function getCategoriesFromBooks(books: Book[]): { name: string; count: number }[] {
  const categoryCounts = new Map<string, number>()
  for (const book of books) {
    if (book.category) {
      const topCategory = book.category.split(' > ')[0]
      categoryCounts.set(topCategory, (categoryCounts.get(topCategory) || 0) + 1)
    }
  }
  return Array.from(categoryCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
}

// 書籍を出版年でフィルタリング
function filterBooksByPublicationYear(books: Book[], pubYear: number | null): Book[] {
  if (!pubYear) return books
  return books.filter(book => {
    if (!book.publication_date) return false
    return new Date(book.publication_date).getFullYear() === pubYear
  })
}

// 書籍を出版社でフィルタリング
function filterBooksByPublisher(books: Book[], publisher: string | null): Book[] {
  if (!publisher) return books
  return books.filter(book => book.publisher === publisher)
}

// 書籍をカテゴリでフィルタリング
function filterBooksByCategory(books: Book[], category: string | null): Book[] {
  if (!category) return books
  return books.filter(book => {
    if (!book.category) return false
    return book.category.startsWith(category)
  })
}

function useSearchParams() {
  const [params, setParams] = useState(() => {
    if (typeof window === 'undefined') return new URLSearchParams()
    return new URLSearchParams(window.location.search)
  })

  // ブラウザの戻る/進むボタンに対応
  useEffect(() => {
    const handlePopState = () => {
      setParams(new URLSearchParams(window.location.search))
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const updateParams = (newParams: Record<string, string>) => {
    const searchParams = new URLSearchParams()
    for (const [key, value] of Object.entries(newParams)) {
      if (value) searchParams.set(key, value)
    }
    const newUrl = searchParams.toString() ? `?${searchParams.toString()}` : window.location.pathname
    window.history.pushState({}, '', newUrl)
    setParams(searchParams)
  }

  return [params, updateParams] as const
}

export default function Page() {
  const { rankings } = useData<Data>()
  const [searchParams, setSearchParams] = useSearchParams()
  const sortMode = (searchParams.get('sort') as SortMode) || 'point'
  const currentPage = parseInt(searchParams.get('page') || '1', 10)
  const searchQuery = searchParams.get('q') || ''
  const yearParam = searchParams.get('year')
  const selectedYear = yearParam ? parseInt(yearParam, 10) : null
  const selectedChannel = searchParams.get('channel') || null
  const pubYearParam = searchParams.get('pubYear')
  const selectedPubYear = pubYearParam ? parseInt(pubYearParam, 10) : null
  const selectedPublisher = searchParams.get('publisher') || null
  const selectedCategory = searchParams.get('category') || null

  // Full book data loaded client-side for filtering/sorting
  const [allBooks, setAllBooks] = useState<Book[] | null>(null)
  const [inputValue, setInputValue] = useState(searchQuery)

  useEffect(() => {
    fetchBooks()
      .then(data => setAllBooks(data))
      .catch(err => console.error('Failed to fetch books:', err))
  }, [])

  // Use full book data when available, fall back to SSR rankings
  const hasFullData = allBooks !== null

  const availableYears = useMemo(() => hasFullData ? getYearsFromBooks(allBooks) : [], [allBooks, hasFullData])
  const availableChannels = useMemo(() => hasFullData ? getChannelsFromBooks(allBooks) : [], [allBooks, hasFullData])
  const availablePubYears = useMemo(() => hasFullData ? getPublicationYearsFromBooks(allBooks) : [], [allBooks, hasFullData])
  const availablePublishers = useMemo(() => hasFullData ? getPublishersFromBooks(allBooks) : [], [allBooks, hasFullData])
  const availableCategories = useMemo(() => hasFullData ? getCategoriesFromBooks(allBooks) : [], [allBooks, hasFullData])
  const totalVideos = useMemo(() => {
    if (!hasFullData) return 0
    return allBooks.reduce((sum, b) => sum + (b.videos?.length || 0), 0)
  }, [allBooks, hasFullData])

  const books = useMemo(() => {
    if (hasFullData) {
      let filtered = filterBooksByYear(allBooks, selectedYear)
      filtered = filterBooksByChannel(filtered, selectedChannel)
      filtered = filterBooksByPublicationYear(filtered, selectedPubYear)
      filtered = filterBooksByPublisher(filtered, selectedPublisher)
      filtered = filterBooksByCategory(filtered, selectedCategory)
      const sorted = [...filtered].sort((a, b) => {
        if (sortMode === 'point') return calcPoint(b).point - calcPoint(a).point
        if (sortMode === 'views') return b.total_views - a.total_views
        if (sortMode === 'likes') return b.total_likes - a.total_likes
        return b.count - a.count
      })
      return sorted
    }
    // SSR: use rankings data (already sorted by count)
    return rankings as (RankingEntry & { videos?: never })[]
  }, [allBooks, hasFullData, selectedYear, selectedChannel, selectedPubYear, selectedPublisher, selectedCategory, sortMode, rankings])

  const filteredBooks = searchQuery
    ? books.filter(book =>
        book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (book.author && book.author.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : books

  const totalPages = Math.ceil(filteredBooks.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const currentBooks = filteredBooks.slice(startIndex, startIndex + ITEMS_PER_PAGE)

  const buildParams = (overrides: Partial<{ sort: string; page: string; q: string; year: string; channel: string; pubYear: string; publisher: string; category: string }>) => {
    const params: Record<string, string> = {}
    const sort = overrides.sort ?? sortMode
    const page = overrides.page ?? '1'
    const q = overrides.q ?? searchQuery
    const year = overrides.year !== undefined ? overrides.year : (selectedYear?.toString() || '')
    const channel = overrides.channel !== undefined ? overrides.channel : (selectedChannel || '')
    const pubYear = overrides.pubYear !== undefined ? overrides.pubYear : (selectedPubYear?.toString() || '')
    const publisher = overrides.publisher !== undefined ? overrides.publisher : (selectedPublisher || '')
    const category = overrides.category !== undefined ? overrides.category : (selectedCategory || '')

    params.sort = sort
    params.page = page
    if (q) params.q = q
    if (year) params.year = year
    if (channel) params.channel = channel
    if (pubYear) params.pubYear = pubYear
    if (publisher) params.publisher = publisher
    if (category) params.category = category
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

  const handleChannelChange = (channel: string | null) => {
    setSearchParams(buildParams({ channel: channel || '', page: '1' }))
  }

  const handlePubYearChange = (pubYear: number | null) => {
    setSearchParams(buildParams({ pubYear: pubYear?.toString() || '', page: '1' }))
  }

  const handlePublisherChange = (publisher: string | null) => {
    setSearchParams(buildParams({ publisher: publisher || '', page: '1' }))
  }

  const handleCategoryChange = (category: string | null) => {
    setSearchParams(buildParams({ category: category || '', page: '1' }))
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
      <div className="summary-stats">
        <span>投稿数: <strong>{hasFullData ? totalVideos.toLocaleString() : '...'}</strong></span>
        <span>書籍数: <strong>{hasFullData ? allBooks.length.toLocaleString() : rankings.length.toLocaleString()}</strong></span>
      </div>
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
        <div className="filter-selects">
          <select
            className="filter-select"
            value={selectedYear || ''}
            onChange={(e) => handleYearChange(e.target.value ? parseInt(e.target.value, 10) : null)}
          >
            <option value="">全期間</option>
            {availableYears.map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
          <select
            className="filter-select"
            value={selectedChannel || ''}
            onChange={(e) => handleChannelChange(e.target.value || null)}
          >
            <option value="">全チャンネル</option>
            {availableChannels.map(ch => (
              <option key={ch.name} value={ch.name}>{ch.name}</option>
            ))}
          </select>
        </div>
        {/* 3段目: 出版年・出版社・ジャンル */}
        <div className="filter-selects">
          <select
            className="filter-select"
            value={selectedPubYear || ''}
            onChange={(e) => handlePubYearChange(e.target.value ? parseInt(e.target.value, 10) : null)}
          >
            <option value="">出版年: 全て</option>
            {availablePubYears.map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
          <select
            className="filter-select"
            value={selectedPublisher || ''}
            onChange={(e) => handlePublisherChange(e.target.value || null)}
          >
            <option value="">出版社: 全て</option>
            {availablePublishers.slice(0, 50).map(pub => (
              <option key={pub.name} value={pub.name}>{pub.name} ({pub.count})</option>
            ))}
          </select>
          <select
            className="filter-select"
            value={selectedCategory || ''}
            onChange={(e) => handleCategoryChange(e.target.value || null)}
          >
            <option value="">ジャンル: 全て</option>
            {availableCategories.map(cat => (
              <option key={cat.name} value={cat.name}>{cat.name} ({cat.count})</option>
            ))}
          </select>
        </div>
      </div>
      {(selectedYear || selectedChannel || selectedPubYear || selectedPublisher || selectedCategory) && (
        <p className="filter-result">
          {[
            selectedYear && `紹介年:${selectedYear}年`,
            selectedChannel,
            selectedPubYear && `出版:${selectedPubYear}年`,
            selectedPublisher,
            selectedCategory,
          ].filter(Boolean).join(' / ')}
          : {filteredBooks.length}件
        </p>
      )}
      <div className="ranking-list">
        {currentBooks.map((book, i) => (
          <div key={book.id} className="ranking-card">
            <span className="rank">{startIndex + i + 1}</span>
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
              {'publisher' in book && book.publisher && <span className="book-publisher">{book.publisher}</span>}
              {'publication_date' in book && book.publication_date && (
                <span className="book-pubdate">{formatDate(book.publication_date)}</span>
              )}
              {'category' in book && book.category && (
                <span className="book-category">{book.category}</span>
              )}
              <div className="book-stats">
                {hasFullData && 'videos' in book && (() => { const { point, channels } = calcPoint(book as Book); return (
                  <span>📊 <span className="stat-value">{point}pt</span>（{channels}ch）</span>
                )})()}
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
      {renderPagination()}
    </div>
  )
}
