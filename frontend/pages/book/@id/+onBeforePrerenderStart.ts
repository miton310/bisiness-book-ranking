import booksData from '../../../public/data/books.json'

export function onBeforePrerenderStart() {
  const books = booksData as { id: string }[]
  return books.map(book => `/book/${book.id}`)
}
