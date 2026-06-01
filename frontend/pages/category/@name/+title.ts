import type { PageContext } from 'vike/types'
import type { Data } from './+data'

export function title(pageContext: PageContext<Data>): string {
  const { categoryName, books } = pageContext.data ?? {}
  if (!categoryName) return 'ビジネス書ランキング'
  return `${categoryName}のおすすめビジネス書ランキング（${books?.length ?? 0}冊）- YouTuber紹介実績`
}
