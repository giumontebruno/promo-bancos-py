import csv
import json
import hashlib
import requests
from datetime import datetime, timezone
import re
import unicodedata
from pathlib import Path
from sudameris_campaigns import expand_campaign


IN = Path("outputs/sudameris_promociones.csv")
OUT_CSV = Path("outputs/sudameris_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/sudameris_beneficios_por_categoria.md")


CATEGORIES = [
    ("Supermercados", ["LUISITO", "REAL SUPERMERCADOS", "FRIGOMAS"]),
    ("Farmacias", ["FARMACENTER", "FARMACIA", "BIGGIE FARMA", "DRUGSTORE"]),
    ("Combustible", ["COPETROL", "COPEMARKET", "ENEX", "ECOP", "ESTACIONES DE SERVICIO", "CCU"]),
    ("Gastronomía", ["GASTRONOM", "RESTAURANTE", "PARU", "CONCEPTS", "BISTRO", "SERENDIPITY", "HORNALLA", "CANTINA", "BIGGIE EXPRESS"]),
    ("Viajes y turismo", ["TRAVEL", "DTP", "POSADA", "YACHT", "HOTEL", "PAQUETE", "ALOJAMIENTO"]),
    ("Moda", ["BABY COTTONS", "ADOLFO DOMINGUEZ", "CARO CUORE", "RAPSODIA", "ESTANCIAS", "YOUNIQUE"]),
    ("Hogar", ["MATERASSI", "PARANA HOGAR", "COLCHONES", "LINCOLN"]),
    ("Deportes y clubes", ["CLUB", "LIVE FITNESS", "DEPORTIVO", "NÁUTICO", "NAUTICO"]),
    ("Entretenimiento y experiencias", ["MCLAREN", "F1", "DISTRITO PERSEVERANCIA"]),
    ("Cuotas y tarjetas", ["CUOTAS", "TARJETAS EMPRESARIALES", "COMPRAS EN EL EXTERIOR", "SUDAMERIS GO"]),
    ("Solidaridad", ["DONACIÓN", "DONACION", "TECHO"]),
]


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip().strip(":").strip()


def campaign_key(value):
    normalized = unicodedata.normalize("NFKD", clean(value))
    return "".join(char for char in normalized if not unicodedata.combining(char)).upper()


def category_for(row):
    haystack = f"{row['Comercio/Promocion']} {row['Beneficios']} {row['Texto completo']}".upper()
    for category, keys in CATEGORIES:
        if any(key in haystack for key in keys):
            return category
    return "Otros"


