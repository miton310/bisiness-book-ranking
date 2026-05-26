import rankingsData from '../../public/data/rankings.json'
import type { RankingEntry } from '../../src/types'

export type Data = { rankings: RankingEntry[] }

export function data(): Data {
  // SSRは上位20件のみ返す（残りはクライアントサイドでfetchBooks()が取得）
  const top20 = (rankingsData as RankingEntry[]).slice(0, 20)
  return { rankings: top20 }
}
