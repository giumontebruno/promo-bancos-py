import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
PUBLIC = ROOT / "public"
DATA = ROOT / "data"


SOURCE_FILES = [
    ("Sudameris", OUTPUTS / "sudameris_beneficios_por_categoria.csv"),
    ("Itaú", OUTPUTS / "itau_beneficios_por_categoria.csv"),
    ("BNF", OUTPUTS / "bnf_beneficios_por_categoria.csv"),
    ("Continental", OUTPUTS / "continental_beneficios_por_categoria.csv"),
    ("ueno bank", OUTPUTS / "ueno_beneficios_por_categoria.csv"),
]


DAY_ALIASES = {
    "lunes": "lunes",
    "martes": "martes",
    "miercoles": "miércoles",
    "miércoles": "miércoles",
    "jueves": "jueves",
    "viernes": "viernes",
    "sabado": "sábado",
    "sábado": "sábado",
    "sabados": "sábado",
    "sábados": "sábado",
    "domingo": "domingo",
    "domingos": "domingo",
}


def clean(text):
    replacements = {
        "�": "é",
        "Mi�rcoles": "Miércoles",
        "mi�rcoles": "miércoles",
        "cr�dito": "crédito",
        "Cr�dito": "Crédito",
        "computar�": "computará",
        "m�ximo": "máximo",
        "Promoci�n": "Promoción",
    }
    value = str(text or "")
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"\s+", " ", value).strip()


def first(row, *names):
    for name in names:
        if clean(row.get(name)):
            return clean(row.get(name))
    return ""


def detect_days(*texts):
    haystack = " ".join(clean(t).lower() for t in texts)
    if detect_month_days(haystack):
        return []
    ordinal_rules = detect_ordinal_weekdays(haystack)
    if ordinal_rules:
        return list(dict.fromkeys(rule["day"] for rule in ordinal_rules))
    if re.search(r"todos los d[ií]as|todos los dias", haystack):
        return ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    days = detect_day_ranges(haystack)
    for raw, normalized in DAY_ALIASES.items():
        if re.search(rf"\b{re.escape(raw)}\b", haystack):
            days.append(normalized)
    return list(dict.fromkeys(days))


def detect_day_ranges(*texts):
    haystack = " ".join(clean(t).lower() for t in texts)
    order = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    day_pattern = "|".join(re.escape(day) for day in DAY_ALIASES)
    ranges = []
    for match in re.finditer(rf"\b(?:de\s+)?({day_pattern})\s+a\s+({day_pattern})\b", haystack):
        start_day = DAY_ALIASES[match.group(1)]
        end_day = DAY_ALIASES[match.group(2)]
        start = order.index(start_day)
        end = order.index(end_day)
        if start <= end:
            ranges.extend(order[start : end + 1])
        else:
            ranges.extend(order[start:] + order[: end + 1])
    return list(dict.fromkeys(ranges))


def detect_month_days(*texts):
    haystack = " ".join(clean(t).lower() for t in texts)
    found = []
    for match in re.finditer(r"\b(?:d[ií]a\s*)?([0-3]?\d)\s+de\s+cada\s+mes\b", haystack):
        day = int(match.group(1))
        if 1 <= day <= 31:
            found.append(day)
    return list(dict.fromkeys(found))


def detect_ordinal_weekdays(*texts):
    haystack = " ".join(clean(t).lower() for t in texts)
    ordinal_words = {
        "primer": 1,
        "primero": 1,
        "primera": 1,
        "segundo": 2,
        "segunda": 2,
        "tercer": 3,
        "tercero": 3,
        "tercera": 3,
        "cuarto": 4,
        "cuarta": 4,
        "ultimo": -1,
        "último": -1,
        "ultima": -1,
        "última": -1,
    }
    rules = []
    day_pattern = "|".join(re.escape(day) for day in DAY_ALIASES)
    ordinal_pattern = "|".join(ordinal_words)
    for match in re.finditer(rf"\b({ordinal_pattern})\s+((?:{day_pattern})(?:\s+y\s+(?:{day_pattern}))*)\s+de\s+cada\s+mes\b", haystack):
        ordinal = ordinal_words[match.group(1)]
        day_text = match.group(2)
        for raw, normalized in DAY_ALIASES.items():
            if re.search(rf"\b{re.escape(raw)}\b", day_text):
                rules.append({"ordinal": ordinal, "day": normalized})
    for match in re.finditer(rf"\bsolo\s+el\s+({ordinal_pattern})\s+((?:{day_pattern})(?:\s+y\s+(?:{day_pattern}))*)\b", haystack):
        ordinal = ordinal_words[match.group(1)]
        day_text = match.group(2)
        for raw, normalized in DAY_ALIASES.items():
            if re.search(rf"\b{re.escape(raw)}\b", day_text):
                rules.append({"ordinal": ordinal, "day": normalized})
    return [dict(t) for t in {tuple(rule.items()) for rule in rules}]


