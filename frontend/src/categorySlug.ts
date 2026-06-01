export const CATEGORY_SLUG: Record<string, string> = {
  '人文・思想': 'humanities',
  'ビジネス・経済': 'business',
  '暮らし・健康・子育て': 'lifestyle',
  'ノンフィクション': 'nonfiction',
  '社会・政治': 'society',
  '投資・金融・会社経営': 'investment',
  '文学・評論': 'literature',
  '科学・テクノロジー': 'science',
  '趣味・実用': 'hobby',
  '歴史・地理': 'history',
  'アート・建築・デザイン': 'art',
  'コンピュータ・IT': 'technology',
  'スポーツ・アウトドア': 'sports',
  '教育・学参・受験': 'education',
  '児童書': 'childrens',
  '語学・辞事典・年鑑': 'language',
}

export const SLUG_TO_CATEGORY: Record<string, string> = Object.fromEntries(
  Object.entries(CATEGORY_SLUG).map(([cat, slug]) => [slug, cat])
)

export function categoryToSlug(category: string): string {
  return CATEGORY_SLUG[category] ?? encodeURIComponent(category)
}

export function slugToCategory(slug: string): string {
  return SLUG_TO_CATEGORY[slug] ?? decodeURIComponent(slug)
}
