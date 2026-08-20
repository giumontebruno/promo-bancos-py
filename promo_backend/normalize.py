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
    if re.search(r"todos los d[ií]as|todos los dias", haystack):
        return ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    days = []
    for raw, normalized in DAY_ALIASES.items():
        if re.search(rf"\b{re.escape(raw)}\b", haystack):
            days.append(normalized)
    return list(dict.fromkeys(days))


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


def normalize_row(bank, row):
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
    caps = first(row, "Montos / topes", "Tope detectado", "Montos", "Topes")
    levels = first(row, "Descuentos por nivel", "Beneficio por niveles")
    source_url = first(row, "URL detalle", "URL", "Bases / PDF URL", "Fuente API", "Bases y condiciones URL")
    detail = first(row, "Detalle", "Texto completo", "Texto bases", "Texto bases y condiciones")

    normalized = {
        "bank": bank,
        "category": category,
        "merchant_name": merchant or merchants or category,
        "merchant_locations_or_group": merchants,
        "benefit_summary": benefit,
        "benefit_type": detect_benefit_type(" ".join([benefit, levels, detail])),
        "percentages": detect_percentages(" ".join([benefit, levels, detail])),
        "promotion_days": detect_days(day_text, detail),
        "day_text": day_text or "No especificado",
        "validity": validity,
        "caps_and_minimums": caps,
        "level_rules": levels,
        "source_url": source_url,
        "raw_detail": detail[:4000],
    }
    normalized["id"] = row_id(normalized)
    return normalized


def load_promotions():
    promotions = []
    for bank, path in SOURCE_FILES:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                promotions.append(normalize_row(bank, row))
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