def detect_benefit_type(text):
    text = clean(text).lower()
    if "cuota" in text and "sin inter" in text:
        return "cuotas_sin_intereses"
    if "reintegro" in text:
        return "reintegro"
    if "descuento" in text:
        return "descuento"
    return "beneficio"


def detect_percentages(text):
    return list(dict.fromkeys(re.findall(r"\d{1,3}\s*%", clean(text))))


def row_id(row):
    base = "|".join(
        [
            row.get("bank", ""),
            row.get("merchant_name", ""),
            row.get("category", ""),
            row.get("validity", ""),
            row.get("source_url", ""),
        ]
    )
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def normalize_row(bank, row, merchant_override=None, group_override=None, category_override=None):
    category = first(row, "Categoría", "Categoria", "category") or "Sin categoría"
    merchant = first(
        row,
        "Comercio/Promoción",
        "Comercio/Promocion",
        "Comercio",
        "Promoción",
        "Promocion",
    )
    benefit = first(
        row,
        "Cantidad de descuento / beneficio",
        "% detectado",
        "Beneficios",
        "Beneficio",
        "Detalle",
    )
    day_text = first(row, "Día de promoción", "Dia de promoción", "Día", "Dia")
    validity = first(row, "Vigencia", "Hasta", "Desde")
    merchants = first(row, "Locales / comercios detectados", "Locales / comercios incluidos", "Locales")
    location = first(row, "Localidad", "Ciudad", "Departamento", "Ubicación", "Ubicacion")
    caps = first(row, "Montos / topes", "Tope detectado", "Montos", "Topes")
    levels = first(row, "Descuentos por nivel", "Beneficio por niveles")
    source_url = first(row, "URL detalle", "URL", "Bases / PDF URL", "Fuente API", "Bases y condiciones URL")
    detail = first(row, "Detalle", "Texto completo", "Texto bases", "Texto bases y condiciones")

    normalized = {
        "bank": bank,
        "category": category_override or category,
        "merchant_name": merchant_override or merchant or merchants or category,
        "merchant_locations_or_group": group_override if group_override is not None else merchants or location,
        "benefit_summary": benefit,
        "benefit_type": detect_benefit_type(" ".join([benefit, levels, detail])),
        "percentages": detect_percentages(" ".join([benefit, levels, detail])),
        "promotion_days": detect_days(day_text, validity, detail),
        "month_days": detect_month_days(day_text, validity, detail),
        "ordinal_weekdays": detect_ordinal_weekdays(day_text, validity, detail),
        "day_text": day_text or "No especificado",
        "validity": validity,
        "caps_and_minimums": caps,
        "level_rules": levels,
        "source_url": source_url,
        "raw_detail": detail[:4000],
    }
    normalized["id"] = row_id(normalized)
    return normalized


def split_merchant_list(value):
    text = clean(value)
    if not text or text.lower().startswith(("no aplica", "ver detalle", "publicidad")):
        return []
    if any(phrase in text.lower() for phrase in ["promoción válida", "aplica exclusivamente", "beneficio válido"]):
        return []
    merchants = [clean(part) for part in text.split(";")]
    merchants = [merchant for merchant in merchants if merchant and len(merchant) <= 80]
    return list(dict.fromkeys(merchants))


def should_skip_ueno_row(row):
    category = clean(row.get("Categoría")).lower()
    merchant = clean(row.get("Comercio/Promoción")).lower()
    detail = clean(row.get("Detalle")).lower()
    return (
        category == "beneficios del mes"
        and ("publicidad" in detail or "publicidad" in merchant or "ahorrá más con" in merchant)
    )


