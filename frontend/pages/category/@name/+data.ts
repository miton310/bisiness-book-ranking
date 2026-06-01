import type { PageContextServer } from 'vike/types'
import booksData from '../../../public/data/books.json'
import type { Book } from '../../../src/types'
import { slugToCategory } from '../../../src/categorySlug'

export type Data = {
  categoryName: string
  books: Pick<Book, 'id' | 'title' | 'author' | 'publisher' | 'image_url' | 'count' | 'total_views' | 'total_likes' | 'amazon_url' | 'publication_date'>[]
}

export function data(pageContext: PageContextServer): Data {
  const slug = pageContext.routeParams?.name ?? ''
  const categoryName = slugToCategory(slug)
  const books = (booksData as Book[])
    .filter(b => b.category?.split(' > ')[0] === categoryName)
    .sort((a, b) => b.count - a.count)
    .map(({ id, title, author, publisher, image_url, count, total_views, total_likes, amazon_url, publication_date }) => ({
      id, title, author, publisher, image_url, count, total_views, total_likes, amazon_url, publication_date,
    }))

  return { categoryName, books }
}
