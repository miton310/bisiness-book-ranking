import channelsData from '../../public/data/channels.json'
import type { Channel } from '../../src/types'

export type Data = { channels: Channel[] }

export function data(): Data {
  return { channels: (channelsData as any).channels as Channel[] }
}
