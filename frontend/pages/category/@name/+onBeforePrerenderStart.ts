import booksData from '../../../public/data/books.json'
import type { Book } from '../../../src/types'
import { categoryToSlug } from '../../../src/categorySlug'

export function onBeforePrerenderStart() {
  const categories = [...new Set(
    (booksData as Book[])
      .map(b => b.category?.split(' > ')[0])
      .filter((c): c is string => !!c)
  )]
  return categories.map(name => `/category/${categoryToSlug(name)}`)
}
