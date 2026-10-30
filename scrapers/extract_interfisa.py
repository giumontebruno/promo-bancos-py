"""Interfisa: complete index discovery; strict, native-text contract parsing."""
import argparse
import re
import unicodedata
try:
    from .new_bank_documents import clean, numeric_dates, row, run
except ImportError:
    from new_bank_documents import clean, numeric_dates, row, run

PAGE = 'https://www.interfisa.com.py/beneficios'


def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.upper()) if unicodedata.category(c) != 'Mn')


def parse(item, text, today):
    value = clean(text)
    # Never attach a merchant to a different merchant's linked PDF.
    title = re.search(r'BASES Y CONDICIONES DE LA PROMOCI[ÓO]N\s*[“"«]([^”"»]+)', value, re.I)
    if not title or folded(item['name']) != folded(clean(title[1])):
        return [], 'review_required: index/PDF merchant identity not exact'
    validity = re.search(r'1\.\s*Vigencia\s*(.*?)\s*2\.\s*Condiciones', value, re.I)
    benefits = re.search(r'3\.\s*Beneficios\s*(.*?)\s*4\.\s*', value, re.I)
    conditions = re.search(r'2\.\s*Condiciones\s*(.*?)\s*3\.\s*Beneficios', value, re.I)
    if not validity or not benefits or not conditions:
        return [], 'review_required: unsupported document sections'
    if numeric_dates(conditions[1]) or re.search(r'fondeo|dep[oó]sito|saldo promedio|activaci[oó]n|inscripci[oó]n previa', conditions[1], re.I):
        return [], 'review_required: additional action/date eligibility'
    dates = numeric_dates(validity[1])
    if len(dates) == 2 and dates[0] <= dates[1]:
        start, end = dates
    elif len(dates) == 1 and re.search(r'v[áa]lida para el', validity[1], re.I):
        start = end = dates[0]
    else:
        return [], 'review_required: ambiguous validity'
    if end < today:
        return [], 'expired'
    strict_range = re.fullmatch(r'La Promoci[oó]n es v[áa]lida (todos los (?:d[ií]as|lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bados|domingos)) desde el \d{1,2}/\d{1,2}/\d{4} (?:hasta el|al) \d{1,2}/\d{1,2}/\d{4}\.?', validity[1], re.I)
    strict_day = re.fullmatch(r'La Promoci[oó]n es v[áa]lida para el (?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bado|domingo) \d{1,2}/\d{1,2}/\d{4}\.?', validity[1], re.I)
    if not strict_range and not strict_day:
        return [], 'review_required: additional or unsupported validity conditions'
    day_match = re.search(r'(todos los (?:d[ií]as|lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bados|domingos))', validity[1], re.I)
    if not day_match and start != end:
        return [], 'review_required: day scope absent'
    day = day_match[1] if day_match else start.strftime('%d/%m/%Y')
    block = benefits[1]
    # Only explicit prose variants are parsed. Tables, compound/additive discounts,
    # lottery/points and unqualified "hasta" percentages remain in the review queue.
    clauses = re.findall(r'[•]\s*(.*?)(?=[•]|Tope de compra|$)', block, re.I)
    purchase = re.search(r'Tope de compra mensual de Gs\.?\s*([\d.]+)\s*por cuenta de tarjeta, incluyendo las tarjetas adicionales', block, re.I)
    if not clauses or not purchase:
        return [], 'review_required: unsupported benefit/cap template'
    locals_match = re.search(r'4\.\s*Locales adheridos\s*(.*?)\s*5\.\s*Tarjetas excluidas', value, re.I)
    excludes = re.search(r'5\.\s*Tarjetas excluidas\s*(.*?)\s*6\.', value, re.I)
    if not locals_match or not excludes:
        return [], 'review_required: missing location/exclusion scope'
    shared_terms = block[block.lower().find('tope de compra'):].strip()
    if '%' in shared_terms:
        return [], 'review_required: additional benefit in shared terms'
    rows = []
    for index, clause in enumerate(clauses):
        refund = re.fullmatch(r'(\d{1,2})% de reintegro con las afinidades (.+?)\. M[áa]ximo de reintegro Gs\.?\s*([\d.]+)', clause.strip(' .'), re.I)
        financing = re.fullmatch(r'Hasta (\d{1,2}) cuotas sin intereses con las afinidades (.+)', clause.strip(' .'), re.I)
        if refund:
            rate, cards, cap = refund.groups()
            benefit = f'{rate}% de reintegro'
            caps = f'Tope de compra mensual: Gs. {purchase[1]} por cuenta de tarjeta, incluyendo adicionales. Máximo de reintegro: Gs. {cap}.'
            kind = 'reintegro'
        elif financing:
            quota, cards = financing.groups()
            benefit = f'Hasta {quota} cuotas sin intereses'
            caps = 'Las bases incluyen un tope de compra mensual común. Su aplicación a las cuotas no está confirmada; consultar la cláusula original en el detalle. No se afirma financiación sin tope.'
            kind = 'cuotas_sin_intereses'
        else:
            return [], 'review_required: unparsed benefit clause'
        detail = f'{benefit} con {cards}. {caps} {validity[1]} {conditions[1]} {shared_terms} {excludes[1]}'
        record = row('Interfisa', item, text, benefit, cards, day, start, end, caps,
                     variant=f'scope-{index+1}', category=item.get('category', 'Sin categoría'), locations=locals_match[1], detail=detail)
        record['Tipo de beneficio verificado'] = kind
        if financing and not refund:
            record['Estado verificacion'] = 'unconfirmed'
            record['Aplicabilidad de tope a cuotas'] = 'No confirmada; cláusula común preservada en Detalle.'
        rows.append(record)
    return rows, 'published_partial: financing cap applicability unconfirmed' if any(r.get('Estado verificacion') == 'unconfirmed' for r in rows) else 'published'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--cache'); parser.add_argument('--html')
    args = parser.parse_args()
    from pathlib import Path
    run('interfisa', PAGE, parse, cache=args.cache, html=Path(args.html).read_text() if args.html else None)
