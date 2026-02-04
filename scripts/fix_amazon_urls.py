#!/usr/bin/env python3
"""既存のbooks.jsonのamazon_urlをISBN-13からASINに修正"""

import json

def isbn13_to_asin(isbn13):
    src = str(isbn13).replace('-', '')
    if len(src) != 13 or not src.startswith('978'):
        return None
    core = src[3:12]
    total = sum(int(d) * (10 - i) for i, d in enumerate(core))
    remainder = total % 11
    check_digit = 11 - remainder
    if check_digit == 11:
        cd_str = '0'
    elif check_digit == 10:
        cd_str = 'X'
    else:
        cd_str = str(check_digit)
    return core + cd_str

AMAZON_TRACKING_ID = 'business-book-ranking02-22'

with open('data/books.json') as f:
    books = json.load(f)

fixed = 0
for book in books:
    isbn = book.get('isbn')
    if not isbn:
        continue

    url = book.get('amazon_url', '')
    # ISBN-13がURLに入っている場合を修正
    if f'/dp/{isbn}' in url:
        asin = isbn13_to_asin(isbn)
        if asin:
            book['asin'] = asin
            book['amazon_url'] = f'https://www.amazon.co.jp/dp/{asin}?tag={AMAZON_TRACKING_ID}'
            fixed += 1

with open('data/books.json', 'w') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f'修正: {fixed}件')
