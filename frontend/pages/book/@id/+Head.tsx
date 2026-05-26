import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export function Head() {
  const { book } = useData<Data>()

  if (!book) return null

  const description = `『${book.title}』${book.author ? `（${book.author}著）` : ''}はYouTuberに${book.count}回紹介された人気のビジネス書。社会人におすすめの一冊。総再生回数${book.total_views.toLocaleString()}回。`

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
