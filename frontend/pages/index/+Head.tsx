import { usePageContext } from 'vike-react/usePageContext'

export function Head() {
  const pageContext = usePageContext()
  const search = pageContext.urlParsed?.search ?? {}
  // フィルター・ページネーション・検索パラメータが存在する場合はnoindex
  const noIndexKeys = ['sort', 'year', 'channel', 'pubYear', 'publisher', 'category', 'tag', 'q', 'page']
  const hasFilters = noIndexKeys.some(k => search[k] !== undefined && search[k] !== '')

  const description = '本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化。紹介回数・再生回数・いいね数でランキング。'
  const pageUrl = 'https://business.douga-summary.jp/'

  return (
    <>
      {hasFilters && <meta name="robots" content="noindex,follow" />}
      <meta name="description" content={description} />
      <meta property="og:title" content="社会人におすすめのビジネス書ランキング" />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
