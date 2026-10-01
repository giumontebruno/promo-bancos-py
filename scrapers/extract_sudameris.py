import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


BASE = "https://www.sudameris.com.py"
START = f"{BASE}/beneficios"
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


def extract(session):
    html = get(session, START).text
    (WORK_DIR / "sudameris_beneficios.html").write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    links = []
    seen = set()
    for a in soup.select('a.link[href*="/beneficios/"][href$="/detalle"]'):
        url = urljoin(BASE, a.get("href"))
        if url not in seen:
            seen.add(url)
            links.append({"title": clean(a.get_text(" ")), "url": url})
    if not links:
        raise ValueError("Sudameris returned no promotion links")

    rows = []
    for item in links:
        resp = get(session, item["url"])
        detail_soup = BeautifulSoup(resp.text, "html.parser")
        description = detail_soup.select_one(".description-promo")
        raw_text = description.get_text("\n") if description else detail_soup.get_text("\n")
        text = clean(raw_text)
        title = clean((detail_soup.find(["h1", "h2", "h3", "h4"]) or {}).get_text(" ") if detail_soup.find(["h1", "h2", "h3", "h4"]) else item["title"])
        vigencia = section_after(raw_text, "VIGENCIA")
        beneficios = section_after(raw_text, "BENEFICIOS?")
        desde, hasta = extract_dates(vigencia)
        combined = f"{vigencia} {beneficios}"
        bases = [
            urljoin(BASE, a.get("href"))
            for a in detail_soup.select('a[href$=".pdf"], a[href*=".pdf?"]')
            if "Bases" in clean(a.get_text(" "))
        ]

        rows.append(
            {
                "Banco": "Sudameris",
                "Comercio/Promocion": title or item["title"],
                "Resumen cuadro": item["title"],
                "Vigencia": vigencia,
                "Desde": desde,
                "Hasta": hasta,
                "Beneficios": beneficios,
                "% detectado": extract_percent(combined),
                "Tope detectado": extract_tope(combined),
                "Cuotas detectadas": extract_cuotas(combined),
                "Bases y condiciones URL": "; ".join(dict.fromkeys(bases)),
                "URL": item["url"],
                "Texto completo": text,
            }
        )
        time.sleep(0.15)
    return rows


def main():
    OUT_DIR.mkdir(exist_ok=True)
    WORK_DIR.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        rows = extract(session)
    except (requests.RequestException, RuntimeError, ValueError):
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
