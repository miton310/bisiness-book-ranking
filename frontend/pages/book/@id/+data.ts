import type { PageContextServer } from 'vike/types'
import booksData from '../../../public/data/books.json'
import type { Book } from '../../../src/types'

export type Data = {
  book: Book | null
  relatedByAuthor: Pick<Book, 'id' | 'title' | 'author' | 'image_url' | 'count' | 'total_views'>[]
  relatedByCategory: Pick<Book, 'id' | 'title' | 'author' | 'image_url' | 'count' | 'total_views'>[]
}

export function data(pageContext: PageContextServer): Data {
  const id = pageContext.routeParams?.id
  const books = booksData as Book[]
  const book = books.find(b => b.id === id) || null

  if (!book) return { book: null, relatedByAuthor: [], relatedByCategory: [] }

  const topCategory = book.category?.split(' > ')[0] ?? null

  const relatedByAuthor = book.author
    ? books
        .filter(b => b.id !== book.id && b.author === book.author)
        .sort((a, b) => b.count - a.count)
        .slice(0, 5)
        .map(({ id, title, author, image_url, count, total_views }) => ({ id, title, author, image_url, count, total_views }))
    : []

  const relatedByCategory = topCategory
    ? books
        .filter(b => b.id !== book.id && b.category?.startsWith(topCategory) && b.author !== book.author)
        .sort((a, b) => b.count - a.count)
        .slice(0, 6)
        .map(({ id, title, author, image_url, count, total_views }) => ({ id, title, author, image_url, count, total_views }))
    : []

  return { book, relatedByAuthor, relatedByCategory }
}
