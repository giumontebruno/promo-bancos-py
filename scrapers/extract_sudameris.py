import csv
import json
import unicodedata
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


BASE = "https://www.sudameris.com.py"
START = f"{BASE}/personas/beneficios"
OUT_DIR = Path("outputs")
WORK_DIR = Path("work")


class BrowserResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if not 200 <= self.status_code < 300:
            raise RuntimeError(f"Sudameris HTTP {self.status_code}")


class BrowserSession:
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(channel="chrome", headless=False)
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        return self

    def __exit__(self, *_):
        self.browser.close()
        self.playwright.stop()

    def get(self, url, timeout=30):
        response = self.page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        return BrowserResponse(response.status if response else 599, self.page.content())


def get(session, url):
    last_error = None
    for attempt in range(3):
        try:
            response = session.get(url, timeout=45)
            response.raise_for_status()
            return response
        except (requests.RequestException, RuntimeError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise last_error


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def section_after(text, heading):
    pattern = rf"{heading}\s*(.*?)(?:VIGENCIA|BENEFICIOS?|Categorias|Contactos|Bases y Condiciones|Promociones relacionadas|Buscador de comercios|$)"
    match = re.search(pattern, text, flags=re.I | re.S)
    return clean(match.group(1)) if match else ""


def extract_dates(vigencia):
    desde = hasta = ""
    m = re.search(r"Desde el\s+(.+?)\s+hasta el\s+(.+?)(?:\.|$)", vigencia, re.I)
    if m:
        desde, hasta = clean(m.group(1)), clean(m.group(2))
    else:
        m = re.search(r"Hasta el\s+(.+?)(?:\.|$)", vigencia, re.I)
        if m:
            hasta = clean(m.group(1))
    return desde, hasta


def extract_percent(text):
    return "; ".join(sorted(set(re.findall(r"\d{1,3}\s*%", text))))


def extract_cuotas(text):
    values = re.findall(r"(?:hasta\s+)?\d+\s+cuotas?\s+sin\s+inter[eé]s(?:es)?", text, re.I)
    return "; ".join(dict.fromkeys(clean(v) for v in values))


def extract_tope(text):
    hits = re.findall(r"(?:tope[^.:\n]*[: ]\s*)?Gs\.?\s*[\d\.]+", text, re.I)
    return "; ".join(dict.fromkeys(clean(v) for v in hits if "Gs" in v))


def campaign_identity(title):
    value = ''.join(c for c in unicodedata.normalize('NFKD', title.upper()) if not unicodedata.combining(c))
    value = re.sub(r'[^A-Z0-9]+', ' ', value).strip()
    return 'GASTRONOMIA' if value == 'GASTRONOMIA 26' else value


def read_api(response):
    # Browser fallback wraps API JSON in a <pre> element.
    text = response.text
    if text.lstrip().startswith('<'):
        pre = BeautifulSoup(text, 'html.parser').find('pre')
        if not pre:
            raise ValueError('Sudameris API did not return JSON')
        text = pre.get_text()
    data = json.loads(text)
    if not isinstance(data.get('data'), list) or not isinstance(data.get('has_more'), bool):
        raise ValueError('Unexpected Sudameris pagination schema')
    return data


def current_offers(session):
    seen = set()
    offers = []
    for page in range(1, 101):
        batch = read_api(get(session, f'{BASE}/api/benefits?category=all&city=all&page={page}'))
        if batch.get('current_page') != page:
            raise ValueError('Sudameris returned an unexpected page')
        if batch['has_more'] and not batch['data']:
            raise ValueError('Sudameris returned an empty intermediate page')
        for item in batch['data']:
            if item['id'] in seen:
                raise ValueError('Sudameris repeated a promotion across pages')
            if not item['url'].startswith(BASE + '/personas/beneficios/'):
                raise ValueError('Unexpected Sudameris detail URL')
            seen.add(item['id'])
            offers.append(item)
        if not batch['has_more']:
            if not offers:
                raise ValueError('Sudameris returned no promotions')
            return offers
    raise ValueError('Sudameris pagination limit exceeded')


def extract(session):
    previous_path = OUT_DIR / 'sudameris_promociones.csv'
    previous = list(csv.DictReader(previous_path.open(encoding='utf-8-sig', newline=''))) if previous_path.exists() else []
    by_title = {}
    for old in previous:
        by_title.setdefault(campaign_identity(old['Comercio/Promocion']), []).append(old)
    rows = []
    for item in current_offers(session):
        soup = BeautifulSoup(get(session, item['url']).text, 'html.parser')
        description = soup.select_one('.benefit-description[data-raw-description]')
        if description is None and not soup.find('h1'):
            raise ValueError('Sudameris detail missing content: ' + item['url'])
        raw_text = description.get_text(' ', strip=True) if description else ' '.join(item.get('short_description_lines', []))
        print('Read official campaign:', item['title'], flush=True)
        bases = [urljoin(BASE, a['href']) for a in soup.select('a[href]')
                 if '.pdf' in a['href'].lower() and 'bases' in a.get_text(' ', strip=True).lower()]
        candidates = by_title.get(campaign_identity(item['title']), [])
        old = candidates[0] if len(candidates) == 1 else {}
        vigencia = clean(item.get('validity_text', ''))
        beneficios = clean(' '.join(item.get('short_description_lines', [])))
        desde, hasta = extract_dates(vigencia)
        rows.append({
            'Banco': 'Sudameris',
            'Comercio/Promocion': old.get('Comercio/Promocion', item['title']),
            'Resumen cuadro': item['title'], 'Vigencia': vigencia,
            'Desde': desde, 'Hasta': hasta, 'Beneficios': beneficios,
            '% detectado': extract_percent(beneficios),
            'Tope detectado': extract_tope(raw_text),
            'Cuotas detectadas': extract_cuotas(beneficios),
            'Bases y condiciones URL': '; '.join(dict.fromkeys(bases)),
            'URL': old.get('URL', item['url']),
            'URL fuente actual': item['url'],
            'Bases URL identidad': old.get('Bases URL identidad') or old.get('Bases y condiciones URL', ''),
            'Texto completo': clean(raw_text),
        })
    return rows


def main():
    OUT_DIR.mkdir(exist_ok=True)
    WORK_DIR.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        rows = extract(session)
    except (requests.RequestException, RuntimeError):
        with BrowserSession() as browser_session:
            rows = extract(browser_session)

    csv_path = OUT_DIR / "sudameris_promociones.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUT_DIR / "sudameris_promociones_resumen.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Sudameris promociones\n\nExtraidas desde {START}\n\nTotal: {len(rows)}\n\n")
        f.write("| Banco | Comercio/Promocion | Vigencia | Beneficios | URL |\n")
        f.write("|---|---|---|---|---|\n")
        for row in rows:
            f.write(
                "| "
                + " | ".join(
                    [
                        row["Banco"],
                        row["Comercio/Promocion"].replace("|", "/"),
                        row["Vigencia"].replace("|", "/")[:180],
                        row["Beneficios"].replace("|", "/")[:220],
                        row["URL"],
                    ]
                )
                + " |\n"
            )

    print(f"{len(rows)} promociones -> {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
