export function Head() {
  const description = 'ビジネス書ランキングの運営方針・データ収集方法・ランキング集計ロジックについて。本要約系YouTuberの紹介動画をYouTube Data APIで集計し、公平なランキングを目指しています。'
  const pageUrl = 'https://business.douga-summary.jp/about'

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
