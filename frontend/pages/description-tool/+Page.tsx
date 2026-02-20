import { useState, useEffect } from 'react'

interface Book {
  id: string
  title: string
  author: string | null
  publisher: string | null
  category?: string
  image_url?: string
  description?: string
}

interface SavedDescription {
  id: string
  title: string
  description: string
  savedAt: string
}

export default function Page() {
  const [books, setBooks] = useState<Book[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Book[]>([])
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [description, setDescription] = useState('')
  const [savedDescriptions, setSavedDescriptions] = useState<SavedDescription[]>([])
  const [message, setMessage] = useState('')

  // 書籍データを読み込み
  useEffect(() => {
    fetch('/data/books.json')
      .then(res => res.json())
      .then(data => setBooks(data))
      .catch(err => console.error('Failed to load books:', err))
  }, [])

  // localStorageから保存済みの紹介文を読み込み
  useEffect(() => {
    const saved = localStorage.getItem('book-descriptions')
    if (saved) {
      setSavedDescriptions(JSON.parse(saved))
    }
  }, [])

  // 検索
  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    const query = searchQuery.toLowerCase()
    const results = books
      .filter(book =>
        book.title.toLowerCase().includes(query) ||
        (book.author && book.author.toLowerCase().includes(query))
      )
      .slice(0, 20)
    setSearchResults(results)
  }

  // 本を選択
  const handleSelectBook = (book: Book) => {
    setSelectedBook(book)
    setSearchResults([])
    setSearchQuery('')
    // 既に保存済みの紹介文があれば読み込む
    const saved = savedDescriptions.find(s => s.id === book.id)
    setDescription(saved?.description || book.description || '')
  }

  // 保存
  const handleSave = () => {
    if (!selectedBook || !description.trim()) {
      setMessage('本を選択し、紹介文を入力してください')
      return
    }

    const newSaved: SavedDescription = {
      id: selectedBook.id,
      title: selectedBook.title,
      description: description.trim(),
      savedAt: new Date().toISOString(),
    }

    const updated = [
      ...savedDescriptions.filter(s => s.id !== selectedBook.id),
      newSaved,
    ].sort((a, b) => b.savedAt.localeCompare(a.savedAt))

    setSavedDescriptions(updated)
    localStorage.setItem('book-descriptions', JSON.stringify(updated))
    setMessage(`「${selectedBook.title}」の紹介文を保存しました`)
    setTimeout(() => setMessage(''), 3000)
  }

  // JSONエクスポート
  const handleExport = () => {
    const data = JSON.stringify(savedDescriptions, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `book-descriptions-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 削除
  const handleDelete = (id: string) => {
    const updated = savedDescriptions.filter(s => s.id !== id)
    setSavedDescriptions(updated)
    localStorage.setItem('book-descriptions', JSON.stringify(updated))
  }

  return (
    <div>
      <h2 className="page-heading">本の紹介文入力ツール</h2>
      <p className="subtitle">Perplexity等で生成した紹介文を入力・管理</p>

      {/* 検索 */}
      <div className="search-section">
        <div className="search-form">
          <input
            type="text"
            className="search-input"
            placeholder="本のタイトルまたは著者で検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="search-btn" onClick={handleSearch}>
            検索
          </button>
        </div>

        {/* 検索結果 */}
        {searchResults.length > 0 && (
          <div className="search-results">
            {searchResults.map(book => (
              <div
                key={book.id}
                className="search-result-item"
                onClick={() => handleSelectBook(book)}
              >
                {book.image_url && (
                  <img src={book.image_url} alt={book.title} className="result-thumb" />
                )}
                <div className="result-info">
                  <strong>{book.title}</strong>
                  {book.author && <span className="result-author">{book.author}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 選択された本 */}
      {selectedBook && (
        <div className="selected-book">
          <h3>選択中の本</h3>
          <div className="book-detail">
            {selectedBook.image_url && (
              <img src={selectedBook.image_url} alt={selectedBook.title} className="selected-thumb" />
            )}
            <div className="selected-info">
              <p className="selected-title">{selectedBook.title}</p>
              {selectedBook.author && <p>著者: {selectedBook.author}</p>}
              {selectedBook.publisher && <p>出版社: {selectedBook.publisher}</p>}
              {selectedBook.category && <p>カテゴリ: {selectedBook.category}</p>}
            </div>
          </div>

          <div className="description-input">
            <label>紹介文</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="この本の紹介文を入力してください..."
              rows={6}
            />
            <div className="char-count">{description.length}文字</div>
            <button className="save-btn" onClick={handleSave}>
              保存
            </button>
          </div>
        </div>
      )}

      {/* メッセージ */}
      {message && <div className="message">{message}</div>}

      {/* 保存済みリスト */}
      {savedDescriptions.length > 0 && (
        <div className="saved-section">
          <div className="saved-header">
            <h3>保存済みの紹介文 ({savedDescriptions.length}件)</h3>
            <button className="export-btn" onClick={handleExport}>
              JSONエクスポート
            </button>
          </div>
          <div className="saved-list">
            {savedDescriptions.map(saved => (
              <div key={saved.id} className="saved-item">
                <div className="saved-title">{saved.title}</div>
                <div className="saved-description">{saved.description}</div>
                <div className="saved-actions">
                  <button
                    className="edit-btn"
                    onClick={() => {
                      const book = books.find(b => b.id === saved.id)
                      if (book) handleSelectBook(book)
                    }}
                  >
                    編集
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(saved.id)}
                  >
                    削除
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
