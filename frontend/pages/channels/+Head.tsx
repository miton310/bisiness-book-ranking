export function Head() {
  const description = '書籍紹介系YouTubeチャンネルの一覧。本要約チャンネル、サラタメさん、フェルミ漫画大学など、ビジネス書を紹介する人気チャンネルを掲載。'
  const pageUrl = 'https://business.douga-summary.jp/channels'

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:title" content="チャンネル一覧 - ビジネス書ランキング" />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
