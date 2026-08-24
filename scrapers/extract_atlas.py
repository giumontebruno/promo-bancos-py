import csv
import html
import re
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
]


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(str(text or ""))).strip()


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
            "Vigencia": data.get("terminos") or "No especificado",
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
