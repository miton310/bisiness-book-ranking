import type { PageContextServer } from 'vike/types'
import booksData from '../../../public/data/books.json'
import type { Book } from '../../../src/types'

export type Data = { book: Book | null }

export function data(pageContext: PageContextServer): Data {
  const id = pageContext.routeParams?.id
  const book = (booksData as Book[]).find(b => b.id === id) || null
  return { book }
}
