import books from '../../../public/data/books.json'

export async function onBeforePrerenderStart() {
  return books.map((book: { id: string }) => `/book/${book.id}`)
}
