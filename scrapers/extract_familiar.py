"""Capture official Familiar cards for review before catalog publication."""
import hashlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import pdfplumber
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
START = 'https://www.familiar.com.py/promociones-tarjetas'


def parse_cards(html, source=START):
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for item in soup.select('.promotions-collection-item'):
        name = item.select_one('[fs-list-field="name"]')
        link = item.select_one('a[href*="/pdfs/"]')
        if not name or not link:
            continue
        day = item.select_one('[fs-list-field="description"]')
        end = item.select_one('.end-date')
        rows.append({
            'bank': 'Familiar', 'merchant_name': name.get_text(' ', strip=True),
            'day_text': day.get_text(' ', strip=True) if day else '',
            'benefit_summary': '; '.join(n.get_text(' ', strip=True) for n in item.select('div.text-s') if n.get_text(strip=True)),
            'validity_raw': end.get_text(' ', strip=True) if end else '',
            'categories': [n.get_text(' ', strip=True) for n in item.select('[fs-list-field="category"]')],
            'regions': [n.get_text(' ', strip=True) for n in item.select('[fs-list-field="locations"]')],
            'source_url': urljoin(source, link['href']), 'listing_url': source,
            'review_status': 'pending_terms_review',
        })
    next_link = soup.select_one('a.w-pagination-next[href]')
    return rows, urljoin(source, next_link['href']) if next_link else None


def terms_pdf(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('iframe[src]'):
        value = parse_qs(urlparse(node['src']).query).get('url', [''])[0]
        if urlparse(value).hostname == 'cdn.prod.website-files.com' and urlparse(value).path.lower().endswith('.pdf'):
            return value
    return None


def main():
    session = requests.Session()
    url, seen, records, terms = START, set(), {}, {}
    while url and url not in seen:
        if urlparse(url).hostname != 'www.familiar.com.py' or len(seen) >= 50:
            raise ValueError('Unexpected Familiar pagination')
        response = session.get(url, timeout=30)
        response.raise_for_status()
        rows, following = parse_cards(response.content, url)
        if not rows:
            raise ValueError('Familiar returned no cards; previous extraction preserved')
        for row in rows:
            records[(row['merchant_name'], row['source_url'])] = row
        seen.add(url)
        url = following
        time.sleep(.2)
    for row in records.values():
        source = row['source_url']
        if source not in terms:
            try:
                response = session.get(source, timeout=30)
                response.raise_for_status()
                pdf_url = terms_pdf(response.content)
                if not pdf_url:
                    raise ValueError('No official terms PDF')
                pdf_response = session.get(pdf_url, timeout=30)
                pdf_response.raise_for_status()
                if not pdf_response.content.startswith(b'%PDF') or len(pdf_response.content) > 15_000_000:
                    raise ValueError('Invalid terms document')
                with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
                    text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
                terms[source] = {'pdf_url':pdf_url, 'pdf_sha256':hashlib.sha256(pdf_response.content).hexdigest(), 'terms_text':text}
            except (requests.RequestException, ValueError) as error:
                terms[source] = {'terms_error':type(error).__name__}
            time.sleep(.2)
        row.update(terms[source])
    output = ROOT / 'outputs/familiar_extraction_review.json'
    output.write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(), 'pages':len(seen), 'records':list(records.values())}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Familiar: {len(records)} cards, {len(seen)} pages; {sum("terms_text" in r for r in records.values())} with terms. Pending review, not published.')


if __name__ == '__main__':
    main()
