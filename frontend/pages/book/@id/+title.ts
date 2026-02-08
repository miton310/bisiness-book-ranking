import type { PageContext } from 'vike/types'
import type { Data } from './+data'

export function title(pageContext: PageContext<Data>): string {
  const book = pageContext.data?.book
  if (!book) return 'ビジネス書ランキング'
  return `${book.title} - ビジネス書ランキング`
}
