"""Read monthly UENO terms as tables, with separate branch and benefit records."""
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber
import extract_ueno as monthly
import enrich_ueno_from_bases as bases

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from promo_backend.quality import key, text

CATEGORIES = {
    "combustibles": "Combustible", "petropar": "Combustible", "supermercados": "Supermercados",
    "farmacias": "Farmacias", "clubes": "Clubes sociales", "dba-club-olimpia": "Clubes sociales",
    "dba-club-ccp": "Clubes sociales", "bienestar": "Salud y belleza", "deportes": "Entretenimiento",
    "entretenimiento": "Entretenimiento", "hoteles": "Viajes", "agencias-de-viajes": "Viajes",
}
BRANDS = ["PETROBRAS", "COPETROL", "ENEX", "PETROCHACO", "3MG", "PUMA ENERGY", "PETROMAX", "PETROPAR"]


def money(value):
    found = re.search(r"(?:Gs\.?)?\s*(\d+(?:\.\d{3})+)", str(value or ""))
    return int(found[1].replace(".", "")) if found else None


def parse_tables(pages, source_url, slug):
    levels, merchants, locations = [], [], []
    branch_layout = None
    brand = "Petropar" if slug == "petropar" else ""
    for page_number, tables in enumerate(pages, 1):
        for table in tables:
            cells = [[text(cell) for cell in row] for row in table]
            header = key(" ".join(cell for row in cells[:2] for cell in row))
            period = "semanal" if "semanal" in header else "mensual" if "mensual" in header else ""
            for row in cells:
                if row and re.fullmatch(r"nivel\s*[1-5]", row[0], re.I) and len(row) >= 4:
                    pct = re.search(r"(\d{1,2})\s*%", row[1])
                    if pct:
                        levels.append({"level": int(re.search(r"[1-5]", row[0])[0]), "percent": int(pct[1]),
                                       "purchase_cap": money(row[2]), "refund_cap": money(row[3]),
                                       "period": period, "source_page": page_number})
            location_header = next((row for row in cells[:3] if any(re.search(r"ubicaci[oó]n|direcci[oó]n", cell, re.I) for cell in row)), None)
            if location_header:
                addr = next(i for i, cell in enumerate(location_header) if re.search(r"ubicaci[oó]n|direcci[oó]n", cell, re.I))
                city = next((i for i, cell in enumerate(location_header) if re.search(r"zona|ciudad|localidad", cell, re.I)), None)
                branch_layout = (addr, city)
            if "adheridos" in header:
                for candidate in BRANDS:
                    if key(candidate) in header:
                        brand = candidate
                        break
            numbered = [row for row in cells if row and re.fullmatch(r"\d{1,4}", row[0])]
            for row in numbered:
                if len(row) < 2 or key(row[1]) in {"nombre sucursal", "nombre del comercio"}:
                    continue
                if branch_layout and len(row) > max(i for i in branch_layout if i is not None) and slug in {"combustibles", "petropar"}:
                    addr, city = branch_layout
                    if not row[addr]:
                        continue
                    city_text = row[city] if city is not None else ""
                    name = row[1]
                    if brand and key(brand) not in key(name):
                        name = f"{brand} {name}"
                    fingerprint = "|".join(key(v) for v in (name, row[addr], city_text))
                    locations.append({"id": "loc-ueno-" + hashlib.sha1(fingerprint.encode()).hexdigest()[:10],
                        "bank": "ueno bank", "category": "Combustible", "merchant_name": name,
                        "address": row[addr], "city": city_text, "department": "", "country": "Paraguay",
                        "merchant_brand": brand, "source_url": source_url, "source_page": page_number,
                        "lat": None, "lng": None, "geocode_source": ""})
                elif not branch_layout and len(row) >= 3 and re.search(r"upay|infonet|bancard", " ".join(row[2:]), re.I):
                    name = re.sub(r"\s+(?:detallados? en|en el anexo|\*Exclusivo).*$", "", row[1], flags=re.I)
                    name = re.sub(r"^A trav[eé]s de la APP\s+", "", name, flags=re.I)
                    if len(name) <= 100:
                        merchants.append(name)
    return list({json.dumps(x, sort_keys=True): x for x in levels}.values()), list(dict.fromkeys(merchants)), locations


