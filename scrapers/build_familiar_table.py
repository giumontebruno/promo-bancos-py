"""Publish only Familiar records supported by readable official terms."""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from promo_backend.normalize import detect_days, detect_month_days, detect_ordinal_weekdays

MONTHS = {name: index + 1 for index, name in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split())}


def plain(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c))


def compact(value):
    return re.sub(r'\s+', ' ', value).strip()


def sections(value):
    parts = re.split(r'(?m)^\s*([1-6])\.\s+(?=[A-ZÁÉÍÓÚ])', value)
    return {int(parts[i]): compact(parts[i + 1]) for i in range(1, len(parts) - 1, 2)}


def date_range(value):
    matches = list(re.finditer(r'(\d{1,2})\s+de\s+(' + '|'.join(MONTHS) + r')(?:\s+(?:(?:de|del)\s+)?(20\d{2}))?', plain(value)))
    if len(matches) != 2:
        raise ValueError('ambiguous_dates')
    a, b = matches
    year_b = b[3]
    year_a = a[3] or year_b
    if not year_a or not year_b:
        raise ValueError('missing_year')
    start = date(int(year_a), MONTHS[a[2]], int(a[1]))
    end = date(int(year_b), MONTHS[b[2]], int(b[1]))
    if start > end:
        raise ValueError('reversed_dates')
    return start.isoformat(), end.isoformat()


def convert(row):
    if re.match(r'^(?:GASTRO\s*-|RESTAURANTES PLATINUM$)', row['merchant_name'], re.I):
        raise ValueError('campaign_requires_merchant_expansion')
    text = row.get('terms_text', '')
    if not text:
        raise ValueError('missing_terms')
    parts = sections(text)
    validity, mechanics, scope = parts.get(2, ''), parts.get(3, ''), parts.get(1, '')
    start, end = date_range(validity)
    if end < date.today().isoformat():
        raise ValueError('expired_terms')
    # Remove interval endpoint weekdays; they are not necessarily benefit weekdays.
    schedule = re.split(r'\b(?:desde|del\s+\d)', validity, maxsplit=1, flags=re.I)[0]
    schedule = re.sub(r'\bdel mes\b', 'de cada mes', schedule, flags=re.I)
    schedule = re.sub(r'todos días', 'todos los días', schedule, flags=re.I)
    if not (detect_days(schedule) or detect_month_days(schedule) or detect_ordinal_weekdays(schedule)):
        raise ValueError('unconfirmed_schedule')
    # Keep only actual benefit clauses from the PDF, including card qualifiers.
    header = re.split(r'\b(?:SUCURSAL|COMERCIO|LOCALES ADHERIDOS)\s+(?:DIRECCI[OÓ]N|SUCURSAL|LOCAL|RUBRO)', mechanics, flags=re.I)[0]
    header = re.sub(r'\b(?:doce|veinticuatro|diez|seis|dieciocho)\s*\((\d+)\)', r'\1', header, flags=re.I)
    header = re.sub(r'\b3\.\d+\s*', '\n', header)
    header = re.sub(r'^MEC[AÁ]NICA DE LA PROMOCI[OÓ]N\s*', '', header, flags=re.I)
    clauses = re.split(r'\n|[●•]|(?<=[.!])\s+(?=[A-ZÁÉÍÓÚ*])', header)
    benefit = []
    for clause in clauses:
        if not re.search(r'\d\s*%|\b\d+\s*(?:\([^)]*\)\s*)?cuotas?\s+sin\s+inter', clause, re.I):
            continue
        clause = re.sub(r'^.*?EL CLIENTE\s+(?:recibirá|podrá\s+fraccionar\s+sus\s+compras)\s*', '', clause, flags=re.I)
        clause = re.sub(r'^También podrá fraccionar sus compras\s*', '', clause, flags=re.I)
        clause = re.sub(r',?\s*el reintegro será aplicado en el extracto de sus tarjetas de crédito', '', clause, flags=re.I)
        clause = re.sub(r'^.*?\bobtendrán\s+', '', clause, flags=re.I)
        clause = re.sub(r',?\s*durante la vigencia de la promoción', '', clause, flags=re.I)
        benefit.append(clause.strip(' .'))
    if not benefit:
        raise ValueError('unconfirmed_benefit')
    if len('; '.join(benefit)) > 1000:
        raise ValueError('complex_benefit_table')
    cards = re.search(r'emitidas por EL ORGANIZADOR\s*:\s*(.*?)(?:\.\s*EL CLIENTE|en adelante)', scope, re.I)
    if not cards:
        raise ValueError('unconfirmed_cards')
    name = row['merchant_name']
    # A CMS card pointing to another merchant's PDF is not sufficient evidence.
    core_name = re.split(r'\s*-\s*(?:SHOPPING|TODOS|PLAZA|PASEO)', name, flags=re.I)[0]
    if re.sub(r'\W', '', plain(core_name)) not in re.sub(r'\W', '', plain(text)):
        raise ValueError('merchant_not_in_terms')
    exclusions = re.findall(r'No participan[^.]+\.|No aplica[^.]+\.', scope, re.I)
    caps = re.findall(r'(?:L[ií]mite|Tope)[^.]*?(?:Gs\.?\s*[\d.]+)[^.]*', header, re.I)
    categories = row.get('categories', [])
    category_map = {'gastronomia':'Gastronomía', 'farmacia':'Farmacias', 'indumentaria':'Tiendas',
                    'tiendas':'Tiendas', 'hogar-y-tecnologia':'Hogar y tecnología',
                    'supermercado-y-tiendas':'Supermercados'}
    category = next((category_map[c] for c in categories if c in category_map), 'Especiales')
    if 'combustible-estaciones-de-servicio' in categories:
        category = 'Combustible' if re.search(r'petro|copetrol|estacion', plain(name)) else 'Vehículos'
    if re.search(r'hotel|resort|viaje|planazo', plain(name)):
        category = 'Viajes'
    return {
        'Comercio': name, 'Categoria': category, 'Beneficio': '; '.join(benefit),
        'Dia': re.sub(r'^.*vigencia\s*', '', schedule, flags=re.I).strip(' ,.'), 'Vigencia': f'Desde {start} hasta {end}',
        'Locales': name, 'Localidad': '; '.join(row.get('regions', [])),
        'Montos': '; '.join(caps), 'URL detalle': row['source_url'],
        'Tarjetas verificadas': cards[1].strip(' .'),
        'Detalle': ' '.join([mechanics] + [re.sub(r'^No participan', 'No aplica a', e, flags=re.I) for e in exclusions]),
        'Texto original de la fuente': text,
    }


def main():
    source = json.loads((ROOT / 'outputs/familiar_extraction_review.json').read_text(encoding='utf-8'))
    rows, pending = [], []
    for record in source['records']:
        try:
            rows.append(convert(record))
        except ValueError as error:
            pending.append({'merchant_name': record['merchant_name'], 'source_url': record['source_url'], 'reason': str(error)})
    if not rows:
        raise ValueError('No verified Familiar records; previous catalog preserved')
    with (ROOT / 'outputs/familiar_beneficios_por_categoria.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {'checked_at': source['checked_at'], 'published': len(rows), 'pending': pending}
    (ROOT / 'outputs/familiar_source_meta.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'published': len(rows), 'pending': dict(Counter(r['reason'] for r in pending))}))


if __name__ == '__main__':
    main()
