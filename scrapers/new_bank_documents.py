"""Bounded official-document ingestion. Native text only; uncertain scopes are withheld from the consumer catalog.

Index discovery is complete; publication is deliberately narrower than discovery.
A successful HTTP request is not a claim that a bank's conditions were reviewed.
"""
import csv
import hashlib
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
MAX_DOCUMENTS = 750
MAX_BYTES = 12 * 1024 * 1024
MONTHS = dict(zip(('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre').split(), range(1, 13)))


def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def official_url(url, page):
    value = urljoin(page, url)
    if urlparse(value).scheme != 'https' or urlparse(value).hostname != urlparse(page).hostname:
        raise ValueError('Non-official document URL')
    return value


def download(url, page):
    official_url(url, page)
    # Redirects require validation BEFORE following, not after sending a request.
    for _ in range(4):
        with requests.get(url, timeout=(10, 40), stream=True, allow_redirects=False) as response:
            if response.is_redirect:
                url = official_url(response.headers['Location'], page)
                continue
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Document exceeds byte budget')
                chunks.append(chunk)
            return b''.join(chunks)
    raise ValueError('Too many redirects')


def document_provenance(url, blob, cache_path=None):
    digest = hashlib.sha256(blob).hexdigest()
    if cache_path is None:
        return {'url': url, 'sha256': digest, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'retrieval': 'live'}
    result = {'url': url, 'sha256': digest, 'fetched_at': None, 'retrieval': 'cache_replay',
              'cached_file_mtime': datetime.fromtimestamp(cache_path.stat().st_mtime, timezone.utc).isoformat()}
    sidecar = cache_path.with_suffix('.metadata.json')
    if sidecar.exists():
        try:
            saved = json.loads(sidecar.read_text())
            stamp = datetime.fromisoformat(saved['fetched_at'])
            if saved.get('url') == url and saved.get('sha256') == digest and stamp.tzinfo is not None:
                result['fetched_at'] = saved['fetched_at']
                result['retrieval_evidence'] = 'validated_download_sidecar'
        except (ValueError, KeyError, TypeError):
            pass
    if result['fetched_at'] is None:
        result['retrieval_evidence'] = 'cache_without_valid_download_timestamp'
    return result


def native_text(blob):
    if not blob.startswith(b'%PDF'):
        raise ValueError('Expected PDF')
    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        if len(pdf.pages) > 24:
            raise ValueError('Document exceeds page budget')
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
    if len(clean(text)) < 100:
        raise ValueError('Native text absent; image/OCR review required')
    if len(text) > 160000:
        raise ValueError('Document exceeds text budget')
    return text


def discover(html, bank, page):
    soup = BeautifulSoup(html, 'html.parser')
    result, seen = [], set()
    if bank == 'basa':
        candidates = [(a.get_text(' ', strip=True), a.get('href'), '') for a in soup.select('.promo-grid a[href]') if '.pdf' in a['href'].lower()]
    else:
        candidates = []
        for card in soup.select('.cards-con-modal-item'):
            name, link = card.select_one('.text-uppercase'), card.select_one('a[href]')
            if name and link:
                candidates.append((name.get_text(' ', strip=True), link['href'], card.get_text(' ', strip=True)))
    categories = {}
    if bank == 'interfisa':
        for card in soup.select('.cards-con-modal-item'):
            link, heading = card.select_one('a[href]'), card.find_previous('h1')
            if link and heading:
                categories[urljoin(page, link['href'])] = heading.get_text(' ', strip=True)
    for name, url, caption in candidates:
        if '.pdf' not in url.lower():
            continue
        url = urljoin(page, url)
        key = (clean(name), url)
        if key in seen:
            continue
        seen.add(key)
        result.append({'name': key[0], 'url': url, 'caption': clean(caption), 'category': categories.get(url, 'Sin categoría'), 'key': hashlib.sha256(url.encode()).hexdigest()[:16]})
    if not result or len(result) > MAX_DOCUMENTS:
        raise ValueError('Unexpected official index size; previous export preserved')
    return result


