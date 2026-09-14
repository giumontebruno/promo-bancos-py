import csv
import hashlib
import json
import re
from datetime import date, datetime, timezone
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
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Mayoristas_2026_SEP_2026_5bc6ee5563.pdf",
    },
    {
        "categoria": "Farmacias",
        "descuento": "10% reintegro",
        "dia": "No especificado en tarjeta",
        "detalle": "Promoción en farmacias pagando con Tarjeta de Crédito VISA BNF.",
        "marcas": "ASISMED Drugstore; Farmacias Catedral; Farmacia Vicente Scavone; Farmacenter; Farma Koke; Farmacia Santa Victoria",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Farmacias_2026_SEP_2026_3ca4b62e69.pdf",
    },
    {
        "categoria": "Estaciones de Servicio",
        "descuento": "20% reintegro",
        "dia": "Miércoles",
        "detalle": "Promoción en combustibles pagando con Tarjetas de Crédito BNF.",
        "marcas": "Puma; Copetrol; Compasa; Petrochaco; 3MG",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Estaciones_de_Servicio_2026_SEP_2026_0c00026515.pdf",
    },
    {
        "categoria": "Supermercados",
        "descuento": "30% reintegro",
        "dia": "Jueves",
        "detalle": "Promoción en supermercados pagando con Tarjetas de Crédito VISA BNF.",
        "marcas": "",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Supermercados_2026_SEP_2026_d048e2b720.pdf",
    },
    {
        "categoria": "Frigoríficos",
        "descuento": "30% reintegro",
        "dia": "Viernes",
        "detalle": "Promoción en frigoríficos pagando con Tarjetas de Crédito VISA BNF.",
        "marcas": "Pollos Don Juan; Cooperativa Chortitzer",
        "pdf": "https://www.bnf.gov.py/uploads/Promocion_Reintegro_Frigorificos_2026_SEP_2026_f798717e14.pdf",
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


def branch_records(path, promo):
    """Read the heading above each table, including several brands on one page."""
    records = []
    brand = ""
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            for table in page.find_tables():
                above = clean(page.crop((0, 0, page.width, table.bbox[1])).extract_text())
                headings = re.findall(r'Listado de (?:locales de|estaciones de servicio|salones y puntos de venta de)\s+(.+?)\s+adherid[oa]s', above, re.I)
                if headings:
                    brand = headings[-1]
                rows = table.extract()
                has_merchant = 'Comercios' in clean(' '.join(str(x or '') for x in rows[0]))
                for row in rows:
                    cells = [clean(x) for x in row if clean(x)]
                    if len(cells) < 4 or not cells[0].isdigit():
                        continue
                    merchant = cells[1] if has_merchant else brand
                    offset = 2 if has_merchant else 1
                    if not merchant or len(cells) < offset + 3:
                        raise ValueError(f'BNF: unnamed branch on page {page_number}')
                    address, city, department = cells[offset:offset + 3]
                    digest = hashlib.sha256('|'.join((merchant, address, city)).casefold().encode()).hexdigest()[:16]
                    records.append({'id': 'loc-bnf-' + digest, 'bank': 'BNF',
                        'category': {'Estaciones de Servicio': 'Combustible', 'Frigoríficos': 'Supermercados'}.get(promo['categoria'], promo['categoria']),
                        'source_category': promo['categoria'], 'merchant_name': merchant,
                        'merchant_brand': merchant, 'address': address, 'city': city,
                        'department': department, 'country': 'Paraguay', 'source_url': promo['pdf'],
                        'source_page': page_number, 'lat': None, 'lng': None, 'geocode_source': '',
                        'online_only': address.lower().startswith('app ')})
    return records


def benefit_rows(promo, text, branches):
    validity = first_match(text, [r'Vigencia:\s*(.*?)\s*Beneficio:'])
    # Fail the source refresh instead of silently renewing an old monthly PDF.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from promo_backend.quality import validity_dates
    ends = validity_dates(validity)['ends_on']
    if not ends or ends < date.today().isoformat():
        raise ValueError(f'BNF {promo["categoria"]}: expired or unknown validity: {validity}')
    benefit = first_match(text, [r'Beneficio:\s*(.*?)\s*Condiciones:'])
    rates = list(dict.fromkeys(re.findall(r'(\d+)\s*%\s*de reintegro', benefit, re.I)))
    if not rates:
        raise ValueError('BNF: no refund percentage in benefit section')
    conditions = first_match(text, [r'Condiciones:\s*(.*?)\s*Exclusiones:'])
    exclusions = first_match(text, [r'Exclusiones:\s*(.*?)(?:Listado de|$)'])
    clauses = [clean(x) for x in re.split('[•●]', conditions) if clean(x)]
    rows = []
    for rate in rates:
        scoped = first_match(benefit, [rf'({rate}\s*%\s*de reintegro[^•●]*?)(?=[•●]|$)'])
        cards_match = re.search(r'Visa\s+(.+?)(?:\s+BNF|[.;]|$)', scoped, re.I)
        cards = 'Tarjetas de crédito Visa ' + (cards_match[1] if cards_match else 'Clásica, Oro y Platinum') + ' BNF'
        classic_only = 'clásica' in cards.lower() and not re.search('oro|platinum', cards, re.I)
        premium_only = not classic_only and len(rates) > 1
        limits = []
        for clause in clauses:
            if not re.search(r'tope de (?:compra|reintegro)', clause, re.I):
                continue
            kind = 'compra' if re.search('tope de compra', clause, re.I) else 'reintegro'
            amounts = list(re.finditer(r'Gs\.?\s*([\d.]+)', clause, re.I))
            for i, amount in enumerate(amounts):
                scope = clause[amount.end():amounts[i+1].start() if i+1 < len(amounts) else len(clause)]
                if not re.search('visa|platinum|clásica', scope, re.I):
                    scope = clause[:amount.start()]
                has_classic = bool(re.search('clásica', scope, re.I))
                has_premium = bool(re.search('oro|platinum', scope, re.I))
                if classic_only and has_premium and not has_classic:
                    continue
                if premium_only and has_classic and not has_premium:
                    continue
                limits.append(f'Tope de {kind} mensual: Gs. {amount[1]}.')
        additional = [x for x in clauses if not re.search(r'tope de (?:compra|reintegro)', x, re.I)]
        warning = ''
        if premium_only and '600.000 (guaraníes trescientos setenta y cinco mil)' in conditions:
            warning = 'El PDF indica Gs. 600.000 de reintegro, pero expresa otro importe en letras. Confirmar el tope con BNF antes de comprar.'
            limits = []
        for merchant in dict.fromkeys(x['merchant_name'] for x in branches):
            local_branches = [x for x in branches if x['merchant_name'] == merchant]
            merchant_additional = [clause for clause in additional
                if 'COPETROL VAMOS' not in clause.upper() or 'COPETROL' in merchant.upper()]
            normalized = f'Vigencia: {validity} Beneficio: {rate}% de reintegro. {cards}. ' + ' '.join(limits + merchant_additional) + ' Exclusiones: ' + exclusions
            rows.append({'Categoría': promo['categoria'], 'Banco': 'BNF',
                'Comercio/Promoción': merchant, 'Cantidad de descuento / beneficio': f'{rate}% reintegro',
                'Día de promoción': promo['dia'], 'Vigencia': validity,
                'Locales / comercios incluidos': f'{len(local_branches)} locales adheridos de {merchant}',
                'Cantidad de locales detectados': str(len(local_branches)),
                'Montos / topes': ' '.join(limits), 'Detalle': normalized + ' ' + warning,
                'Bases y condiciones URL': promo['pdf'], 'Texto bases': normalized,
                'Texto original de la fuente': text.split('Listado de')[0],
                'Tarjetas verificadas': cards, 'Advertencia de fuente': warning})
    installments = re.search(r'Hasta\s+(\d+)\s+cuotas sin intereses[^•●]*', benefit, re.I)
    if installments:
        seen = set()
        for row in list(rows):
            merchant = row['Comercio/Promoción']
            if merchant in seen:
                continue
            seen.add(merchant)
            finance = dict(row)
            finance['Cantidad de descuento / beneficio'] = f'{installments[1]} cuotas sin intereses'
            finance['Montos / topes'] = ''
            finance['Advertencia de fuente'] = ''
            finance['Detalle'] = finance['Texto bases'] = f'Vigencia: {validity} Beneficio: {installments[0]} Tarjetas de crédito Visa BNF. El reintegro no se acumula con compras financiadas en cuotas.'
            rows.append(finance)
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
    branches = []
    for promo in PROMOS:
        pdf_path = download_pdf(promo["pdf"])
        pdf_text = extract_pdf_text(pdf_path)
        current_branches = branch_records(pdf_path, promo)
        branches.extend(current_branches)
        rows.extend(benefit_rows(promo, pdf_text, current_branches))

    OUT_CSV.parent.mkdir(exist_ok=True)
    Path('outputs/bnf_branch_sources.json').write_text(json.dumps(branches, ensure_ascii=False, indent=2), encoding='utf-8')
    Path('outputs/bnf_source_meta.json').write_text(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'source_urls': [p['pdf'] for p in PROMOS]}), encoding='utf-8')
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
