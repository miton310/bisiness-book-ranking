import fs from 'fs'
import path from 'path'

export async function onBeforePrerenderStart() {
  const dataPath = path.join(process.cwd(), 'public', 'data', 'books.json')
  const books = JSON.parse(fs.readFileSync(dataPath, 'utf-8'))

  return books.map((book: { id: string }) => `/book/${book.id}`)
}
