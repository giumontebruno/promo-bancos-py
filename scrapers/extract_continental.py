import csv
import json
import re
from html import unescape
from pathlib import Path

import requests


BASE = "https://www.bancontinental.com.py"
API = f"{BASE}/api/comercios?_limit=-1"
OUT_CSV = Path("outputs/continental_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/continental_beneficios_por_categoria.md")
WORK_JSON = Path("work/continental_comercios.json")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("**", " ").replace("__", " ")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def first_match(text, patterns, default="No especificado"):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            return clean(m.group(1) if m.groups() else m.group(0)).strip(". ")
    return default


def extract_day(text):
    return first_match(
        text,
        [
            r"\b(Todos los días)\b",
            r"\b(Los\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos))\b",
            r"\b(Todos los\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos))\b",
            r"\b(Primer\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)[^.]*)",
            r"\b(Tercer\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)[^.]*)",
            r"\b(?:Desde|de)\s+los\s+(.{0,50}?(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo).{0,80}?)(?:\.|\n)",
        ],
    )


def extract_vigencia(text):
    return first_match(
        text,
        [
            r"(Vigente desde\s+.*?(?:\.|$))",
            r"(Vigente hasta\s+.*?(?:\.|$))",
            r"(Válido hasta\s+.*?(?:\.|$))",
            r"(Valido hasta\s+.*?(?:\.|$))",
        ],
    )


def extract_discount(item, text):
    parts = []
    pct = item.get("porcentaje_ahorro") or {}
    if pct.get("titulo"):
        parts.append(pct["titulo"])
    for pattern in [
        r"hasta\s+\d+\s+cuotas?\s+sin\s+inter[eé]s(?:es)?",
        r"\d+\s*%\s+de\s+reintegro",
        r"\d+\s*%\s+en\s+caja",
        r"\d+\s*%\s+de\s+descuento",
    ]:
        parts.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(parts)) or "Ver descripción"


def extract_topes(text):
    hits = []
    for pattern in [
        r"l[ií]mite[^.]{0,160}",
        r"tope[^.]{0,160}",
        r"Gs\.?\s*[\d\.]+",
    ]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(hits)) or "No especificado"


DATE = r'\d{1,2}\s+(?:de\s+)?\w+\s+del?\s+\d{4}'
EXPIRY = re.compile(r'Vigente hasta\s+(?:el\s+)?(' + DATE + r')', re.I)
BENEFIT = re.compile(r'-\s*(?=(?:Hasta\s+)?\d+\s*(?:%|cuotas))', re.I)


def scoped_segments(text):
    """Split explicit scopes only; never borrow a later expiry for an earlier benefit."""
    expiries = list(EXPIRY.finditer(text))
    forward = re.search(r'Vigente desde el\s+(' + DATE + r')\s+al\s+(' + DATE + r')\s*:', text, re.I)
    school = re.findall(r'-\s*(\d+)% de reintegro del (\d+) al (\d+) de (\w+) de (\d{4})\.', text, re.I)
    if len(school) == 3:
        prefix = text[:text.index('-')]
        cap = re.search(r'Límite de compra de hasta.*?(?=Además)', text)[0]
        finance = text[text.index('Además'):]
        common = finance[finance.index('Válido pagando'):]
        common = re.sub(r'Vigente del.*?\.', '', common)
        result = []
        for pct, start, end, month, year in school:
            validity = f'Desde el {start} de {month} de {year} hasta el {end} de {month} de {year}'
            result.append((f'{prefix} {pct}% de reintegro. {cap} {common}', validity, 'Todos los días'))
        result.append((prefix + finance, f'Desde el {school[0][1]} de {school[0][3]} de {school[0][4]} hasta el {school[-1][2]} de {school[-1][3]} de {school[-1][4]}', 'Todos los días'))
        return result
    if len(expiries) < 2 and not forward:
        return []
    chunks = []
    cursor = 0
    for expiry in expiries:
        chunks.append((text[cursor:expiry.start()], expiry[0]))
        cursor = expiry.end()
    common = text[cursor:].lstrip('. ')
    if forward:
        rest = text[forward.end():]
        cut = re.search(r'Las promociones aplican', rest, re.I)
        if not cut:
            raise ValueError('Unrecognized forward-date Continental scope')
        chunks.append((rest[:cut.start()], forward[0].rstrip(':')))
        common = rest[cut.start():]
    # Some sources list card-specific caps after all dated benefits.
    cap_pattern = re.compile(r'-\s*Reintegros del (\d+)%\s+(.*?)(?=\s*-\s*Reintegros del|Las promociones|Locales adheridos|\(\*|$)', re.I)
    caps = {m[1]: m[2].strip() for m in cap_pattern.finditer(common)}
    common = cap_pattern.sub('', common)
    common = re.sub(r'Límites de compras:\s*', '', common)
    initial = text[:BENEFIT.search(text).start()]
    result = []
    for chunk, validity in chunks:
        markers = list(BENEFIT.finditer(chunk))
        if not markers:
            raise ValueError('Missing benefit in Continental date scope')
        context = chunk[:markers[0].start()].strip(' ._-')
        # Leading schedule persists only when the later block has no own schedule.
        has_day = re.search(r'lunes|martes|miércoles|jueves|viernes|sábado|domingo|días|del \d+ al', context, re.I)
        context = context if has_day else initial + ' ' + context
        context = re.sub(r'^Además[, :]*', '', context, flags=re.I)
        for i, marker in enumerate(markers):
            benefit = chunk[marker.end():markers[i+1].start() if i+1 < len(markers) else len(chunk)].strip(' ._')
            percent = re.match(r'(?:Hasta\s+)?(\d+)%', benefit, re.I)
            cap = caps.get(percent[1], '') if percent else ''
            detail = clean(f'{context} {benefit}. {validity}. {cap} {common}')
            day = context
            interval = re.search(r'Del (\d+) al (\d+) de (\w+)', context, re.I)
            if interval:
                year = re.search(r'\d{4}', validity)[0]
                validity = f'Desde el {interval[1]} de {interval[3]} de {year} hasta el {interval[2]} de {interval[3]} de {year}'
            result.append((detail, validity, day))
    return result


