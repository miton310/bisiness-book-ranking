export function Head() {
  const description = 'ビジネス書ランキングの運営方針・データ収集方法・ランキング集計ロジックについて。本要約系YouTuberの紹介動画をYouTube Data APIで集計し、公平なランキングを目指しています。'
  const pageUrl = 'https://business.douga-summary.jp/about'

  return (
    <>
      <meta name="description" content={description} />
      <meta property="og:title" content="このサイトについて - ビジネス書ランキング" />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
