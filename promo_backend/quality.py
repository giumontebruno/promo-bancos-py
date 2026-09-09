"""Conservative normalization: every extracted condition retains its evidence."""

import calendar
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import date

MONTHS = {name: i for i, name in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1
)}
MONEY = r"(?:Gs\.?|G\.|guaran[ií]es)\s*([0-9]+(?:[. ,][0-9]{3})*)"


def text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def key(value):
    return "".join(c for c in unicodedata.normalize("NFKD", text(value).casefold())
                   if not unicodedata.combining(c))


def sentence(value):
    value = text(value)
    if value.isupper():
        value = value.lower()
    for pattern, replacement in [(r"\bvisa\b", "Visa"), (r"\bmastercard\b", "Mastercard"),
                                 (r"\bqr\b", "QR"), (r"\bbnf\b", "BNF"),
                                 (r"\bapple pay\b", "Apple Pay"), (r"\bgoogle pay\b", "Google Pay")]:
        value = re.sub(pattern, replacement, value, flags=re.I)
    value = re.sub(r"(\d)\s+%", r"\1%", value)
    value = re.sub(r",\s*\.", ".", value)
    return value[:1].upper() + value[1:]


def sentences(value):
    # Periods in Gs., S.A. and 500.000 must not split an amount or company.
    return list(dict.fromkeys(text(part) for part in re.split(
        r"(?<!Gs)(?<!gs)(?<!Sr)(?<!Dr)(?<!Av)\.(?=\s+[A-ZÁÉÍÓÚÑ])|[;\n●•]+", str(value or "")
    ) if text(part)))


def parse_date(value):
    value = key(value).strip(" .")
    iso = re.fullmatch(r"(20\d{2})-(\d{1,2})-(\d{1,2})", value)
    numeric = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", value)
    written = re.fullmatch(r"(\d{1,2})\s+de\s+(\w+)\s+(?:(?:de|del)\s+)?(20\d{2})", value)
    try:
        if iso:
            return date(*map(int, iso.groups())).isoformat()
        if numeric:
            d, m, y = map(int, numeric.groups())
            return date(y, m, d).isoformat()
        if written:
            d, m, y = written.groups()
            return date(int(y), MONTHS[m], int(d)).isoformat()
    except (ValueError, KeyError):
        pass
    return None


DATE_PATTERN = r"(?:20\d{2}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2}|\d{1,2}\s+de\s+\w+\s+(?:(?:de|del)\s+)?20\d{2})"


def validity_dates(value):
    value = key(value)
    starts = [parse_date(m.group(1)) for m in re.finditer(r"(?:desde|del)\s+(?:el\s+)?(" + DATE_PATTERN + ")", value)]
    ends = [parse_date(m.group(1)) for m in re.finditer(r"(?:hasta|al)\s+(?:el\s+)?(" + DATE_PATTERN + ")", value)]
    if parse_date(value):
        ends.append(parse_date(value))
    monthly = re.fullmatch(r"([a-z]+)\s+(20\d{2})", value)
    if monthly and monthly[1] in MONTHS:
        y, m = int(monthly[2]), MONTHS[monthly[1]]
        starts.append(date(y, m, 1).isoformat())
        ends.append(date(y, m, calendar.monthrange(y, m)[1]).isoformat())
    # Conflicting date ranges are flagged, never silently extended to the latest date.
    starts, ends = sorted(set(filter(None, starts))), sorted(set(filter(None, ends)))
    return {"starts_on": starts[0] if len(starts) == 1 else None,
            "ends_on": ends[0] if len(ends) == 1 else None,
            "conflicting_dates": len(starts) > 1 or len(ends) > 1}


def extract_limits(value):
    labels = {
        "purchase": r"(?:tope|l[ií]mite)(?:\s+(?:m[aá]ximo|mensual|semanal|diario))?\s+(?:de\s+)?compra",
        "refund": r"(?:tope(?:\s+de)?|l[ií]mite(?:\s+de)?|m[aá]ximo(?:\s+de)?)\s+reintegro|reintegro\s+m[aá]ximo",
        "minimum": r"(?:compra|monto)\s+m[ií]nimo|m[ií]nimo\s+de\s+compra",
    }
    result = []
    for part in sentences(value):
        markers = sorted((match.start(), match.end(), kind) for kind, pattern in labels.items()
                         for match in re.finditer(pattern, part, re.I))
        for index, (start, end, kind) in enumerate(markers):
            stop = markers[index + 1][0] if index + 1 < len(markers) else len(part)
            scope = part[start:stop]
            amounts = list(re.finditer(MONEY, scope, re.I))
            if len(amounts) != 1:
                continue
            value_number = int(re.sub(r"\D", "", amounts[0][1]))
            period = next((p for p in ("mensual", "semanal", "diario") if p in key(part)), None)
            result.append({"kind": kind, "amount": value_number, "currency": "PYG",
                           "period": period, "evidence": sentence(scope)})
    return list({json.dumps(x, sort_keys=True): x for x in result}.values())


