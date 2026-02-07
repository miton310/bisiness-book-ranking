export interface Video {
  video_id: string
  video_title: string
  channel: string
  link: string
  published: string
  view_count: number
  like_count: number
}

export interface Book {
  id: string
  title: string
  author: string | null
  publisher: string | null
  amazon_url: string
  count: number
  total_views: number
  total_likes: number
  videos: Video[]
  image_url?: string
  publication_date?: string
  isbn?: string
}

export interface Channel {
  name: string
  channel_id: string
  subscribers: string
  note: string
}

export interface RankingEntry {
  id: string
  title: string
  author: string | null
  count: number
  total_views: number
  total_likes: number
  amazon_url: string
  image_url?: string
  publisher?: string
  publication_date?: string
}
