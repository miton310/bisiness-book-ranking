import type { PageContext } from 'vike/types'
import type { Data } from './+data'

export function title(pageContext: PageContext<Data>): string {
  const book = pageContext.data?.book
  if (!book) return '社会人におすすめのビジネス書ランキング'
  const author = book.author ? ` - ${book.author}` : ''
  return `${book.title}${author} | 社会人におすすめのビジネス書ランキング`
}