def infer_ueno_category(category, merchant, group):
    if clean(category).lower() != "beneficios del mes":
        return category
    haystack = clean(" ".join([merchant, group])).lower()
    rules = [
        ("Combustible", ["petropar", "copetrol", "enex", "petrobras", "puma energy", "petrochaco", "petromax"]),
        ("Supermercados", ["kingo", "ahorrazo", "salemma", "superseis", "stock", "delimarket", "real"]),
        ("Farmacias", ["farmacia", "farmacenter", "biggie farma", "drugstore", "farmatotal", "isalú", "isalu"]),
        ("Viajes", ["hotel", "cabaña", "cabañas", "oasis dream", "planazo", "quinta la paloma"]),
        ("Entretenimiento", ["club", "deportes", "academia", "gym", "pilates", "feria", "flight", "virtuality"]),
        ("Tiendas", ["joyas", "joyería", "joyeria", "vernier", "koala"]),
    ]
    for inferred, needles in rules:
        if any(needle in haystack for needle in needles):
            return inferred
    return "Especiales"


def normalize_source_row(bank, row):
    if bank != "ueno bank":
        return [normalize_row(bank, row)]
    if should_skip_ueno_row(row):
        return []
    original_category = first(row, "Categoría", "Categoria", "category") or "Sin categoría"
    original_group = first(row, "Comercio/Promoción", "Comercio/Promocion", "Comercio", "Promoción", "Promocion")
    merchants = split_merchant_list(first(row, "Locales / comercios detectados", "Locales / comercios incluidos", "Locales"))
    if len(merchants) == 1:
        category = infer_ueno_category(original_category, merchants[0], original_group)
        return [normalize_row(bank, row, merchant_override=merchants[0], group_override=original_group, category_override=category)]
    if len(merchants) == 0:
        category = infer_ueno_category(original_category, original_group, "")
        return [normalize_row(bank, row, category_override=category)]
    return [
        normalize_row(
            bank,
            row,
            merchant_override=merchant,
            group_override=original_group,
            category_override=infer_ueno_category(original_category, merchant, original_group),
        )
        for merchant in merchants
    ]


def load_promotions():
    promotions = []
    for bank, path in SOURCE_FILES:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                promotions.extend(normalize_source_row(bank, row))
    promotions.sort(key=lambda r: (r["bank"], r["category"], r["merchant_name"]))
    return promotions


def write_csv(path, rows):
    fieldnames = [
        "id",
        "bank",
        "category",
        "merchant_name",
        "merchant_locations_or_group",
        "benefit_summary",
        "benefit_type",
        "percentages",
        "promotion_days",
        "month_days",
        "ordinal_weekdays",
        "day_text",
        "validity",
        "caps_and_minimums",
        "level_rules",
        "source_url",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["percentages"] = "; ".join(out["percentages"])
            out["promotion_days"] = "; ".join(out["promotion_days"])
            out["month_days"] = "; ".join(str(day) for day in out.get("month_days", []))
            out["ordinal_weekdays"] = "; ".join(
                f"{rule.get('ordinal')}:{rule.get('day')}" for rule in out.get("ordinal_weekdays", [])
            )
            writer.writerow({k: out.get(k, "") for k in fieldnames})


def main():
    PUBLIC.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)

    promotions = load_promotions()
    now = datetime.now(timezone.utc).isoformat()
    categories = sorted({p["category"] for p in promotions if p["category"]})
    banks = sorted({p["bank"] for p in promotions if p["bank"]})
    by_day = {day: [] for day in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}
    by_category = {category: [] for category in categories}

    for promo in promotions:
        for day in promo["promotion_days"]:
            by_day.setdefault(day, []).append(promo["id"])
        by_category.setdefault(promo["category"], []).append(promo["id"])

    manifest = {
        "generated_at": now,
        "promotion_count": len(promotions),
        "banks": banks,
        "categories": categories,
        "source_files": [str(path.relative_to(ROOT)) for _, path in SOURCE_FILES],
    }

    (PUBLIC / "promotions.json").write_text(json.dumps(promotions, ensure_ascii=False, indent=2), encoding="utf-8")
    (PUBLIC / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (PUBLIC / "index_by_day.json").write_text(json.dumps(by_day, ensure_ascii=False, indent=2), encoding="utf-8")
    (PUBLIC / "index_by_category.json").write_text(json.dumps(by_category, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(PUBLIC / "promotions.csv", promotions)
    write_csv(DATA / "promotions.csv", promotions)
    print(f"Normalized {len(promotions)} promotions into public/promotions.json")


if __name__ == "__main__":
    main()
