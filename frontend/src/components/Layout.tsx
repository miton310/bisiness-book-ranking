import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>
            <Link to="/" className="site-title">
              ビジネス書ランキング - 本要約系YouTuberが紹介したビジネス書や人生に役に立つ本を集計・ランキング化
            </Link>
          </h1>
          <nav className="nav">
            <Link to="/">トップ</Link>
            <Link to="/ranking">ランキング</Link>
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
