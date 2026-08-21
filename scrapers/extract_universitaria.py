import csv
import html
import re
from pathlib import Path
from urllib.parse import urljoin

import pdfplumber
import requests
from bs4 import BeautifulSoup


BASE = "https://www.universitaria.coop"
START = f"{BASE}/promociones"
OUT_CSV = Path("outputs/universitaria_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/universitaria_beneficios_por_categoria.md")
WORK_DIR = Path("work/universitaria")


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(str(text or ""))).strip()


def fetch(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response


def extract_pdf_text(session, url):
    if not url:
        return ""
    filename = re.sub(r"[^a-zA-Z0-9_.-]+", "_", url.rsplit("/", 1)[-1] or "bases.pdf")
    path = WORK_DIR / "pdfs" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(fetch(session, url).content)
    try:
        with pdfplumber.open(path) as pdf:
            return clean(" ".join(page.extract_text() or "" for page in pdf.pages))[:5000]
    except Exception:
        return ""


def first_match(text, patterns, default="No especificado"):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            return clean(match.group(1) if match.groups() else match.group(0)).strip(". ")
    return default


def extract_day(text):
    return first_match(text, [
        r"(todos los días)",
        r"(todos los (?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos))",
        r"\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
    ])


def extract_validity(text):
    return first_match(text, [
        r"(vigencia[^.]{0,180})",
        r"(desde\s+el?\s*\d{1,2}[^.]{0,140})",
        r"(hasta\s+el?\s*\d{1,2}[^.]{0,140})",
    ])


def extract_topes(text):
    hits = []
    for pattern in [r"tope[^.]{0,160}", r"mínim[oa][^.]{0,140}", r"Gs\.?\s*[\d\.]+"]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(hits))


def extract_benefit(card_text, combined_text):
    card_text = clean(card_text)
    combined_text = clean(combined_text)
    weak = not card_text or re.fullmatch(
        r"(?i)(todos los d[ií]as|todos los (?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados|domingos)|martes y s[aá]bados|con tarjetas de cr[eé]dito universitaria|en productos seleccionados|popeyes|subway)",
        card_text,
    )
    if not weak:
        return card_text

    hits = []
    for pattern in [
        r"hasta\s+\d+\s*\([^)]+\)\s+cuotas\s+sin\s+inter[eé]s(?:es)?",
        r"hasta\s+\d+\s+cuotas\s+sin\s+inter[eé]s(?:es)?",
        r"\d{1,3}\s*%\s*(?:de\s*)?(?:descuento|reintegro)",
        r"(?:panal|cabal|mastercard)\s+qr\s+\d{1,3}\s*%",
        r"pago\s+con\s+tc\s+f[ií]sica[^.]{0,80}\d{1,3}\s*%",
    ]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, combined_text, flags=re.I))
    return "; ".join(dict.fromkeys(hits)) or card_text or "Ver detalle"


def category_links(soup):
    links = []
    for a in soup.select('a.card-promociones[href*="/promociones/post/"]'):
        href = urljoin(BASE, a.get("href"))
        name = clean((a.select_one(".title-card-promociones") or a).get_text(" "))
        if href and name:
            links.append((name.title(), href))
    return list(dict.fromkeys(links))


def nearest_heading(card):
    node = card
    while node:
        prev = node.find_previous(["h2", "h1"])
        if prev:
            return clean(prev.get_text(" "))
        node = node.parent
    return ""


def parse_category(session, category, url):
    page = fetch(session, url).text
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    (WORK_DIR / f"{slug}.html").write_text(page, encoding="utf-8")
    soup = BeautifulSoup(page, "html.parser")
    rows = []
    for card in soup.select(".promo-item"):
        title = clean((card.select_one("[rel='category']") or {}).get_text(" ") if card.select_one("[rel='category']") else "")
        title = title or nearest_heading(card) or category
        benefit = clean(" ".join(p.get_text(" ", strip=True) for p in card.select(".card-body p")))
        image = card.select_one("img")
        image_url = urljoin(BASE, image.get("src")) if image and image.get("src") else ""
        bases = card.select_one('a[href$=".pdf"], a[href*=".pdf"]')
        bases_url = urljoin(BASE, bases.get("href")) if bases and bases.get("href") else ""
        bases_text = extract_pdf_text(session, bases_url)
        combined = clean(" ".join([title, benefit, bases_text]))
        rows.append({
            "Categoría": category,
            "Banco": "Coop. Universitaria",
            "Comercio/Promoción": title,
            "Cantidad de descuento / beneficio": extract_benefit(benefit, combined),
            "Día de promoción": extract_day(combined),
            "Vigencia": extract_validity(combined),
            "Montos / topes": extract_topes(combined),
            "Detalle": combined,
            "Imagen URL": image_url,
            "Bases y condiciones URL": bases_url,
            "URL categoría": url,
        })
    return rows


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    start_page = fetch(session, START).text
    (WORK_DIR / "promociones.html").write_text(start_page, encoding="utf-8")
    links = category_links(BeautifulSoup(start_page, "html.parser"))

    rows = []
    seen = set()
    for category, url in links:
        for row in parse_category(session, category, url):
            key = (row["Categoría"], row["Comercio/Promoción"], row["Cantidad de descuento / beneficio"], row["Bases y condiciones URL"])
            if key not in seen:
                seen.add(key)
                rows.append(row)

    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Cooperativa Universitaria - promociones por categoria\n\n")
        f.write(f"Fuente: {START}\n\nTotal de promociones: {len(rows)}\n\n")
        for category in sorted({r["Categoría"] for r in rows}):
            f.write(f"## {category}\n\n")
            f.write("| Comercio/Promoción | Beneficio | Día | Vigencia |\n")
            f.write("|---|---|---|---|\n")
            for row in [r for r in rows if r["Categoría"] == category]:
                vals = [row["Comercio/Promoción"], row["Cantidad de descuento / beneficio"], row["Día de promoción"], row["Vigencia"]]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:220] for v in vals) + " |\n")
            f.write("\n")

    print(f"{len(rows)} promociones -> {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
