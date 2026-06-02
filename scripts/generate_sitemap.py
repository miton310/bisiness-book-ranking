#!/usr/bin/env python3
"""
Generate sitemap.xml for the business book ranking site
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def get_book_lastmod(book: dict) -> str:
    """最新の紹介動画日付をlastmodとして返す。なければ今日の日付。"""
    dates = [v.get("published", "") for v in book.get("videos", []) if v.get("published")]
    if dates:
        latest = max(dates)
        return latest[:10]  # YYYY-MM-DD
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate_sitemap():
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / "books.json", "r", encoding="utf-8") as f:
        books = json.load(f)

    base_url = "https://business.douga-summary.jp"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # 静的ページ
    static_pages = [
        {"loc": "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "/channels", "priority": "0.8", "changefreq": "weekly"},
    ]
    for page in static_pages:
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{base_url}{page['loc']}</loc>")
        sitemap.append(f"    <lastmod>{today}</lastmod>")
        sitemap.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        sitemap.append(f"    <priority>{page['priority']}</priority>")
        sitemap.append("  </url>")

    # カテゴリページ（ASCIIスラッグ使用）
    CATEGORY_SLUG = {
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
    categories = sorted(set(
        b.get("category", "").split(" > ")[0]
        for b in books
        if b.get("category")
    ))
    for cat in categories:
        slug = CATEGORY_SLUG.get(cat, cat)
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{base_url}/category/{slug}</loc>")
        sitemap.append(f"    <lastmod>{today}</lastmod>")
        sitemap.append(f"    <changefreq>weekly</changefreq>")
        sitemap.append(f"    <priority>0.8</priority>")
        sitemap.append("  </url>")

    # 書籍詳細ページ（lastmodを動的に設定）
    for book in books:
        book_id = book.get("id")
        if book_id:
            lastmod = get_book_lastmod(book)
            sitemap.append("  <url>")
            sitemap.append(f"    <loc>{base_url}/book/{book_id}</loc>")
            sitemap.append(f"    <lastmod>{lastmod}</lastmod>")
            sitemap.append(f"    <changefreq>weekly</changefreq>")
            sitemap.append(f"    <priority>0.7</priority>")
            sitemap.append("  </url>")

    sitemap.append("</urlset>")

    output_path = Path(__file__).parent.parent / "frontend" / "public" / "sitemap.xml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))

    total = len(static_pages) + len(categories) + len(books)
    print(f"✓ Sitemap generated: {output_path}")
    print(f"  Static: {len(static_pages)}, Categories: {len(categories)}, Books: {len(books)}, Total: {total}")


if __name__ == "__main__":
    generate_sitemap()
