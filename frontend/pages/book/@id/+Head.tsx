import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export function Head() {
  const { book } = useData<Data>()

  if (!book) return null

  const channels = [...new Set(book.videos.map(v => v.channel))]
  const channelStr = channels.slice(0, 2).join('・') + (channels.length > 2 ? `など${channels.length}チャンネル` : '')
  const description = [
    `『${book.title}』を${channelStr}が紹介。`,
    book.author && `著者: ${book.author}。`,
    `YouTuber ${book.count}回紹介、総再生回数${Math.round(book.total_views / 10000)}万回。`,
    `Amazonで購入・詳細を確認。`,
  ].filter(Boolean).join('')

  const pageUrl = `https://business.douga-summary.jp/book/${book.id}`

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:title" content={`${book.title}${book.author ? ` - ${book.author}` : ''} | 社会人におすすめのビジネス書`} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      {book.image_url && <meta property="og:image" content={book.image_url} />}
      <meta property="og:type" content="article" />
      <meta name="twitter:card" content={book.image_url ? 'summary_large_image' : 'summary'} />
      <meta name="twitter:title" content={`${book.title}${book.author ? ` - ${book.author}` : ''} | 社会人におすすめのビジネス書`} />
      <meta name="twitter:description" content={description} />
      {book.image_url && <meta name="twitter:image" content={book.image_url} />}
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
