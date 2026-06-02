export function Head() {
  const description = '書籍紹介系YouTubeチャンネルの一覧。本要約チャンネル、サラタメさん、フェルミ漫画大学など、ビジネス書を紹介する人気チャンネルを掲載。'
  const pageUrl = 'https://business.douga-summary.jp/channels'

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content="https://business.douga-summary.jp/og-image.png" />
      <meta name="twitter:image" content="https://business.douga-summary.jp/og-image.png" />
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
