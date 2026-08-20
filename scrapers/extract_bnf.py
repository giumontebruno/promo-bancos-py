import csv
import re
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber
import requests


OUT_CSV = Path("outputs/bnf_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/bnf_beneficios_por_categoria.md")
PDF_DIR = Path("work/bnf/pdfs")

PROMOS = [
    {
        "categoria": "Mayoristas",
        "descuento": "30% reintegro",
        "dia": "Sábados",
        "detalle": "Promoción en mayoristas pagando con Tarjetas de Crédito VISA BNF.",
        "marcas": "BOX Mayorista; Aho Aho Comercial; Supermás; Casa Grütter",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Mayoristas_2026_AGOSTO_fb99dd53e5.pdf",
    },
    {
        "categoria": "Farmacias",
        "descuento": "10% reintegro",
        "dia": "No especificado en tarjeta",
        "detalle": "Promoción en farmacias pagando con Tarjeta de Crédito VISA BNF.",
        "marcas": "ASISMED Drugstore; Farmacias Catedral; Farmacia Vicente Scavone; Farmacenter; Farma Koke; Farmacia Santa Victoria",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Farmacias_2026_AGOSTO_2026_297be5ea2b.pdf",
    },
    {
        "categoria": "Estaciones de Servicio",
        "descuento": "20% reintegro",
        "dia": "Miércoles",
        "detalle": "Promoción en combustibles pagando con Tarjetas de Crédito BNF.",
        "marcas": "Puma; Copetrol; Compasa; Petrochaco; 3MG",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Estaciones_de_Servicio_2026_AGOSTO_2026_fd2e476e47.pdf",
    },
    {
        "categoria": "Supermercados",
        "descuento": "30% reintegro",
        "dia": "Jueves",
        "detalle": "Promoción en supermercados pagando con Tarjetas de Crédito VISA BNF.",
        "marcas": "",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Supermercados_2026_AGOSTO_2e7bd73fa2.pdf",
    },
    {
        "categoria": "Frigoríficos",
        "descuento": "30% reintegro",
        "dia": "Viernes",
        "detalle": "Promoción en frigoríficos pagando con Tarjetas de Crédito VISA BNF.",
        "marcas": "Pollos Don Juan; Cooperativa Chortitzer",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Frigorificos_2026_AGOSTO_33175dc92c.pdf",
    },
]


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def download_pdf(url):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(url).path).name
    path = PDF_DIR / name
    if not path.exists():
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def extract_pdf_text(path):
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
    return clean("\n".join(chunks))


def table_rows(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for raw in table[1:]:
                    cells = [clean(c) for c in raw if clean(c)]
                    if len(cells) >= 4 and re.match(r"^\d+$", cells[0]):
                        rows.append(cells)
    return rows


def first_match(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            return clean(m.group(1) if m.groups() else m.group(0))
    return ""


def extract_vigencia(text):
    return first_match(
        text,
        [
            r"(?:vigencia|promoción tendrá vigencia|promocion tendra vigencia)[: ]+(.*?)(?:\.|;|Condiciones|Bases|$)",
            r"(desde\s+el\s+.+?\s+hasta\s+el\s+.+?(?:2026|2025))",
            r"(del\s+\d{1,2}\s+de\s+\w+\s+al\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4})",
            r"(del\s+\d{1,2}/\d{1,2}/\d{4}\s+al\s+\d{1,2}/\d{1,2}/\d{4})",
        ],
    ) or "Ver bases y condiciones"


def extract_amounts(text):
    parts = []
    for pattern in [
        r"tope[^.]{0,120}",
        r"monto[^.]{0,120}",
        r"Gs\.?\s*[\d\.]+",
        r"₲\s*[\d\.]+",
    ]:
        parts.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(parts)) or "Ver bases y condiciones"


def extract_locales(text, rows, marcas=""):
    if marcas:
        return f"{len(rows)} locales. Marcas/comercios: {marcas}"
    merchants = []
    for cells in rows:
        # Tables with commerce column: N, Comercio, Direccion, Ciudad, Departamento.
        if len(cells) >= 5 and not re.search(r"^(avda|calle|ruta|km|dr\.|mcal|jose|av\.|avenida)\b", cells[1], re.I):
            merchants.append(cells[1])
    if merchants:
        unique = list(dict.fromkeys(m.replace("\n", " ") for m in merchants))
        return f"{len(rows)} locales. Comercios detectados: " + ", ".join(unique[:25])

    # Capture likely merchant lists after "aplica en", "locales", or "comercios".
    candidates = []
    for pattern in [
        r"(?:comercios|locales|establecimientos|aplica en|adheridos)[: ]+(.*?)(?:vigencia|tope|monto|condiciones|bases|forma de participación|restricciones|$)",
    ]:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            candidates.append(clean(m.group(1)))
    if candidates:
        value = max(candidates, key=len)
        return value[:900]
    # Fallback: return named brands found in the visible card/PDF text.
    brands = []
    known = [
        "ASISMED", "CATEDRAL", "FARMACENTER", "VICENTE SCAVONE", "SANTA VICTORIA",
        "FARMA KOKE", "PUMA", "COPETROL", "COMPASA", "PETROCHACO", "3MG",
        "POLLOS DON JUAN", "CHORTITZER",
    ]
    upper = text.upper()
    for brand in known:
        if brand in upper:
            brands.append(brand)
    if brands:
        return f"{len(rows)} locales. Marcas detectadas: " + "; ".join(brands)
    return f"{len(rows)} locales listados en bases" if rows else "Ver bases y condiciones"


def main():
    rows = []
    for promo in PROMOS:
        pdf_path = download_pdf(promo["pdf"])
        pdf_text = extract_pdf_text(pdf_path)
        rows_pdf = table_rows(pdf_path)
        rows.append(
            {
                "Categoría": promo["categoria"],
                "Banco": "BNF",
                "Comercio/Promoción": promo["categoria"],
                "Cantidad de descuento / beneficio": promo["descuento"],
                "Día de promoción": promo["dia"],
                "Vigencia": extract_vigencia(pdf_text),
                "Locales / comercios incluidos": extract_locales(pdf_text, rows_pdf, promo.get("marcas", "")),
                "Cantidad de locales detectados": str(len(rows_pdf)),
                "Montos / topes": extract_amounts(pdf_text),
                "Detalle": promo["detalle"],
                "Bases y condiciones URL": promo["pdf"],
                "Texto bases": pdf_text,
            }
        )

    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# BNF - beneficios por categoria\n\n")
        f.write("Fuente: https://www.bnf.gov.py/bnf/web/#/club-beneficios\n\n")
        f.write("| Categoría | Descuento | Día | Vigencia | Locales / comercios | Montos / topes |\n")
        f.write("|---|---|---|---|---|---|\n")
        for row in rows:
            f.write(
                "| "
                + " | ".join(
                    clean(row[col]).replace("|", "/")[:260]
                    for col in [
                        "Categoría",
                        "Cantidad de descuento / beneficio",
                        "Día de promoción",
                        "Vigencia",
                        "Locales / comercios incluidos",
                        "Montos / topes",
                    ]
                )
                + " |\n"
            )

    print(f"{len(rows)} beneficios -> {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
