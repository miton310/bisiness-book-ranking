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
}

export interface RankingEntry {
  id: string
  title: string
  author: string | null
  count: number
  total_views: number
  total_likes: number
  amazon_url: string
}
