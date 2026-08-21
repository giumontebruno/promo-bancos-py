import csv
import re
from html import unescape
from pathlib import Path
from urllib.parse import unquote

import pdfplumber
import requests
from bs4 import BeautifulSoup


IN_CSV = Path("outputs/ueno_beneficios_por_categoria.csv")
LINKS_CSV = Path("work/ueno_pdf_links.csv")
OUT_CSV = Path("outputs/ueno_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/ueno_beneficios_por_categoria.md")
WORK_DIR = Path("work/ueno_bases")
PDF_DIR = Path("work/ueno_bases_pdfs")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def safe_name(url, suffix):
    raw = unquote(url.rstrip("/").split("/")[-1] or "base")
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw).strip("_")[:140] or "base"
    if not stem.lower().endswith(suffix):
        stem += suffix
    return stem


def page_links():
    links = {}
    with LINKS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            page = int(row["Página PDF"])
            url = row["URL"]
            if "/beneficio-byc/" in url or "tyc-beneficios-ueno" in url:
                links.setdefault(page, []).append(url)
    return links


def extract_pdf_links(html):
    urls = re.findall(r"https://www\.ueno\.com\.py/wp-content/uploads/2026/[^\"'\s<>]+?\.pdf", html)
    return list(dict.fromkeys(unescape(u) for u in urls))


def fetch_pdf_text(url):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / safe_name(url, ".pdf")
    if not path.exists():
        response = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        path.write_bytes(response.content)

    pieces = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pieces.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
    except Exception as exc:
        pieces.append(f"ERROR leyendo PDF {url}: {exc}")
    return clean(" ".join(pieces))


def fetch_text(url):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    path = WORK_DIR / safe_name(url, ".html")
    if path.exists():
        html = path.read_text(encoding="utf-8", errors="ignore")
    else:
        response = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        html = response.text
        path.write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    html_text = clean(soup.get_text(" "))
    pdf_urls = extract_pdf_links(html)
    pdf_text = " ".join(fetch_pdf_text(pdf_url) for pdf_url in pdf_urls)
    return html_text, pdf_urls, clean(pdf_text)


def extract_comercios(text):
    all_names = []
    for anex in re.finditer(r"ANEXO I\s+(.*?)(?=ANEXO I|Versi[oó]n\s+\d+|Ante consultas|$)", text, flags=re.I | re.S):
        chunk = clean(anex.group(1))
        # Typical PDF extraction: "1 SALEMMA upay 1 al 31 de Agosto. 2 STOCK ..."
        for part in re.split(r"\s+(?=\d{1,3}\s+)", " " + chunk):
            m = re.match(r"\s*\d{1,3}\s+(.+?)\s+(?:upay|bancard)\b", part, flags=re.I)
            if not m:
                continue
            name = clean(m.group(1))
            name = re.sub(r"\s+(?:POS/VPOS.*|MEDIOS DE PAGO.*|Vigencia.*)$", "", name, flags=re.I)
            if (
                2 <= len(name) <= 90
                and not re.search(r"^(Nombre del comercio|MEDIOS DE PAGO|Vigencia|al\s+\d+)", name, flags=re.I)
                and not re.search(r"cuotas sin intereses|Red$", name, flags=re.I)
            ):
                all_names.append(name)
    if all_names:
        return "; ".join(dict.fromkeys(all_names))[:5000]

    patterns = [
        r"Promoci[oó]n v[aá]lida para todas las sucursales de:\s*(.*?)(?:\.|Beneficio|Condiciones|Medios|$)",
        r"(?:comercios adheridos|aplica en|locales adheridos|alianzas participantes|comercios participantes)[: ]+(.*?)(?:vigencia|tope|monto|beneficio|condiciones|bases|restricciones|$)",
        r"(?:establecimientos|locales)[: ]+(.*?)(?:vigencia|tope|monto|beneficio|condiciones|bases|restricciones|$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            val = clean(m.group(1))
            val = re.sub(r"^●\s*", "", val)
            if (
                len(val) > 8
                and not re.search(r"anexo\s+i$", val, flags=re.I)
                and not re.search(r"Medios de pago habilitados|cuotas sin intereses a trav[eé]s", val, flags=re.I)
            ):
                return val[:1200]
    return ""


def extract_topes(text):
    hits = []
    for pattern in [
        r"(?:tope|l[ií]mite|compra m[ií]nima|monto m[ií]nimo|compra m[ií]n\.?|compras? m[ií]nimas?)[^.]{0,240}",
        r"(?:hasta|m[ií]nimo|m[ií]nima)[^.]{0,120}Gs\.?\s*[\d\.]+[^.]{0,120}",
        r"Gs\.?\s*[\d\.]+",
    ]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(hits))[:1400]


