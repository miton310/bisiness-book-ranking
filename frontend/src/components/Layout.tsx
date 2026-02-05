import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="l-header__inner">
            <h1><Link to="/" className="site-title">ビジネス書ランキング</Link></h1>
            <h2 className='p-header__title--sub'>
              - 本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化
            </h2>         
          </div>
          <nav className="nav">
            <Link to="/">トップ</Link>
            <Link to="/channels">チャンネル一覧</Link>
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
