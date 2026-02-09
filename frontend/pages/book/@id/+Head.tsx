import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export function Head() {
  const { book } = useData<Data>()

  if (!book) return null

  const description = [
    `『${book.title}』`,
    book.author && `著者: ${book.author}`,
    book.publisher && `出版社: ${book.publisher}`,
    `${book.count}回紹介`,
    `総再生回数: ${book.total_views.toLocaleString()}`,
  ].filter(Boolean).join(' | ')

  const pageUrl = `https://business.douga-summary.jp/book/${book.id}`

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:title" content={`${book.title} - ビジネス書ランキング`} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      {book.image_url && <meta property="og:image" content={book.image_url} />}
      <meta property="og:type" content="article" />
      <meta name="twitter:card" content={book.image_url ? 'summary_large_image' : 'summary'} />
      <meta name="twitter:title" content={`${book.title} - ビジネス書ランキング`} />
      <meta name="twitter:description" content={description} />
      {book.image_url && <meta name="twitter:image" content={book.image_url} />}
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
