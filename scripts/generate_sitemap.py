#!/usr/bin/env python3
"""
Generate sitemap.xml for the business book ranking site
"""
import json
from datetime import datetime
from pathlib import Path

def generate_sitemap():
    # Load books data
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / "books.json", "r", encoding="utf-8") as f:
        books = json.load(f)
    
    # Base URL - update this to your actual domain
    base_url = "https://business.douga-summary.jp"
    
    # Current date for lastmod
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Start XML
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Add static pages
    static_pages = [
        {"loc": "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "/ranking/", "priority": "0.9", "changefreq": "daily"},
        {"loc": "/channels", "priority": "0.8", "changefreq": "weekly"},
    ]
    
    for page in static_pages:
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{base_url}{page['loc']}</loc>")
        sitemap.append(f"    <lastmod>{today}</lastmod>")
        sitemap.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        sitemap.append(f"    <priority>{page['priority']}</priority>")
        sitemap.append("  </url>")
    
    # Add book detail pages
    for book in books:
        book_id = book.get("id")
        if book_id:
            sitemap.append("  <url>")
            sitemap.append(f"    <loc>{base_url}/book/{book_id}</loc>")
            sitemap.append(f"    <lastmod>{today}</lastmod>")
            sitemap.append(f"    <changefreq>weekly</changefreq>")
            sitemap.append(f"    <priority>0.7</priority>")
            sitemap.append("  </url>")
    
    # Close XML
    sitemap.append("</urlset>")
    
    # Write sitemap
    output_path = Path(__file__).parent.parent / "frontend" / "public" / "sitemap.xml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))
    
    print(f"✓ Sitemap generated: {output_path}")
    print(f"  Total URLs: {len(static_pages) + len(books)}")

if __name__ == "__main__":
    generate_sitemap()
