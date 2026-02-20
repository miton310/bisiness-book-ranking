import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export default function Page() {
  const { channels } = useData<Data>()

  // 構造化データ（JSON-LD）
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "ビジネス書を紹介するYouTubeチャンネル一覧",
    "description": "社会人におすすめのビジネス書を紹介しているYouTubeチャンネル",
    "numberOfItems": channels.length,
    "itemListElement": channels.map((ch, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "item": {
        "@type": "Organization",
        "name": ch.name,
        "url": `https://www.youtube.com/channel/${ch.channel_id}`,
      }
    }))
  }

  const breadcrumbData = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://business.douga-summary.jp/" },
      { "@type": "ListItem", "position": 2, "name": "チャンネル一覧", "item": "https://business.douga-summary.jp/channels" }
    ]
  }

  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbData) }}
      />
      <h2 className="page-heading">チャンネル一覧</h2>
      <p className="subtitle">書籍紹介系YouTubeチャンネル: {channels.length}件</p>
      <div className="channel-list">
        {channels.map(ch => (
          <div key={ch.channel_id} className="channel-card">
            <div className="channel-info">
              <h3 className="channel-name">{ch.name}</h3>
              <p className="channel-subscribers">登録者数: {ch.subscribers}</p>
              {ch.note && <p className="channel-note">{ch.note}</p>}
            </div>
            <a
              href={`https://www.youtube.com/channel/${ch.channel_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="youtube-btn"
            >
              YouTube
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
