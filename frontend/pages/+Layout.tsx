import type { ReactNode } from 'react'
import '../src/index.scss'

function TopLink({ children, className }: { children: ReactNode; className?: string }) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (typeof window !== 'undefined' && window.location.pathname === '/') {
      e.preventDefault()
      window.history.pushState({}, '', '/')
      window.dispatchEvent(new PopStateEvent('popstate'))
      window.scrollTo(0, 0)
    }
  }
  return <a href="/" className={className} onClick={handleClick}>{children}</a>
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="l-header__inner">
            <h1><TopLink className="site-title">社会人におすすめのビジネス書ランキング</TopLink></h1>
            <h2 className='p-header__title--sub'>
              - 社会人が今読むべきビジネス書をランキング化。YouTuberが紹介したおすすめ本やベストセラーを集計。人生に役立つイチオシの本を見つけて、効率的に学びましょう。
            </h2>
          </div>
          <nav className="nav">
            <TopLink>トップ</TopLink>
            <a href="/channels">チャンネル一覧</a>
          </nav>
        </div>
      </header>
      <main className="main container">
        {children}
      </main>
      <footer className="footer">
        <div className="container">
          <p>本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化</p>
        </div>
      </footer>
    </div>
  )
}
