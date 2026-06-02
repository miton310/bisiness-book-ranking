export function Head() {
  return (
    <>
      <meta charSet="UTF-8" />
      <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="author" content="ビジネス書ランキング運営チーム" />
      <meta name="robots" content="index, follow" />
      <meta property="og:site_name" content="社会人におすすめのビジネス書ランキング" />
      <meta property="og:locale" content="ja_JP" />
      <meta name="twitter:card" content="summary_large_image" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet" />
      <script async src="https://www.googletagmanager.com/gtag/js?id=G-MB6YFYL48Y"></script>
      <script dangerouslySetInnerHTML={{
        __html: `
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-MB6YFYL48Y');
        `
      }} />
    </>
  )
}
