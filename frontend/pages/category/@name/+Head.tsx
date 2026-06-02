import { useData } from 'vike-react/useData'
import type { Data } from './+data'
import { categoryToSlug } from '../../../src/categorySlug'

export function Head() {
  const { categoryName, books } = useData<Data>()
  const pageUrl = `https://business.douga-summary.jp/category/${categoryToSlug(categoryName)}`
  const description = `${categoryName}のビジネス書ランキング。本要約系YouTuberが実際に動画で紹介した${books.length}冊を紹介回数・再生回数でランキング化。今読むべき一冊を見つけてください。`

  const listSchema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${categoryName}のビジネス書ランキング`,
    url: pageUrl,
    numberOfItems: books.length,
    itemListElement: books.slice(0, 10).map((b, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: b.title,
      url: `https://business.douga-summary.jp/book/${b.id}`,
    })),
  }

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content="https://business.douga-summary.jp/og-image.png" />
      <meta name="twitter:image" content="https://business.douga-summary.jp/og-image.png" />
      <link rel="canonical" href={pageUrl} />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(listSchema) }}
      />
    </>
  )
}