def numeric_dates(text):
    result = []
    for day, month, year in re.findall(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', text):
        result.append(date(int(year), int(month), int(day)))
    return result


def row(bank, item, text, benefit, cards, day, start, end, caps, variant='base', category='Sin categoría', locations='', detail=None):
    return {'Banco': bank, 'Categoría': category, 'Comercio/Promoción': item['name'],
            'Cantidad de descuento / beneficio': benefit, 'Día de promoción': day,
            'Vigencia': f'Desde {start.isoformat()} hasta {end.isoformat()}' if start else f'Hasta {end.isoformat()}',
            'Montos / topes': caps, 'Tarjetas verificadas': cards, 'Detalle': clean(detail or text),
            'Locales': locations, 'Ciudad': 'No especificado', 'URL detalle': item['url'],
            'Variante': variant, 'Texto original de la fuente': clean(text),
            'Estado verificacion': 'official_document', 'SHA256 documento': item.get('sha256', ''),
            'Verificado UTC': item.get('fetched_at', ''), 'Topes revisados por variante': 'yes'}


def run(bank, page, parser, *, cache=None, html=None, today=None):
    today = today or datetime.now(timezone(timedelta(hours=-3))).date()
    fetched_at = datetime.now(timezone.utc).isoformat()
    html = html if html is not None else download(page, page).decode('utf-8')
    items = discover(html, bank, page)
    work = ROOT / 'work' / f'{bank}_documents'
    work.mkdir(parents=True, exist_ok=True)
    (work / 'index.html').write_text(html, encoding='utf-8')
    cache = Path(cache) if cache else None
    def get(item):
        try:
            official_url(item['url'], page)
            path = cache / (item['key'] + '.pdf') if cache else None
            blob = path.read_bytes() if path and path.exists() else download(item['url'], page)
            if len(blob) > MAX_BYTES:
                raise ValueError('Document exceeds byte budget')
            provenance = document_provenance(item['url'], blob, path if path and path.exists() else None)
            item.update(provenance)
            output_path = work / (item['key'] + '.pdf')
            output_path.write_bytes(blob)
            output_path.with_suffix('.metadata.json').write_text(json.dumps(provenance, ensure_ascii=False), encoding='utf-8')
            text = native_text(blob)
            item['native_text_sha256'] = hashlib.sha256(text.encode()).hexdigest()
            (work / (item['key'] + '.txt')).write_text(text, encoding='utf-8')
            # Save native text and exact byte hash, not OCR guesses or fabricated terms.
            rows, state = parser(item, text, today)
            return item, rows, state
        except Exception as exc:
            return item, [], 'fetch_or_parse_error: ' + str(exc)[:200]
    # The index is finite. Three concurrent requests; no recursion, logins or retries.
    rows, states = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for item, published, state in pool.map(get, items):
            rows.extend(published)
            states.append({**item, 'state': state, 'published_rows': len(published)})
    meta = {'bank': bank, 'source_page': page, 'attempted_at': fetched_at, 'cache_replay': bool(cache),
            'discovered': len(items), 'unique_documents': len({x['url'] for x in items}),
            'fetched': len({x['url'] for x in states if 'sha256' in x}), 'fetched_records': sum('sha256' in x for x in states), 'published_rows': len(rows), 'published_documents': sum(x['published_rows'] > 0 for x in states),
            'native_text_documents': len({x['url'] for x in states if 'native_text_sha256' in x}),
            'fetch_errors': len({x['url'] for x in states if 'sha256' not in x}),
            'expired': sum(x['state'] == 'expired' for x in states),
            'pending': sum(x['state'] not in ('published', 'expired') for x in states),
            'documents': states}
    meta['published_unconfirmed_rows'] = sum(item.get('Estado verificacion') == 'unconfirmed' for item in rows)
    meta['published_confirmed_rows'] = len(rows) - meta['published_unconfirmed_rows']
    meta['status'] = 'partial' if meta['pending'] else 'fetched'
    outputs = ROOT / 'outputs'; outputs.mkdir(exist_ok=True)
    (outputs / f'{bank}_source_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    if not rows:
        raise RuntimeError('No publishable verified documents; previous CSV preserved; inspect source meta')
    for item in rows:
        item['URL fuente actual'] = page
    target = outputs / f'{bank}_beneficios_por_categoria.csv'
    temp = target.with_suffix('.csv.tmp')
    fields = list(dict.fromkeys(key for item in rows for key in item))
    with temp.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    temp.replace(target)
    print(json.dumps({key: value for key, value in meta.items() if key != 'documents'}, ensure_ascii=False))
    return rows, meta
