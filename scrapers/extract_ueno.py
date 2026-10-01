"""Discover and extract the current UENO benefit PDFs by category."""

import calendar
import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pdfplumber
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_URL = "https://www.ueno.com.py/beneficios-sitemap.xml"
WORK_DIR = ROOT / "work/ueno_monthly_pdfs"
MANIFEST_PATH = ROOT / "work/ueno_monthly_sources.json"
RAW_CSV = ROOT / "work/ueno_monthly_index.csv"
OUT_CSV = ROOT / "outputs/ueno_beneficios_por_categoria.csv"
OUT_MD = ROOT / "outputs/ueno_beneficios_por_categoria.md"

MONTH_SLUGS = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}
CATEGORIES = {
    "supermercados": "Supermercados",
    "combustibles": "Combustible",
    "petropar": "Combustible",
    "farmacias": "Farmacias",
    "gastronomia": "Gastronomía",
    "black-gastronomia": "Gastronomía",
    "la-cuadrita": "Gastronomía",
    "black-la-cuadrita": "Gastronomía",
    "clubes": "Clubes sociales",
    "club-cerro": "Clubes sociales",
    "club-olimpia": "Clubes sociales",
    "deportes": "Entretenimiento",
    "entretenimiento": "Entretenimiento",
    "hoteles": "Viajes",
    "agencias-de-viajes": "Viajes",
    "bienestar": "Salud y belleza",
    "black-bienestar": "Salud y belleza",
    "optica-luce": "Salud y belleza",
    "depyless": "Salud y belleza",
    "pilates-by-depyless": "Salud y belleza",
    "escuela-judicial": "Servicios",
    "prosegur": "Servicios",
    "pagopar": "Servicios",
    "cuotas-sin-intereses": "Cuotas sin intereses",
    "cuotas-ueno-black": "Cuotas sin intereses",
    "umarket-cuotas": "Cuotas sin intereses",
    "cuotas-alula": "Cuotas sin intereses",
    "rakiura-cuotas": "Cuotas sin intereses",
    "black-viajes": "Viajes",
    "plataformas-black": "Entretenimiento",
    "black-tiendas": "Tiendas",
    "black-souk": "Tiendas",
    "black-free-spirit": "Tiendas",
    "black-dellapoletti": "Tiendas",
    "black-sax": "Tiendas",
}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def current_period(today=None):
    today = today or date.today()
    return f"{MONTH_SLUGS[today.month]}{today.year}", today


def session():
    client = requests.Session()
    client.headers.update({"User-Agent": "Mozilla/5.0 (compatible; PaybackPY/1.0; promotion catalog)"})
    return client


def discover_sources(client, today=None):
    period, today = current_period(today)
    response = client.get(SITEMAP_URL, timeout=40)
    response.raise_for_status()
    urls = re.findall(r"<loc>(.*?)</loc>", response.text, flags=re.I)
    page_urls = [url for url in urls if f"/beneficio-byc/{period}/" in url and url.rstrip("/").split("/")[-1] != period]
    sources = []
    for page_url in page_urls:
        page = client.get(page_url, timeout=40)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        candidates = []
        for tag in soup.select("[href], [src], [data]"):
            for attribute in ("href", "src", "data"):
                value = tag.get(attribute)
                if value and re.search(r"\.pdf(?:$|[?#])", value, flags=re.I):
                    candidates.append(urljoin(page.url, value))
        if not candidates:
            continue
        slug = urlparse(page_url).path.rstrip("/").split("/")[-1]
        title = clean(soup.title.get_text(" ") if soup.title else slug.replace("-", " ").title())
        title = re.sub(r"\s*-\s*ueno\s*-\s*Banco Digital.*$", "", title, flags=re.I)
        sources.append({
            "index": len(sources) + 1,
            "period": period,
            "slug": slug,
            "category": CATEGORIES.get(slug, "Tiendas"),
            "title": title,
            "page_url": page_url,
            "pdf_url": list(dict.fromkeys(candidates))[0],
            "period_end": f"{today.year}-{today.month:02d}-{calendar.monthrange(today.year, today.month)[1]:02d}",
        })
    if len(sources) < 20:
        raise RuntimeError(f"UENO discovery returned only {len(sources)} current category PDFs")
    return sources


