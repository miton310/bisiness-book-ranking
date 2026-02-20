import rankingsData from '../../public/data/rankings.json'
import type { RankingEntry } from '../../src/types'

export type Data = { rankings: RankingEntry[] }

export function data(): Data {
  return { rankings: rankingsData as RankingEntry[] }
}
