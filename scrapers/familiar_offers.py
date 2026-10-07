"""Split only evidenced Familiar card clauses; never infer rates from nearby text."""
import hashlib
import re
import unicodedata
from promo_backend.quality import extract_limits


def compact(s):
    return re.sub(r'\s+', ' ', s).strip(' ,.')


def key(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if not unicodedata.combining(c))


def mechanics(row):
    value = row['Detalle']
    return re.split(r'\b(?:SUCURSAL(?:ES)?|COMERCIO(?:S)?|LOCALES ADHERIDOS)\s+(?:DIRECCI[OÓ]N(?:ES)?|SUCURSAL|LOCAL|RUBRO)', value, flags=re.I)[0]


def common_rules(text):
    # Preserve restrictions and shared cap scopes without copying other variants' rates.
    patterns = [r'\*?(?:Beneficios|(?:La\s+)?Promoci[oó]n(?:es)?|Promociones)\s+aplican?[^*.]+(?:\*|\.|$)',
                r'Los l[ií]mites de compra se aplican[^.]+\.',
                r'No (?:aplica|participan|acumulable)[^.]+\.',
                r'No se (?:multiplicar|sumar)[^.]+\.']
    found = []
    for pattern in patterns:
        found.extend(m[0].strip('* ') for m in re.finditer(pattern, text, re.I))
    return ' '.join(dict.fromkeys(found))


def number_words(s):
    return re.sub(r'\b(?:doce|veinticuatro|diez|seis|dieciocho)\s*\((\d+)\)', r'\1', s, flags=re.I)


def offer(row, cards, benefit, evidence, kind, day=None):
    cards = compact(re.sub(r'^cr[eé]dito\s+', '', cards, flags=re.I))
    if not cards or len(cards) > 250 or re.search(r'\d\s*%|compras|obtendr', cards, re.I):
        raise ValueError('ambiguous_variant_cards')
    result = dict(row)
    identity = key(cards) + '|' + kind
    result.update({'Beneficio':benefit, 'Tarjetas verificadas':cards,
                   'Variante':hashlib.sha256(identity.encode()).hexdigest()[:16],
                   'Tipo de variante':'premium' if 'platinum' in key(cards) and not re.search(r'oro|gold|clasic|positiva', key(cards)) else 'base',
                   'Etiqueta de variante':cards,
                   'Detalle':compact(evidence + ' ' + common_rules(mechanics(row)) + ' ' + ' '.join(re.findall(r'No aplica[^.]+\.', row['Detalle'], re.I))),
                   'Montos':'; '.join(x['evidence'] for x in extract_limits(evidence)) if kind == 'reintegro' else '',
                   'Tipo de beneficio verificado':kind})
    if day:
        result['Dia'] = day
    return result


def numbered_rate_offers(row, text):
    # Each candidate ends at the next numbered clause, never at a money separator.
    blocks = re.split(r'\b3\.\d+\.?\s+', text)
    out = []
    for block in blocks[1:]:
        m = re.match(r'Con sus tarjetas de cr[eé]dito\s+(.+?)\s+EL CLIENTE obtendr[aá]\s+(\d+)\s*%\s+de reintegro', block, re.I)
        if not m:
            continue
        # Strip subsequent unnumbered financing clause from the rate evidence.
        evidence = re.split(r'Tambi[eé]n\S*\s+podr[aá]n|Podr[aá]n fraccionar', block, maxsplit=1, flags=re.I)[0]
        out.append(offer(row, m[1], f'{m[2]}% de reintegro', evidence, 'reintegro'))
    return out


def qr_rate_offers(row, text):
    pattern = r'Tarjetas\s+([^:]+):\s*(\d+)%\s+de reintegro[^●•]*?(?=(?:[●•]\s*Tarjetas)|\*Beneficios|$)'
    out = []
    for m in re.finditer(pattern, text, re.I):
        block = m[0]
        extra = re.search(r'\+\s*(\d+)%\s+adicional pagando con QR desde la aplicaci[oó]n de Banco Familiar', block, re.I)
        if not extra:
            raise ValueError('unconfirmed_qr_variant')
        # Keep conditional bonus in the same eligibility row, not as a separate discount.
        benefit = f'{m[2]}% de reintegro + {extra[1]}% adicional pagando con QR desde la aplicación de Banco Familiar'
        quota = re.search(r'hasta\s+(\d+)\s+cuotas sin intereses', block, re.I)
        if quota:
            benefit += f'; Hasta {quota[1]} cuotas sin intereses'
        out.append(offer(row, 'Tarjetas ' + m[1], benefit, block, 'reintegro'))
    return out


def installment_schedule(text, start, end):
    # A following numbered clause or new sentence starts a different schedule.
    tail = re.split(r'\b3\.\d+|\.\s+(?=[A-ZÁÉÍÓÚ])', text[end:], maxsplit=1)[0]
    scope = text[start:end] + tail
    weekday = r'(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?)'
    explicit = re.search(r'(?:(?:solo|sólo)\s+(?:los?\s+)?|todos? los?\s+|de\s+)' + weekday + r'(?:\s*(?:y|a|al|,)\s*(?:los?\s+)?' + weekday + r')*', scope, re.I)
    daily = re.search(r'todos los d[ií]as', scope, re.I)
    if explicit and daily:
        raise ValueError('conflicting_installment_schedules')
    if explicit:
        return explicit[0]
    if daily:
        return 'todos los días'
    return None


