import type { Book, RankingEntry } from './types'

const BASE = import.meta.env.BASE_URL + 'data'

export async function fetchRankings(): Promise<RankingEntry[]> {
  const res = await fetch(`${BASE}/rankings.json`)
  return res.json()
}

export async function fetchRankingsViews(): Promise<RankingEntry[]> {
  const res = await fetch(`${BASE}/rankings_views.json`)
  return res.json()
}

export async function fetchRankingsLikes(): Promise<RankingEntry[]> {
  const res = await fetch(`${BASE}/rankings_likes.json`)
  return res.json()
}

export async function fetchBooks(): Promise<Book[]> {
  const res = await fetch(`${BASE}/books.json`)
  return res.json()
}

export async function fetchBookById(id: string): Promise<Book | null> {
  const books = await fetchBooks()
  return books.find(b => b.id === id) || null
}
