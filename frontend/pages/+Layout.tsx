import type { ReactNode } from 'react'
import '../src/index.scss'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="l-header__inner">
            <h1><a href="/" className="site-title">ビジネス書ランキング</a></h1>
            <h2 className='p-header__title--sub'>
              - 本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化
            </h2>
          </div>
          <nav className="nav">
            <a href="/">トップ</a>
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
