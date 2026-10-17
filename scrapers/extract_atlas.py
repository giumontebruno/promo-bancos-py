import csv
import html
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE = "https://www.bancoatlas.com.py"
START = f"{BASE}/web/beneficios"
OUT_CSV = Path("outputs/atlas_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/atlas_beneficios_por_categoria.md")
WORK_DIR = Path("work/atlas")
FIELDNAMES = [
    "Categoría",
    "Banco",
    "Comercio/Promoción",
    "Cantidad de descuento / beneficio",
    "Día de promoción",
    "Vigencia",
    "Localidad",
    "Montos / topes",
    "Medios de pago",
    "Beneficio adicional",
    "Detalle",
    "Logo URL",
    "URL detalle",
    "URL categoría",
    "Porcentaje efectivo",
    "Estado verificacion",
    "Texto original de la fuente",
]


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(str(text or ""))).strip()



def normalized_validity(value):
    """Expand only explicit dated Atlas clauses; never infer an omitted year."""
    value = clean(value)
    months = {name: i for i, name in enumerate(("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"), 1)}
    numeric = re.search(r"(?:del\s+)?(\d{1,2})/(\d{1,2})\s+al\s+(\d{1,2})/(\d{1,2})\s+del?\s+(20\d{2})", value, re.I)
    exact_numeric = re.search(r"(?:vigente|v[aá]lida)\s+(?:el d[ií]a|el)\s+(\d{1,2})/(\d{1,2})/(20\d{2})", value, re.I)
    single_numeric = re.search(r"hasta\s+el\s+(\d{1,2})/(\d{1,2})\s+del?\s+(20\d{2})", value, re.I)
    exact = re.search(r"(?:vigente|v[aá]lida)\s+(?:las fechas|el d[ií]a|el)\s+(\d{1,2})(?:\s+y\s+(\d{1,2}))?\s+de\s+(" + '|'.join(months) + r")\s+del?\s+(20\d{2})", value, re.I)
    try:
        if numeric:
            d1,m1,d2,m2,y=map(int,numeric.groups()); start=date(y,m1,d1); end=date(y,m2,d2)
        elif exact_numeric:
            d,m,y=map(int,exact_numeric.groups()); start=end=date(y,m,d)
        elif single_numeric:
            d,m,y=map(int,single_numeric.groups()); return 'Hasta ' + date(y,m,d).isoformat()
        elif exact:
            d1,d2,m,y=exact.groups(); start=date(int(y),months[m.lower()],int(d1)); end=date(int(y),months[m.lower()],int(d2 or d1))
            # A range is safe only for adjacent explicitly listed dates.
            if (end-start).days not in (0,1): return value
        else:
            return value
    except ValueError:
        return value
    if end < start: return value
    return f'Desde {start.isoformat()} hasta {end.isoformat()}'

def attrs(card):
    out = {}
    for key, value in card.attrs.items():
        if key.startswith("data-"):
            out[key[5:].replace("-", "_")] = clean(value)
    return out


def fetch(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_page(session, url, page_no):
    page = fetch(session, url)
    (WORK_DIR / f"beneficios_page_{page_no}.html").write_text(page, encoding="utf-8")
    soup = BeautifulSoup(page, "html.parser")
    rows = []
    for card in soup.select('[data-modal-target="beneficio-modal"]'):
        data = attrs(card)
        if data.get("expired", "").lower() == "true":
            continue
        name = data.get("nombre")
        if not name:
            continue
        label = data.get("label_pct") or "beneficio"
        benefit_parts = []
        if data.get("pct"):
            benefit_parts.append(f"{data['pct']} {label}")
        if data.get("extra_label"):
            benefit_parts.append(data["extra_label"])
        if data.get("cuotas"):
            benefit_parts.append(data["cuotas"])
        category = data.get("categoria", "").replace("&quot;", '"')
        category = clean(re.sub(r'[\[\]"]', "", category).split(",")[0]) or "Sin categoría"
        cities = data.get("ciudades", "").replace("&quot;", '"')
        cities = clean(re.sub(r'[\[\]"]', "", cities).replace(",", "; "))
        detail = clean(" ".join([
            data.get("desc"),
            data.get("extra_label"),
            data.get("extra_resto"),
            data.get("terminos"),
        ]))
        source_url = urljoin(BASE, data.get("boton_url") or "/web/beneficios")
        rows.append({
            "Categoría": category,
            "Banco": "Atlas",
            "Comercio/Promoción": name,
            "Cantidad de descuento / beneficio": "; ".join(dict.fromkeys(benefit_parts)) or "Ver detalle",
            "Día de promoción": data.get("dias") or data.get("dias_filtro") or "No especificado",
            "Vigencia": normalized_validity(data.get("terminos")) or "No especificado",
            "Localidad": cities,
            "Montos / topes": data.get("topes", "").replace("||", "; "),
            "Medios de pago": data.get("desc"),
            "Beneficio adicional": clean(" ".join([data.get("extra_label"), data.get("extra_resto")])),
            "Detalle": detail,
            "Logo URL": urljoin(BASE, data.get("logo") or ""),
            "URL detalle": source_url,
            "URL categoría": url,
        })
    return rows



def apply_document_reviews(rows, session):
    reviews = json.loads(Path('data/atlas_document_reviews.json').read_text(encoding='utf-8'))
    for row in rows:
        review = reviews.get(row['Comercio/Promoción'])
        if not review: continue
        original = row['Detalle']
        response = session.get(review['document_url'], timeout=30)
        response.raise_for_status()
        if hashlib.sha256(original.encode()).hexdigest() != review['detail_sha256'] or hashlib.sha256(response.content).hexdigest() != review['document_sha256']:
            row['Estado verificacion'] = 'unconfirmed'
            continue
        row['Texto original de la fuente'] = original
        row['Detalle'] = original + ' ' + review['note']
        row['Cantidad de descuento / beneficio'] = review['benefit_summary']
        if review.get('effective_percent') is not None:
            row['Porcentaje efectivo'] = str(review['effective_percent'])
        row['Estado verificacion'] = 'official_document'
    return rows

def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    rows = []
    seen = set()
    for page_no in range(1, 8):
        url = START if page_no == 1 else f"{START}?page={page_no}"
        page_rows = parse_page(session, url, page_no)
        if not page_rows and page_no > 1:
            break
        for row in page_rows:
            key = (row["Comercio/Promoción"], row["Cantidad de descuento / beneficio"], row["Día de promoción"])
            if key not in seen:
                seen.add(key)
                rows.append(row)

    rows = apply_document_reviews(rows, session)
    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    if not rows:
        print("WARNING: Atlas returned 0 active benefits. Keeping existing Atlas output files.")
        return

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Atlas - beneficios por categoria\n\n")
        f.write(f"Fuente: {START}\n\nTotal de beneficios: {len(rows)}\n\n")
        for category in sorted({r["Categoría"] for r in rows}):
            f.write(f"## {category}\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia |\n")
            f.write("|---|---|---|---|\n")
            for row in [r for r in rows if r["Categoría"] == category]:
                vals = [row["Comercio/Promoción"], row["Cantidad de descuento / beneficio"], row["Día de promoción"], row["Vigencia"]]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:220] for v in vals) + " |\n")
            f.write("\n")

    print(f"{len(rows)} beneficios -> {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
