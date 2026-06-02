import { useData } from 'vike-react/useData'
import type { Data } from './+data'
import type { Book } from '../../../src/types'
import { categoryToSlug } from '../../../src/categorySlug'

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function buildSummaryText(book: Book): string {
  const channels = [...new Set(book.videos.map(v => v.channel))]
  const years = [...new Set(book.videos.map(v => new Date(v.published).getFullYear()))].sort()
  const firstYear = years[0]
  const lastYear = years[years.length - 1]
  const totalViewsMan = Math.round(book.total_views / 10000)

  const parts: string[] = []

  if (channels.length === 1) {
    parts.push(`「${book.title}」は${channels[0]}が紹介したビジネス書です。`)
  } else {
    const channelStr = channels.slice(0, 3).join('・') + (channels.length > 3 ? `など${channels.length}チャンネル` : '')
    parts.push(`「${book.title}」は${channelStr}が紹介したビジネス書です。`)
  }

  if (firstYear === lastYear) {
    parts.push(`${firstYear}年に紹介され、`)
  } else {
    parts.push(`${firstYear}年から${lastYear}年にかけて継続的に紹介され、`)
  }

  parts.push(`累計${book.count}本の動画で取り上げられています。`)

  if (totalViewsMan >= 1) {
    parts.push(`紹介動画の総再生回数は${totalViewsMan}万回を超えており、`)
  }
  parts.push(`多くの視聴者に支持されている注目の一冊です。`)

  if (book.author) {
    parts.push(`著者は${book.author}氏。`)
  }
  if (book.publisher) {
    parts.push(`${book.publisher}より出版。`)
  }

  return parts.join('')
}

function buildStructuredData(book: Book, pageUrl: string): object {
  const schema: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Book',
    name: book.title,
    url: pageUrl,
  }
  if (book.author) schema.author = { '@type': 'Person', name: book.author }
  if (book.publisher) schema.publisher = { '@type': 'Organization', name: book.publisher }
  if (book.publication_date) schema.datePublished = book.publication_date.slice(0, 10)
  if (book.image_url) schema.image = book.image_url
  if (book.isbn) schema.isbn = book.isbn
  if (book.description) schema.description = book.description
  if (book.amazon_url) {
    schema.offers = {
      '@type': 'Offer',
      url: book.amazon_url,
      availability: 'https://schema.org/InStock',
      priceCurrency: 'JPY',
      seller: { '@type': 'Organization', name: 'Amazon.co.jp' },
    }
  }
  return schema
}

export default function Page() {
  const { book, relatedByAuthor, relatedByCategory } = useData<Data>()

  if (!book) return <p>書籍が見つかりません。<a href="/">トップに戻る</a></p>

  const pageUrl = `https://business.douga-summary.jp/book/${book.id}`
  const summaryText = buildSummaryText(book)
  const structuredData = buildStructuredData(book, pageUrl)
  const topCategory = book.category?.split(' > ')[0]

  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />

      <nav className="breadcrumb" aria-label="パンくず">
        <a href="/">トップ</a>
        {topCategory && (
          <>
            <span className="breadcrumb-sep">›</span>
            <a href={`/category/${categoryToSlug(topCategory)}`}>{topCategory}</a>
          </>
        )}
        <span className="breadcrumb-sep">›</span>
        <span className="breadcrumb-current">{book.title.length > 30 ? book.title.slice(0, 30) + '…' : book.title}</span>
      </nav>

      <div className="detail-header">
        {book.image_url && (
          <img
            src={book.image_url}
            alt={book.title}
            className="detail-cover"
          />
        )}
        <div className="detail-info">
          <h1 className="detail-title">{book.title}</h1>
          <div className="detail-meta">
            {book.author && <p>著者: {book.author}</p>}
            {book.publisher && <p>出版社: {book.publisher}</p>}
            {book.publication_date && <p>出版日: {formatDate(book.publication_date)}</p>}
            {book.category && <p>カテゴリ: {book.category}</p>}
          </div>
          <a
            href={book.amazon_url}
            target="_blank"
            rel="noopener noreferrer"
            className="amazon-btn-large"
          >
            Amazonで購入する →
          </a>
        </div>
      </div>

      <div className="detail-stats">
        <div className="stat-card">
          <span className="stat-value">{book.count}</span>
          <span className="stat-label">紹介回数</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{book.total_views.toLocaleString()}</span>
          <span className="stat-label">総再生回数</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{book.total_likes.toLocaleString()}</span>
          <span className="stat-label">総いいね数</span>
        </div>
      </div>

      <div className="book-summary-section">
        <h2>この本が選ばれる理由</h2>
        <p>{summaryText}</p>
      </div>

      {book.description && (
        <div className="book-description">
          <h2>本の内容</h2>
          <p>{book.description}</p>
        </div>
      )}

      {book.keywords && book.keywords.length > 0 && (
        <div className="book-keywords-section">
          <h2>キーワード</h2>
          <div className="book-keywords">
            {book.keywords.map(keyword => (
              <a key={keyword} href={`/?tag=${encodeURIComponent(keyword)}`} className="keyword-tag">
                {keyword}
              </a>
            ))}
          </div>
        </div>
      )}

      <h2>紹介動画一覧</h2>
      <div className="video-list">
        {book.videos.map(video => (
          <div key={video.video_id} className="video-card">
            <img
              src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
              alt={video.video_title}
              className="video-thumb"
              loading="lazy"
            />
            <div className="video-info">
              <a
                href={video.link}
                target="_blank"
                rel="noopener noreferrer"
                className="video-title"
              >
                {video.video_title}
              </a>
              <span className="video-channel">{video.channel}</span>
              <div className="video-stats">
                <span>再生 {video.view_count.toLocaleString()}</span>
                <span>いいね {video.like_count.toLocaleString()}</span>
                <span>{new Date(video.published).toLocaleDateString('ja-JP')}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="amazon-cta-section">
        <p className="amazon-cta-text">
          {book.count}人のYouTuberが推薦。気になったら今すぐチェック。
        </p>
        <a
          href={book.amazon_url}
          target="_blank"
          rel="noopener noreferrer"
          className="amazon-btn-large"
        >
          Amazonで購入する →
        </a>
      </div>

      {relatedByAuthor.length > 0 && (
        <section className="related-section">
          <h2>同じ著者の本</h2>
          <div className="related-grid">
            {relatedByAuthor.map(b => (
              <a key={b.id} href={`/book/${b.id}`} className="related-card">
                {b.image_url && (
                  <img src={b.image_url} alt={b.title} className="related-cover" loading="lazy" />
                )}
                <div className="related-info">
                  <p className="related-title">{b.title}</p>
                  <p className="related-stats">紹介 {b.count}回</p>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {relatedByCategory.length > 0 && topCategory && (
        <section className="related-section">
          <h2>同じジャンルの人気本（{topCategory}）</h2>
          <div className="related-grid">
            {relatedByCategory.map(b => (
              <a key={b.id} href={`/book/${b.id}`} className="related-card">
                {b.image_url && (
                  <img src={b.image_url} alt={b.title} className="related-cover" loading="lazy" />
                )}
                <div className="related-info">
                  <p className="related-title">{b.title}</p>
                  <p className="related-stats">紹介 {b.count}回</p>
                </div>
              </a>
            ))}
          </div>
          <a href={`/category/${categoryToSlug(topCategory)}`} className="category-link">
            {topCategory}の本をもっと見る →
          </a>
        </section>
      )}
    </div>
  )
}