def installment_offers(row, text):
    text = number_words(text)
    found = []
    # Explicit cards before financing; handles numbered clauses and America Shop.
    before = r'(?:con sus tarjetas de cr[eé]dito|tarjetas de cr[eé]dito de Banco Familiar)\s+([^.%]{1,250}?)(?:\s+podr[aá]n fraccionar|\s+todos los d[ií]as,.*?EL CLIENTE podr[aá] fraccionar)\s+sus (?:compras|pagos)\s+(?:hasta en|en hasta)\s+(\d+)\s+cuotas sin intereses'
    for m in re.finditer(before, text, re.I):
        if len(m[1]) > 250 or re.search(r'\d\s*%|EL CLIENTE|realicen', m[1], re.I):
            continue
        found.append((m[2], m[1], m[0], installment_schedule(text,m.start(),m.end())))
    # Explicit cards after financing; boundaries exclude the next alternative.
    after = r'(?:hasta en|en hasta|en|hasta)\s+(\d+)\s+cuotas sin intereses\s+con\s+(?:sus\s+)?(?:tarjetas|TC)\s+(.+?)(?=\s+y\s+(?:hasta|en)|[.;*]|$)'
    for m in re.finditer(after, text, re.I):
        found.append((m[1], m[2], m[0], installment_schedule(text,m.start(),m.end())))
    out = []
    for quota, cards, evidence, schedule in found:
        # No percentage or monetary limit belongs to a financing-only row.
        if re.search(r'\d\s*%|l[ií]mite|tope|SUCURSAL', cards, re.I):
            raise ValueError('ambiguous_installment_cards')
        out.append(offer(row, cards, f'Hasta {quota} cuotas sin intereses', evidence,
                         'cuotas_sin_intereses', schedule))
    # Dedup only identical evidenced card/benefit pairs.
    return list({(r['Tarjetas verificadas'],r['Beneficio']):r for r in out}.values())


def split_offers(row):
    text = mechanics(row)
    summary = row['Beneficio']
    quota_counts = set(re.findall(r'(\d+)\s+cuotas sin intereses', number_words(summary), re.I))
    tiered = bool(re.search(r'Con sus tarjetas de cr[eé]dito.+?EL CLIENTE obtendr[aá]', summary, re.I))
    qr_tiered = bool(re.search(r'Tarjetas[^:]+:\s*\d+%', summary, re.I))
    if not (tiered or qr_tiered or len(quota_counts) > 1):
        return [row]
    monetary = qr_rate_offers(row, text) if qr_tiered else numbered_rate_offers(row, text)
    if (tiered or qr_tiered) and len(monetary) < 2:
        raise ValueError('unresolved_card_variants')
    quotas = [] if qr_tiered else installment_offers(row, text)
    if len(quota_counts) > 1 and len(quotas) < len(quota_counts):
        raise ValueError('unresolved_installment_variants')
    if not monetary and re.search(r'\d+\s*%', summary):
        # One common monetary offer plus two financing alternatives. Do not split
        # pharmacy additive/product discounts by arbitrary percentage matches.
        clauses = [c for c in summary.split(';') if re.search(r'\d+\s*%', c)]
        if len(clauses) != 1 or re.search(r'descuento en caja', clauses[0], re.I):
            raise ValueError('complex_monetary_and_installment_variants')
        cutoffs = [m.start() for m in re.finditer(r'Los clientes de EL BANCO tendr[aá]n|3\.1|Tambi[eé]n podr[aá]|Los clientes de EL BANCO con sus tarjetas', text, re.I) if m.start() > 50]
        prefix = text[:min(cutoffs)] if cutoffs else text
        cards = re.search(r'con sus tarjetas de cr[eé]dito\s+(.+?),?\s+que realicen compras', prefix, re.I)
        if not cards:
            # Generic "tarjetas ... mencionadas en punto 1" must retain scope.
            if not re.search(r'mencionadas en el punto 1', prefix, re.I):
                raise ValueError('unconfirmed_shared_rate_cards')
        # A single monetary benefit can have its common purchase limit after the
        # financing sentence (Cycles Shop). Preserve labeled limits, never infer
        # from arbitrary amounts or copy other tiers' caps.
        existing = {(x['kind'],x['amount']) for x in extract_limits(prefix)}
        missing = [x for x in extract_limits(text) if (x['kind'],x['amount']) not in existing]
        for limit in missing:
            # Evidence from a regex can run beyond a missing PDF punctuation mark.
            bounded = re.split(r'Los clientes|Con sus tarjetas|3\.\d+|\*',limit['evidence'],maxsplit=1,flags=re.I)[0]
            prefix += ' ' + bounded
        monetary = [offer(row, cards[1] if cards else row['Tarjetas verificadas'], compact(clauses[0]), prefix, 'reintegro')]
    # Common ten-installment clause is a separate daily offer, not repeated per tier.
    if not qr_tiered and not quotas and len(quota_counts) == 1:
        common = re.search(r'Podr[aá]n fraccionar sus compras, todos los d[ií]as en hasta (\d+) cuotas sin intereses', text, re.I)
        if common:
            eligible = re.search(r'con sus tarjetas de cr[eé]dito\s+(.+?),\s+que realicen compras', text, re.I)
            if not eligible:
                raise ValueError('unconfirmed_shared_installment_cards')
            quotas = [offer(row, eligible[1], f'Hasta {common[1]} cuotas sin intereses', common[0], 'cuotas_sin_intereses', 'todos los días')]
    result = monetary + quotas
    if not result:
        raise ValueError('unresolved_variants')
    if len({r['Variante'] for r in result}) != len(result):
        raise ValueError('ambiguous_variant_identity')
    return result