def review_single_day_contimarket(row):
    """Correct the captured one-day discount, preserving its historical identity.

    The independent Contimarket.com row already describes daily financing. Do
    not promote its schedule/cap into this dated reintegro or duplicate it here.
    """
    if clean(row.get("Comercio/Promoción")).casefold() != "contimarket - 25%":
        return row
    detail = row.get("Texto original de la fuente") or row.get("Detalle", "")
    exact = re.search(r"Vigente el (\d{1,2}) (?:de )?(\w+) de (20\d{2})", detail, re.I)
    before, sep, after = detail.partition("Además, todos los días:")
    common_at = after.find("Válido pagando")
    if not exact or not sep or common_at < 0 or not re.search(r"25% de reintegro", before):
        return {**row, "Estado verificacion": "unconfirmed",
                "Revisión de variantes": "Changed single-day Contimarket scope requires review"}
    months = {m: i for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}
    from datetime import date
    try:
        actual = date(int(exact[3]), months[exact[2].lower()], int(exact[1])).isoformat()
    except (ValueError, KeyError):
        return {**row, "Estado verificacion": "unconfirmed"}
    common = after[common_at:]
    # Financing is represented separately; keep the original source untouched.
    scoped = clean(before + " " + common)
    scoped = re.sub(r"Reintegros y cuotas", "Reintegros", scoped)
    return {**row, "Detalle": scoped, "Texto original de la fuente": detail,
            "Cantidad de descuento / beneficio": "25% de reintegro",
            "Montos / topes": extract_topes(before),
            "Día de promoción": actual,
            "Vigencia de compras verificada": f"Desde {actual} hasta {actual}"}


def segment_row(row):
    row = review_single_day_contimarket(row)
    scopes = scoped_segments(row['Detalle'])
    if not scopes:
        return [row]
    result = []
    for i, (detail, validity, day) in enumerate(scopes):
        validity = re.sub(r'(\d) (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', r'\1 de \2', validity, flags=re.I)
        card = re.search(r'Privilege Continental|(?:Mastercard )?Black (?:e|y)(?: Visa)? Infinite|Dinelco, Clásica y Oro|\bOro\b', detail)
        result.append({**row, 'Detalle': detail, 'Vigencia': validity,
            'Día de promoción': day, 'Cantidad de descuento / beneficio': ('Hasta ' if re.search(r'\bHasta \d+%', detail, re.I) else '') + extract_discount({}, detail),
            'Montos / topes': extract_topes(detail), 'Variante': f'scope-{i+1}',
            'Tarjetas verificadas': card[0] if card else 'Tarjetas de crédito Continental',
            'Tipo de beneficio verificado': 'descuento' if re.search(r'\d+% en caja', detail) else '',
            'Vigencia de identidad campaña': row['Vigencia'],
            'Texto original de la fuente': row['Detalle']})
    return result


def main(data=None):
    if data is None:
        response = requests.get(API, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or not data:
            raise RuntimeError("Continental returned no merchants; preserving previous export.")
        WORK_JSON.parent.mkdir(exist_ok=True)
        WORK_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    rows = []
    for item in data:
        desc = clean(item.get("descripcion"))
        rubro = item.get("rubro") or {}
        ciudad = item.get("ciudad") or {}
        logo = item.get("logo") or {}
        rows.append(
            {
                "Categoría": rubro.get("nombre") or "Sin categoría",
                "Banco": "Continental",
                "Comercio/Promoción": clean(item.get("nombre")),
                "Cantidad de descuento / beneficio": extract_discount(item, desc),
                "Día de promoción": extract_day(desc),
                "Vigencia": extract_vigencia(desc),
                "Ciudad": ciudad.get("nombre") or "No especificado",
                "Montos / topes": extract_topes(desc),
                "Detalle": desc,
                "Logo URL": BASE + logo.get("url") if logo.get("url") else "",
                "Fuente API": API,
            }
        )

    rows = [segment for row in rows for segment in segment_row(row)]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    categories = {}
    for row in rows:
        categories.setdefault(row["Categoría"], []).append(row)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Continental - beneficios por categoria\n\n")
        f.write(f"Fuente: {API}\n\nTotal de beneficios/comercios: {len(rows)}\n\n")
        for category in sorted(categories):
            f.write(f"## {category} ({len(categories[category])})\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia | Ciudad |\n")
            f.write("|---|---|---|---|---|\n")
            for row in categories[category][:80]:
                vals = [
                    row["Comercio/Promoción"],
                    row["Cantidad de descuento / beneficio"],
                    row["Día de promoción"],
                    row["Vigencia"],
                    row["Ciudad"],
                ]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:180] for v in vals) + " |\n")
            if len(categories[category]) > 80:
                f.write(f"\n_Se omitieron {len(categories[category]) - 80} filas en este resumen; están en el CSV._\n")
            f.write("\n")

    print(f"{len(rows)} beneficios -> {OUT_CSV} and {OUT_MD}")
    for cat, cat_rows in sorted(categories.items(), key=lambda kv: kv[0])[:20]:
        print(f"{cat}: {len(cat_rows)}")


if __name__ == "__main__":
    main()