def extract_levels(text):
    # Preserve snippets around every level mention.
    snippets = []
    for m in re.finditer(r"Nivel\s*(?:1|2|3|4|5|1\s*al\s*5)[^.]{0,160}", text, flags=re.I):
        snippets.append(clean(m.group(0)))
    return "; ".join(dict.fromkeys(snippets))[:1400]


def extract_vigencia(text):
    for pattern in [
        r"(?:vigencia|vigente)[: ]+.*?(?:2026|2027)",
        r"del\s+\d{1,2}\s+al\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",
        r"desde\s+el\s+.*?hasta\s+el\s+.*?(?:2026|2027)",
    ]:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return ""


def main():
    links = page_links()
    rows = list(csv.DictReader(IN_CSV.open(encoding="utf-8-sig", newline="")))
    existing_fields = list(rows[0].keys())
    for field in ["Bases y condiciones URL", "Texto bases y condiciones", "Bases PDF URL", "Texto PDF bases"]:
        if field not in existing_fields:
            existing_fields.append(field)
    for row in rows:
        try:
            page = int(row["Página PDF"])
        except (TypeError, ValueError):
            row["Bases y condiciones URL"] = row.get("Bases / PDF URL", "")
            row["Bases PDF URL"] = row.get("Bases / PDF URL", "")
            row["Texto bases y condiciones"] = row.get("Detalle", "")
            row["Texto PDF bases"] = row.get("Detalle", "")
            continue
        urls = links.get(page, [])
        bases_texts = []
        pdf_urls = []
        pdf_texts = []
        for url in urls:
            try:
                html_text, found_pdfs, pdf_text = fetch_text(url)
                bases_texts.append(html_text)
                pdf_urls.extend(found_pdfs)
                if pdf_text:
                    pdf_texts.append(pdf_text)
            except Exception as exc:
                bases_texts.append(f"ERROR leyendo {url}: {exc}")
        bases_text = clean(" ".join(bases_texts + pdf_texts))
        row["Bases y condiciones URL"] = "; ".join(urls)
        row["Bases PDF URL"] = "; ".join(dict.fromkeys(pdf_urls))
        row["Texto bases y condiciones"] = bases_text
        row["Texto PDF bases"] = clean(" ".join(pdf_texts))
        if bases_text:
            comercios = extract_comercios(bases_text)
            topes = extract_topes(bases_text)
            levels = extract_levels(bases_text)
            vigencia = extract_vigencia(bases_text)
            if comercios:
                row["Locales / comercios detectados"] = comercios
            if topes:
                row["Montos / topes"] = topes
            if levels:
                row["Descuentos por nivel"] = levels
            if vigencia:
                row["Vigencia"] = vigencia

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fields)
        writer.writeheader()
        writer.writerows(rows)

    grouped = {}
    for row in rows:
        grouped.setdefault(row["Categoría"], []).append(row)
    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# ueno bank - beneficios por categoria\n\n")
        f.write("Fuente: PDF mensual + páginas de bases y condiciones enlazadas desde el PDF.\n\n")
        for category in sorted(grouped):
            f.write(f"## {category}\n\n")
            f.write("| Promoción | Locales / comercios | Descuento | Niveles | Topes / mínimos | Vigencia |\n")
            f.write("|---|---|---|---|---|---|\n")
            for row in grouped[category]:
                vals = [
                    row["Comercio/Promoción"],
                    row["Locales / comercios detectados"],
                    row["Cantidad de descuento / beneficio"],
                    row["Descuentos por nivel"],
                    row["Montos / topes"],
                    row["Vigencia"],
                ]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:220] for v in vals) + " |\n")
            f.write("\n")

    print(f"enriched {len(rows)} rows")


if __name__ == "__main__":
    main()
