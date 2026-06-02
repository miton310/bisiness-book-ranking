export function Head() {
  const description = 'ビジネス書ランキングのプライバシーポリシー。アクセス解析（Google Analytics）、Cookie、Amazonアソシエイト等のアフィリエイトプログラムの利用について記載しています。'
  const pageUrl = 'https://business.douga-summary.jp/privacy'

  return (
    <>
      <meta name="description" content={description} />
      <meta name="robots" content="noindex,follow" />
      <meta property="og:title" content="プライバシーポリシー - ビジネス書ランキング" />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <link rel="canonical" href={pageUrl} />
    </>
  )
}
