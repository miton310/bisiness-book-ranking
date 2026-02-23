import type { Config } from 'vike/types'
import vikeReact from 'vike-react/config'

export default {
  extends: [vikeReact],
  ssr: true,
  prerender: true,
} satisfies Config