def extract_day(row):
    text = clean(f"{row['Vigencia']} {row['Texto completo']}")
    patterns = [
        r"Todos los (lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos)",
        r"(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+a\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"Martes a domingo",
        r"Miércoles a sábado",
        r"Viernes y sábados",
        r"primer (lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"Solo el primer (lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"\b\d{1,2}\s+de cada mes\b",
        r"\bTodos los días\b",
    ]
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            found.append(clean(match.group(0)))
    return "; ".join(dict.fromkeys(found)) or "No especificado"


def extract_vigencia(row):
    vigencia = clean(row["Vigencia"])
    text = clean(row["Texto completo"])
    if vigencia and len(vigencia) > 8 and "según las" not in vigencia.lower():
        return vigencia
    for pattern in [
        r"Periodo de campaña:\s*(.*?)(?:\.| Beneficio)",
        r"Vigencia:\s*(.*?)(?:\.| Beneficio)",
        r"vigencia desde\s+(.*?)(?:\.|$)",
        r"Desde el\s+.*?hasta el\s+.*?(?:2026|2025)",
        r"Del\s+\d{1,2}/\d{1,2}\s+al\s+\d{1,2}/\d{1,2}/\d{4}",
    ]:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return vigencia or "No especificado"


def extract_discount(row):
    bits = []
    for col in ["% detectado", "Cuotas detectadas", "Tope detectado"]:
        value = clean(row.get(col, ""))
        if value:
            bits.append(value)
    benefit = clean(row["Beneficios"]) or clean(row["Texto completo"])
    amounts = re.findall(r"(?:Gs\.?\s*[\d\.]+|USD\s*\d+)", benefit, flags=re.I)
    for amount in amounts:
        if amount not in bits:
            bits.append(clean(amount))
    if bits:
        return "; ".join(dict.fromkeys(bits))
    return benefit[:180] if benefit else "No especificado"



def reviewed_document_rows(row):
    path = Path('data/sudameris_document_reviews.json')
    if not path.exists():
        return None
    reviews = json.loads(path.read_text(encoding='utf-8'))
    links = [url.strip() for url in row.get('Bases y condiciones URL', '').split(';')]
    matching = [item for item in reviews if item['pdf'] in links]
    if not matching:
        return None
    verified_hashes = {}
    result = []
    for review in matching:
        if review['pdf'] not in verified_hashes:
            response = requests.get(review['pdf'], timeout=45)
            response.raise_for_status()
            verified_hashes[review['pdf']] = hashlib.sha256(response.content).hexdigest()
        if verified_hashes[review['pdf']] != review['sha256']:
            raise ValueError('Reviewed PDF changed: ' + review['pdf'])
        for key, benefit, cards in review['offers']:
            scoped = {**review, **review.get('offer_overrides', {}).get(key, {})}
            cards = scoped.get('cards', cards)
            cap = scoped.get('cap', '')
            validity = (f"Desde {scoped['start']} hasta {scoped['end']}" if scoped.get('start')
                        else f"Hasta {scoped['end']}")
            result.append({
                'Categoría': scoped['category'], 'Banco': 'Sudameris',
                'Comercio/Promoción': scoped['merchant'],
                'Cantidad de descuento / beneficio': benefit,
                'Día de promoción': scoped['day'], 'Vigencia': validity,
                'Montos / topes': cap, 'URL': row['URL'],
                'URL fuente actual': review['pdf'], 'Estado verificacion': 'official_document',
                'Fecha verificacion fuente': datetime.now(timezone.utc).isoformat(),
                'Tarjetas verificadas': cards, 'Variante': key,
                'Tipo de variante': 'financing' if key.startswith('financing') else key,
                'Etiqueta de variante': key, 'Topes revisados por variante': 'yes',
                'Detalle': f"{benefit}. {cards}. {cap} {scoped['conditions']} {scoped.get('extra', '')}",
                'Texto original de la fuente': review.get('original_conditions', review['conditions']),
            })
    return result


def main():
    with IN.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    previous_rows = list(csv.DictReader(OUT_CSV.open(encoding='utf-8-sig', newline=''))) if OUT_CSV.exists() else []
    table = []
    failures = []
    for row in rows:
        campaign = campaign_key(row['Comercio/Promocion'])
        if campaign in {'GASTRONOMIA', 'GASTRONOMIA 26', 'ZONA ESTE', 'ZONA SUR', 'ZONA NORTE'} or campaign.startswith('PRIMAVERA 2026'):
            try:
                table.extend(expand_campaign(row))
            except (requests.RequestException, ValueError) as error:
                failures.append({'campaign': row['Comercio/Promocion'], 'url': row.get('URL fuente actual') or row['URL'], 'reason': str(error)})
            continue
        try:
            verified = reviewed_document_rows(row)
        except (requests.RequestException, ValueError) as error:
            failures.append({'campaign': row['Comercio/Promocion'], 'url': row.get('URL fuente actual') or row['URL'], 'reason': str(error)})
            verified = None
        if verified:
            table.extend(verified)
            continue
        prior = [p for p in previous_rows if p['URL'] == row['URL']]
        if len(prior) == 1:
            retained = dict(prior[0])
            retained['URL fuente actual'] = row.get('URL fuente actual', row['URL'])
            retained['Estado verificacion'] = 'unconfirmed'
            table.append(retained)
            continue
        if not row.get('% detectado') and not row.get('Cuotas detectadas'):
            failures.append({'campaign': row['Comercio/Promocion'], 'url': row.get('URL fuente actual') or row['URL'], 'reason': 'No quantified benefit on official page; retained in staging only'})
            continue
        table.append(
            {
                "Categoría": category_for(row),
                "Banco": "Sudameris",
                "Comercio/Promoción": clean(row["Comercio/Promocion"]),
                "Cantidad de descuento / beneficio": extract_discount(row),
                "Día de promoción": extract_day(row),
                "Vigencia": extract_vigencia(row),
                "Detalle": clean(row["Texto completo"]) or clean(row["Beneficios"]),
                "URL fuente actual": row.get("URL fuente actual", row["URL"]),
                "Estado verificacion": "unconfirmed",
                "URL": row["URL"],
            }
        )

    # Missing from the new website is uncertainty, not evidence of expiry.
    if OUT_CSV.exists():
        previous = list(csv.DictReader(OUT_CSV.open(encoding='utf-8-sig', newline='')))
        identities = {(r['URL'], r['Comercio/Promoción']) for r in table}
        verified_urls = {r['URL'] for r in table if r.get('Estado verificacion') == 'official_document' and r.get('Variante')}
        for old in previous:
            if (old['URL'], old['Comercio/Promoción']) not in identities and old['URL'] not in verified_urls:
                old['Estado verificacion'] = 'unconfirmed'
                table.append(old)

    Path('outputs/sudameris_migration_report.json').write_text(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'campaigns': len(rows), 'failures': failures, 'retained_unconfirmed': sum(r.get('Estado verificacion') == 'unconfirmed' for r in table)}, ensure_ascii=False, indent=2), encoding='utf-8')

    table.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(key for row in table for key in row)))
        writer.writeheader()
        writer.writerows(table)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Sudameris - beneficios por categoria\n\n")
        f.write(f"Total de promociones: {len(table)}\n\n")
        for category in sorted({r["Categoría"] for r in table}):
            f.write(f"## {category}\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia |\n")
            f.write("|---|---|---|---|\n")
            for row in [r for r in table if r["Categoría"] == category]:
                values = [
                    row["Comercio/Promoción"],
                    row["Cantidad de descuento / beneficio"],
                    row["Día de promoción"],
                    row["Vigencia"],
                ]
                f.write("| " + " | ".join(v.replace("|", "/")[:220] for v in values) + " |\n")
            f.write("\n")

    print(f"Tabla creada: {OUT_CSV}")
    print(f"Resumen creado: {OUT_MD}")


if __name__ == "__main__":
    main()
