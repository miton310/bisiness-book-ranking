import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchBookById } from '../data'
import type { Book } from '../types'

export function BookDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [book, setBook] = useState<Book | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    fetchBookById(id).then(data => {
      setBook(data)
      setLoading(false)
    })
  }, [id])

  if (loading) return <p>読み込み中...</p>
  if (!book) return <p>書籍が見つかりません。<Link to="/">トップに戻る</Link></p>

  return (
    <div>
      <Link to="/" className="back-link">← トップに戻る</Link>
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
            {book.publication_date && <p>出版日: {book.publication_date}</p>}
          </div>
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
      <a
        href={book.amazon_url}
        target="_blank"
        rel="noopener noreferrer"
        className="amazon-btn-large"
      >
        Amazonで探す
      </a>

      <h2>紹介動画一覧</h2>
      <div className="video-list">
        {book.videos.map(video => (
          <div key={video.video_id} className="video-card">
            <img
              src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
              alt={video.video_title}
              className="video-thumb"
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
    </div>
  )
}
