import { useEffect, useState } from 'react'
import { fetchChannels } from '../data'
import type { Channel } from '../types'

export function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchChannels()
      .then(data => {
        setChannels(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch data:', err)
        setLoading(false)
      })
  }, [])

  if (loading) return <p>読み込み中...</p>

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
