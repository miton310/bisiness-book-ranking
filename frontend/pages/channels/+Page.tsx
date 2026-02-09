import { useData } from 'vike-react/useData'
import type { Data } from './+data'

export default function Page() {
  const { channels } = useData<Data>()

  return (
    <div>
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