def main():
    source_rows = list(csv.DictReader(monthly.OUT_CSV.open(encoding="utf-8-sig")))
    by_page = {int(row["Página PDF"]): row for row in source_rows if str(row["Página PDF"]).isdigit()}
    result, all_locations, review = [], [], []
    for page, links in bases.page_links().items():
        source = by_page.get(page)
        if not source:
            continue
        for url in dict.fromkeys(links):
            if "/beneficio-byc/" not in url:
                continue
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            html, pdf_urls, _ = bases.fetch_text(url)
            for pdf_url in pdf_urls:
                pdf_path = bases.PDF_DIR / bases.safe_name(pdf_url, ".pdf")
                with pdfplumber.open(pdf_path) as pdf:
                    pages = [p.extract_tables() for p in pdf.pages]
                    raw = "\n".join(p.extract_text() or "" for p in pdf.pages)
                levels, merchants, locations = parse_tables(pages, pdf_url, slug)
                all_locations.extend(locations)
                if not merchants:
                    merchants = [slug.replace("-", " ")]
                if slug == "clubes":
                    merchants = ["CIT - Consumos dentro del club", "CIT - Cuotas sociales"]
                # Only an annex heading ends the terms, not a reference within a sentence.
                detail = re.split(r"(?m)^[ \t]*ANEXO\s+[IVX]+\b[^\n]*$", raw, maxsplit=1, flags=re.I)[0]
                if slug == "combustibles":
                    merchants = [brand for brand in BRANDS if brand != "PETROPAR" and re.search(r"\b" + re.escape(brand) + r"\b", detail, re.I)]
                elif slug == "petropar":
                    merchants = ["Petropar"]
                rules = "; ".join(f"Nivel {r['level']}: {r['percent']}%" for r in levels)
                caps = "; ".join(f"Nivel {r['level']}: tope de compra {r['period']} Gs. {r['purchase_cap']:,}; tope de reintegro {r['period']} Gs. {r['refund_cap']:,}".replace(",", ".")
                                 for r in levels if r["purchase_cap"] is not None and r["refund_cap"] is not None)
                pct = list(dict.fromkeys(f"{r['percent']}% reintegro" for r in levels))
                if not pct:
                    pct = [m[0] for m in re.finditer(r"\d{1,2}\s*%\s+(?:de\s+)?(?:reintegro|descuento)", detail, re.I)]
                if not pct and re.search(r"cuotas?\s+sin\s+inter[eé]s", detail, re.I):
                    pct = ["Cuotas sin intereses"]
                if not pct:
                    review.append({"source_url": pdf_url, "reason": "benefit_not_extracted"})
                    continue
                for merchant in merchants:
                    row = dict(source)
                    row.update({"Comercio/Promoción": merchant, "Locales / comercios detectados": merchant,
                        "Categoría": CATEGORIES.get(slug, source["Categoría"]),
                        "Cantidad de descuento / beneficio": "; ".join(dict.fromkeys(pct)),
                        "Descuentos por nivel": rules or "No aplica",
                        "Montos / topes": caps or bases.extract_topes(detail),
                        "Detalle": detail, "Texto PDF bases": detail, "Texto bases y condiciones": "",
                        "Bases y condiciones URL": pdf_url, "Bases PDF URL": pdf_url,
                        "Vigencia": bases.extract_vigencia(detail) or source["Vigencia"],
                        "Niveles estructurados": json.dumps(levels, ensure_ascii=False),
                        "Día de promoción": monthly.extract_day(detail)})
                    if slug in {"combustibles", "petropar"}:
                        row["Día de promoción"] = "Todos los días"
                    result.append(row)
    if not result:
        raise RuntimeError("No UENO terms parsed; previous source preserved.")
    fields = list(dict.fromkeys(field for row in result for field in row))
    with monthly.OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    all_locations = list({item["id"]: item for item in all_locations}.values())
    (ROOT / "outputs/ueno_branch_sources.json").write_text(json.dumps(all_locations, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "outputs/ueno_terms_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "outputs/ueno_source_meta.json").write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "records": len(result)}), encoding="utf-8")
    print(f"UENO: {len(result)} benefits; {len(all_locations)} branch records; {len(review)} documents need review.")


if __name__ == "__main__":
    main()
