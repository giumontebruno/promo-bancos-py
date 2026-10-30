"""Basa: discover the entire official index and publish unambiguous single scopes.

Tables with differing card tiers are not flattened into a misleading maximum.
"""
import argparse
import json
from pathlib import Path
import re
from datetime import date
try:
    from .new_bank_documents import clean, row, run, MONTHS
except ImportError:
    from new_bank_documents import clean, row, run, MONTHS

PAGE = 'https://www.bancobasa.com.py/promociones-personas'
REVIEWS = json.loads((Path(__file__).resolve().parents[1] / 'data/basa_document_reviews.json').read_text())['campaigns']


def parse(item, text, today):
    for review in REVIEWS:
        if item['url'] != review['url']:
            continue
        if item.get('sha256') != review['sha256']:
            return [], 'review_required: previously reviewed document changed'
        end = date.fromisoformat(review['ends_on'])
        if end < today:
            return [], 'expired'
        rows = []
        for merchant in review['merchants']:
            start = review.get('merchant_starts', {}).get(merchant, review.get('starts_on'))
            for scope in review['scopes']:
                caps = scope.get('caps', review['caps'])
                detail = f"{scope['benefit']} con {scope['cards']}. {caps} {review['conditions']}"
                record = row('Basa', {**item, 'name': merchant}, text, scope['benefit'], scope['cards'],
                             scope.get('day', review['day']), date.fromisoformat(start) if start else None,
                             end, caps, scope['key'], review['category'], detail=detail)
                record['Tipo de beneficio verificado'] = 'reintegro'
                rows.append(record)
        return rows, 'published_partial: nationwide financing scope not mapped' if review['name'] == 'HOTELES' else 'published'
    value = clean(text)
    expiry = re.findall(r'Vigencia:\s*(.*?)hasta el (\d{1,2}) de (\w+) de (\d{4})', value, re.I)
    if len(expiry) != 1 or expiry[0][2].lower() not in MONTHS:
        return [], 'review_required: ambiguous/unsupported validity'
    days, day, month, year = expiry[0]
    end = date(int(year), MONTHS[month.lower()], int(day))
    if end < today:
        return [], 'expired'
    if not re.fullmatch(r'todos los (?:d[ií]as|lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bados|domingos)\s*', days, re.I):
        return [], 'review_required: unsupported recurrence/start'
    # Exact title or exact merchant reference required; no fuzzy name matching.
    name = clean(item['name']).upper()
    if name not in value.upper()[:1000]:
        return [], 'review_required: index/PDF merchant identity not exact'
    card_match = re.search(r'seleccionadas citadas a continuaci[oó]n:\s*(Visa Cl[áa]sica,.*?Afinidad Club Libertad\.)', value, re.I)
    if not card_match:
        return [], 'review_required: unsupported card scope'
    # An additional explicit tier outside the standard list means a table needs review.
    before = value[:card_match.start()]
    if re.search(r'Master\s*Card Black|Visa Signature|MasterCard Oro', before, re.I):
        return [], 'review_required: multiple card tiers'
    rates = set(re.findall(r'\b(?:Hasta\s+)?\d{1,2}\s*%', value, re.I))
    quotas = set(re.findall(r'\bHasta\s+(\d{1,2})\b(?!\s*%)', value, re.I))
    if len(rates) > 1 or len(quotas) > 1:
        return [], 'review_required: multiple benefit scopes'
    # Exclude conditional or per-product scopes from automatic scalar extraction.
    if re.search(r'd[eé]bito autom[aá]tico|primera cuota|productos seleccionados|compras m[ií]nimas', value, re.I):
        return [], 'review_required: conditional scope'
    table_refund = re.search(r'Beneficios tarjetas seleccionadas\s*:\s*Reintegro\s*(\d{1,2})%', before, re.I)
    table_discount = re.search(r'Beneficios tarjetas seleccionadas\s*:\s*Descuento\s*En caja', before, re.I)
    if rates and not (table_refund or table_discount):
        return [], 'review_required: unsupported benefit table'
    if not rates and not quotas:
        return [], 'review_required: missing benefit amount'
    parts = []
    if rates:
        parts.append(next(iter(rates)) + (' de reintegro' if table_refund else ' de descuento en caja'))
    if quotas and re.search(r'Cuotas\s*sin intereses', value, re.I):
        parts.append('Hasta ' + next(iter(quotas)) + ' cuotas sin intereses')
    elif quotas:
        return [], 'review_required: quota meaning unclear'
    caps = re.findall(r'(?:tope de compra|tope de reintegro)[^.]*?Gs\.?\s*[\d.]+\.-?[^.]*', value, re.I)
    caps = [re.sub(r'por mes', 'mensual', cap, flags=re.I) for cap in caps]
    caps = '; '.join(caps) if caps else 'No especificado en las bases; no implica beneficio ilimitado.'
    record = row('Basa', item, text, ' + '.join(parts), card_match[1], days.strip(), None, end, caps)
    if table_refund: record['Tipo de beneficio verificado'] = 'reintegro'
    elif rates: record['Tipo de beneficio verificado'] = 'descuento'
    else: record['Tipo de beneficio verificado'] = 'cuotas_sin_intereses'
    return [record], 'published'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--cache'); parser.add_argument('--html')
    args = parser.parse_args()
    from pathlib import Path
    run('basa', PAGE, parse, cache=args.cache, html=Path(args.html).read_text() if args.html else None)
