import { usePageContext } from 'vike-react/usePageContext'
import { useData } from 'vike-react/useData'
import type { Data } from './+data'

const FAQ_ITEMS = [
  {
    q: 'どうやってランキングを集計していますか？',
    a: '本要約チャンネル・サラタメさん・フェルミ漫画大学・学識サロン・アバタローなど人気の本要約系YouTubeチャンネルの動画概要欄を解析し、Amazonリンクから書籍情報を取得しています。各書籍が何本の動画で紹介されたか、紹介動画の総再生回数・いいね数を集計してランキングを作成しています。',
  },
  {
    q: '「ポイント順」とはどういう意味ですか？',
    a: '紹介したチャンネル数を重視したスコアです。1チャンネルが初めてその本を紹介すると5pt加算、同じチャンネルが2本目以降に紹介するたびに1pt加算されます。複数の独立したチャンネルが評価した本ほど高得点になります。',
  },
  {
    q: 'データはどのくらいの頻度で更新されますか？',
    a: 'YouTube Data APIを使用して定期的にデータを収集・更新しています。最新の動画情報が反映されるまで数日かかる場合があります。',
  },
  {
    q: 'どのジャンルのビジネス書が多いですか？',
    a: '人文・思想、ビジネス・経済、暮らし・健康・子育て、ノンフィクションのジャンルが多く登録されています。フィルター機能やジャンル別ページからお目当ての本を探せます。',
  },
  {
    q: 'Amazonのリンクはアフィリエイトリンクですか？',
    a: 'はい、当サイトのAmazonリンクはAmazonアソシエイトプログラムを利用したアフィリエイトリンクです。リンク経由で購入いただくと、サイト運営の収益になりますが、購入者の方のお支払い金額は変わりません。',
  },
]

export function Head() {
  const pageContext = usePageContext()
  const { rankings } = useData<Data>()
  const search = pageContext.urlParsed?.search ?? {}
  const noIndexKeys = ['sort', 'year', 'channel', 'pubYear', 'publisher', 'category', 'tag', 'q', 'page']
  const hasFilters = noIndexKeys.some(k => search[k] !== undefined && search[k] !== '')

  const description = '本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化。紹介回数・再生回数・いいね数でランキング。'
  const pageUrl = 'https://business.douga-summary.jp/'

  const itemListSchema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: '社会人におすすめのビジネス書ランキング',
    url: pageUrl,
    description,
    numberOfItems: rankings.length,
    itemListElement: rankings.slice(0, 10).map((b, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: b.title,
      url: `https://business.douga-summary.jp/book/${b.id}`,
    })),
  }

  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQ_ITEMS.map(item => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: { '@type': 'Answer', text: item.a },
    })),
  }

  return (
    <>
      {hasFilters && <meta name="robots" content="noindex,follow" />}
      <meta name="description" content={description} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content="https://business.douga-summary.jp/og-image.png" />
      <meta name="twitter:image" content="https://business.douga-summary.jp/og-image.png" />
      <link rel="canonical" href={pageUrl} />
      {!hasFilters && (
        <>
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListSchema) }}
          />
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
          />
        </>
      )}
    </>
  )
}