def extract_day(text):
    text = clean(text)
    if re.search(r"todos los d[ií]as", text, flags=re.I):
        return "Todos los días"
    found = []
    for day in ("lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"):
        if re.search(rf"\b{day}\b", text, flags=re.I):
            found.append("miércoles" if day == "miercoles" else "sábado" if day == "sabado" else day)
    return "; ".join(dict.fromkeys(found)) or "No especificado"


def extract_vigencia(text, fallback):
    for pattern in (
        r"(?:vigencia|vigente)[: ]+.*?(?:2026|2027)",
        r"del\s+\d{1,2}\s+(?:de\s+\w+\s+)?al\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",
        r"desde\s+el\s+.*?hasta\s+el\s+.*?(?:2026|2027)",
    ):
        match = re.search(pattern, text, flags=re.I)
        if match:
            return clean(match.group(0))
    return f"Hasta {fallback}"


def extract_topes(text):
    hits = [clean(match.group(0)) for match in re.finditer(r"(?:tope|l[ií]mite|compra m[ií]nima)[^.]{0,180}", text, flags=re.I)]
    return "; ".join(dict.fromkeys(hits))[:1400] or "Ver bases y condiciones"


def extract_levels(text):
    hits = [clean(match.group(0)) for match in re.finditer(r"Nivel\s*(?:1|2|3|4|5|1\s*al\s*5)[^.]{0,150}", text, flags=re.I)]
    return "; ".join(dict.fromkeys(hits))[:1400] or "No especificado"


def extract_benefit(text):
    hits = re.findall(r"\d{1,3}\s*%\s*(?:de\s+)?(?:reintegro|descuento)", text, flags=re.I)
    if hits:
        return "; ".join(dict.fromkeys(clean(hit) for hit in hits))
    quota = re.search(r"(?:hasta\s+)?\d{1,2}\s+cuotas?\s+sin\s+inter[eé]s(?:es)?", text, flags=re.I)
    return clean(quota.group(0)) if quota else "Ver detalle"


def download_and_read(client, source):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    path = WORK_DIR / f"{source['index']:02d}-{source['slug']}.pdf"
    response = client.get(source["pdf_url"], timeout=90)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise RuntimeError(f"UENO did not return a PDF for {source['slug']}")
    path.write_bytes(response.content)
    with pdfplumber.open(path) as pdf:
        text = clean(" ".join(page.extract_text(x_tolerance=1, y_tolerance=3) or "" for page in pdf.pages))
        source["pages"] = len(pdf.pages)
    source["local_pdf"] = str(path.relative_to(ROOT)).replace("\\", "/")
    return text


def main():
    client = session()
    sources = discover_sources(client)
    rows = []
    for source in sources:
        text = download_and_read(client, source)
        rows.append({
            "Categoría": source["category"],
            "Banco": "ueno bank",
            "Comercio/Promoción": source["title"],
            "Cantidad de descuento / beneficio": extract_benefit(text),
            "Beneficio por niveles": "Sí" if re.search(r"\bNivel\s*[1-5]", text, flags=re.I) else "No",
            "Tipo de beneficio por nivel": "Escala por nivel" if re.search(r"\bNivel\s*[1-5]", text, flags=re.I) else "Sin nivel",
            "Descuentos por nivel": extract_levels(text),
            "Día de promoción": extract_day(text),
            "Vigencia": extract_vigencia(text, source["period_end"]),
            "Locales / comercios detectados": source["slug"].replace("-", " ").title(),
            "Montos / topes": extract_topes(text),
            "Reinicio de límites": "",
            "Detalle": text,
            "Bases / PDF URL": source["pdf_url"],
            "Bases y condiciones URL": source["page_url"],
            "Bases PDF URL": source["pdf_url"],
            "Página PDF": source["index"],
            "Fin del período fuente": source["period_end"],
        })
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps({
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "period": sources[0]["period"],
        "sources": sources,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_CSV.parent.mkdir(exist_ok=True)
    for path in (RAW_CSV, OUT_CSV):
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    with OUT_MD.open("w", encoding="utf-8") as handle:
        handle.write(f"# ueno bank - beneficios {sources[0]['period']}\n\n")
        handle.write(f"{len(rows)} documentos oficiales descubiertos desde {SITEMAP_URL}.\n\n")
        for row in rows:
            handle.write(f"- **{row['Comercio/Promoción']}**: {row['Cantidad de descuento / beneficio']} ([fuente]({row['Bases y condiciones URL']}))\n")
    print(f"UENO: {len(rows)} current category PDFs -> {OUT_CSV}")


if __name__ == "__main__":
    main()
