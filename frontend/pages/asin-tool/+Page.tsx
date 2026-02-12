import { useState } from 'react'

const AMAZON_TRACKING_ID = 'business-book-ranking02-22'

export default function Page() {
  const [asin, setAsin] = useState('')
  const [result, setResult] = useState('')

  const handleGenerate = () => {
    const trimmed = asin.trim()
    if (!trimmed) return
    const url = `https://www.amazon.co.jp/dp/${trimmed}?tag=${AMAZON_TRACKING_ID}`
    setResult(url)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(result)
  }

  return (
    <div>
      <h2 className="page-heading">ASINリンク生成</h2>
      <p className="subtitle">ASINを入力してアソシエイトリンクを生成</p>

      <div className="asin-form">
        <input
          type="text"
          className="search-input"
          placeholder="ASINを入力（例: 4894514737）"
          value={asin}
          onChange={(e) => setAsin(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
        />
        <button className="search-btn" onClick={handleGenerate}>
          生成
        </button>
      </div>

      {result && (
        <div className="asin-result">
          <p className="asin-label">生成されたリンク:</p>
          <div className="asin-output">
            <a href={result} target="_blank" rel="noopener noreferrer">
              {result}
            </a>
          </div>
          <button className="amazon-btn" onClick={handleCopy}>
            コピー
          </button>
        </div>
      )}
    </div>
  )
}