def normalize_terms(promo):
    raw = text(promo.get("raw_detail"))
    limits = extract_limits(raw) or extract_limits(promo.get("caps_and_minimums"))
    dates = validity_dates(promo.get("validity"))
    period_end = parse_date(promo.get("source_period_end"))
    if period_end:
        dates["ends_on"] = min(filter(None, (period_end, dates["ends_on"])))
    parts = sentences(raw)
    exclusions = []
    cards = []
    additional = []
    for part in parts:
        excluded = re.search(r"(?:no aplica|se excluyen|quedan excluidas?)[^.●;]+", part, re.I)
        if excluded and re.search(r"tarjet|QR|POS|pago|compra|red |infonet|dinelco", excluded[0], re.I):
            exclusions.append(sentence(excluded[0]))
        if not excluded:
            for match in re.finditer(r"\btarjetas?\s+(?:de\s+)?(?:cr[eé]dito|d[eé]bito)\s+([^.;●:]+)", part, re.I):
                eligible = re.split(r"\b(?:emitid[ao]s?|realizad[ao]s?|el beneficio|se acreditar|se aplic|seg[uú]n|ser[aá])\b", match[0], maxsplit=1, flags=re.I)[0].strip(' ,')
                if len(eligible) <= 250 and not re.search(r"\d\s*%|d[ií]as h[aá]biles|tope|reintegro|\bplazo\b", eligible, re.I):
                    cards.append(sentence(eligible))
        if re.search(r"no (?:es|son) acumulable|no se (?:sumar|multiplicar)|plazo de acreditaci[oó]n|hasta \d+ d[ií]as h[aá]biles|\b(?:POS|VPOS|QR|Upay|Infonet)\b", part, re.I):
            if len(part) <= 550 and not re.search(r"bases y condiciones.*vigencia", part, re.I):
                additional.append(sentence(part))
    cards, exclusions, additional = [list(dict.fromkeys(items)) for items in (cards, exclusions, additional)]
    def card_tokens(value):
        return set(re.findall(r'\w+', key(value))) - {'tarjeta', 'tarjetas', 'de', 'credito', 'debito', 'y', 'o', 'ueno', 'bank'}
    specific_cards = []
    for card in sorted(cards, key=lambda value: len(card_tokens(value)), reverse=True):
        tokens = card_tokens(card)
        if not any(tokens <= card_tokens(existing) for existing in specific_cards):
            specific_cards.append(card)
    cards = specific_cards
    additional = [part for part in additional if part not in exclusions and not part.endswith(':')
                  and not re.search(r'aplica exclusivamente.*tarjetas', part, re.I)]
    timing = re.search(r'hasta\s+(\d+)\s+d[ií]as h[aá]biles', raw, re.I)
    if timing:
        additional = [part for part in additional if not re.search(r'd[ií]as h[aá]biles', part, re.I)]
        additional.append(f'Acreditación del reintegro: hasta {timing[1]} días hábiles.')
    if exclusions and all('qr' in key(part) and 'ueno' in key(part) for part in exclusions):
        exclusions = ['No aplica a pagos con código QR, incluidos los de la app ueno.']
    issues = []
    if not dates["ends_on"]:
        issues.append("validity_unconfirmed")
    if dates["conflicting_dates"]:
        issues.append("conflicting_dates")
    if not promo.get("source_url"):
        issues.append("missing_source")
    if "\ufffd" in raw:
        issues.append("damaged_source_text")
    if promo.get("caps_and_minimums") and not limits:
        issues.append("limits_unconfirmed")
    for kind in ("purchase", "refund", "minimum"):
        if len({x["amount"] for x in limits if x["kind"] == kind}) > 1:
            issues.append(f"multiple_{kind}_limits")
    return {"version": 1, **dates, "limits": limits, "cards": cards,
            "exclusions": exclusions, "additional": additional, "issues": issues,
            "status": "needs_review" if issues else "parsed"}


def deduplicate(promotions):
    unique, seen, ids, aliases = [], {}, set(), {}
    fields = ("bank", "merchant_name", "merchant_locations_or_group", "benefit_summary",
              "day_text", "validity", "caps_and_minimums", "level_rules", "raw_detail")
    for original in promotions:
        promo = dict(original)
        fingerprint = hashlib.sha256(json.dumps([key(promo.get(f)) for f in fields],
                                                ensure_ascii=False).encode()).hexdigest()
        if fingerprint in seen:
            if promo["id"] != seen[fingerprint]:
                aliases[promo["id"]] = seen[fingerprint]
            continue
        if promo["id"] in ids:
            promo["id"] += "-" + fingerprint[:8]
        ids.add(promo["id"])
        seen[fingerprint] = promo["id"]
        promo["terms"] = normalize_terms(promo)
        unique.append(promo)
    # An existing id must never redirect to a different, surviving benefit.
    return unique, {a: b for a, b in aliases.items() if a not in ids}


def quality_report(promotions, original_count, aliases):
    return {"input_count": original_count, "promotion_count": len(promotions),
            "duplicates_removed": original_count - len(promotions), "favorite_aliases": aliases,
            "by_bank": dict(Counter(p["bank"] for p in promotions)),
            "issue_counts": dict(Counter(issue for p in promotions for issue in p["terms"]["issues"])),
            "review_queue": [{"id": p["id"], "bank": p["bank"], "merchant": p["merchant_name"],
                              "issues": p["terms"]["issues"], "source_url": p.get("source_url")}
                             for p in promotions if p["terms"]["issues"]]}


def favorite_aliases(previous, current, existing=None):
    def identity(promo):
        return tuple(key(promo.get(field)) for field in ('bank', 'merchant_name', 'category'))
    candidates = {}
    for promo in current:
        candidates.setdefault(identity(promo), []).append(promo['id'])
    ids = {p['id'] for p in current}
    aliases = dict(existing or {})
    for promo in previous:
        matches = candidates.get(identity(promo), [])
        if promo['id'] not in ids and len(matches) == 1:
            aliases[promo['id']] = matches[0]
    for original, target in list(aliases.items()):
        seen = {original}
        while target in aliases and target not in seen:
            seen.add(target)
            target = aliases[target]
        if target in ids and original not in ids:
            aliases[original] = target
        else:
            aliases.pop(original, None)
    return aliases
