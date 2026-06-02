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
            <div className="site-title-wrap"><TopLink className="site-title">社会人におすすめのビジネス書ランキング</TopLink></div>
            <p className='p-header__title--sub'>
              YouTuberの紹介データで選ぶ、今読むべきビジネス書
            </p>
          </div>
          <nav className="nav">
            <TopLink>トップ</TopLink>
            <a href="/channels">チャンネル一覧</a>
            <a href="/category/business">ビジネス・経済</a>
            <a href="/category/humanities">人文・思想</a>
            <a href="/category/lifestyle">健康・子育て</a>
          </nav>
        </div>
      </header>
      <main className="main container">
        {children}
      </main>
      <footer className="footer">
        <div className="container">
          <nav className="footer-nav">
            <a href="/about">このサイトについて</a>
            <a href="/privacy">プライバシーポリシー</a>
            <a href="/channels">チャンネル一覧</a>
          </nav>
          <p>本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化</p>
        </div>
      </footer>
    </div>
  )
}
