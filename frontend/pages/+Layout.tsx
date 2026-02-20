import type { ReactNode } from 'react'
import '../src/index.scss'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div className="l-header__inner">
            <h1><a href="/" className="site-title">社会人におすすめのビジネス書ランキング</a></h1>
            <h2 className='p-header__title--sub'>
              - 社会人が今読むべきビジネス書をランキング化。YouTuberが紹介したおすすめ本やベストセラーを集計。人生に役立つイチオシの本を見つけて、効率的に学びましょう。
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
          <p>YouTuberが紹介した社会人におすすめのビジネス書や人生に役立つ本を集計・ランキング化</p>
        </div>
      </footer>
    </div>
  )
}
