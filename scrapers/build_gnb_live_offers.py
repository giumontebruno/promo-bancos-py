"""Build GNB app offers from matched live cards and readable official terms."""

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data/gnb_live_cards_2026-09-22.json"
REVIEW = ROOT / "outputs/gnb_card_pdf_review_2026-09-22.csv"
BASE_URL = "https://www.beneficiosbancognb.com.py/v2/beneficios/categorias/"

EXISTING = {148, 408, 598, 313, 73, 260, 543, 607}
EXCLUDE = {20, 157, 297}
WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
DAY_PATTERN = r"lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?"


def compact(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def category(title, summary):
    value = f"{title} {summary}".casefold()
    rules = [
        ("Combustible", ("petrobras", "petrochaco", "petrosur", "puma", "copetrol", "combustible", "estaciones de servicio")),
        ("Farmacias", ("farmacenter", "farmatotal", "farmalife", "farmavip", "farma", "farmacia", "drugstore", "dermocosmética", "isdin")),
        ("Supermercados", ("supermercado", "ahorramás", "jullito", "areté", "festa")),
        ("Gastronomía", ("gastronómica", "café", "restó", "bistro", "grill", "sushi", "poke", "restaurante", "burger king", "subway", "popeyes", "almacén fd", "asado benitez", "malandras")),
        ("Entretenimiento", ("cinemark", "cine", "padel", "gym", "sommelier")),
        ("Viajes", ("viajes", "travel", "safebag", "agencia", "aerolínea")),
        ("Vehículos", ("autocentro", "garden", "jeep", "automaq", "tonina", "taller", "cubierta", "neumático")),
        ("Tecnología", ("electrónica", "nissei", "cell", "compumarket", "gadget", "mercado digital")),
        ("Hogar y construcción", ("muebles", "hogar", "ferrex", "ferre", "jardín", "decoración")),
        ("Salud y belleza", ("spa", "peluquería", "belleza", "bienestar", "óptica", "clínica", "odontología")),
    ]
    for name, words in rules:
        if any(word in value for word in words):
            return name
    return "Tiendas"


def benefit_bullets(value):
    return [compact(part) for part in re.split(r"\s*•\s*", value or "") if compact(part)]


def has_installments(value):
    return bool(re.search(r"\b\d{1,2}\s+cuotas?\s+sin\s+intereses\b", value, re.I))


def day_text(summary, conditions, benefit, installments):
    if re.search(r"jueves\s+y\s+viernes\s+de\s+la\s+tercera\s+semana", conditions, re.I):
        return "tercer jueves y viernes de cada mes"
    if re.search(r"beneficio\s+v[aá]lid[oa]\s+todos\s+los\s+d[ií]as", conditions, re.I):
        return "Todos los días"
    if installments:
        if re.search(r"cuotas?\s+sin\s+intereses.{0,45}todos\s+los\s+d[ií]as", conditions, re.I) or re.search(r"cuotas?\s+sin\s+intereses.{0,30}todos\s+los\s+d[ií]as", summary, re.I):
            return "Todos los días"
    else:
        if re.search(r"(?:descuento|reintegro).{0,65}todos\s+los\s+d[ií]as", conditions, re.I):
            return "Todos los días"

    relevant = summary.split("+")[0] if not installments else summary.rsplit("+", 1)[-1]
    relevant = f"{relevant} {benefit}"
    ordinal = re.search(rf"\b(?:primer|segundo|tercer|cuarto|[uú]ltimo)\s+(?:{DAY_PATTERN})(?:\s+y\s+(?:{DAY_PATTERN}))?\s+de\s+cada\s+mes", f"{relevant} {conditions}", re.I)
    if ordinal:
        return compact(ordinal.group(0))
    month_days = re.search(r"\b(?:del?\s+)?\d{1,2}\s+al\s+\d{1,2}\s+de\s+cada\s+mes", f"{relevant} {conditions}", re.I)
    if month_days:
        return compact(month_days.group(0))
    if re.search(r"todos\s+los\s+d[ií]as", relevant, re.I):
        return "Todos los días"
    day_range = re.search(rf"\b(?:de\s+)?({DAY_PATTERN})\s+a\s+({DAY_PATTERN})\b", relevant, re.I)
    if day_range:
        return compact(day_range.group(0))
    days = []
    for name in WEEKDAYS:
        plural = f"{name}s?" if name in {"sábado", "domingo"} else name
        if re.search(rf"\b{plural}\b", relevant, re.I):
            days.append(name)
    if days:
        return ", ".join(days)
    condition_lines = benefit_bullets(conditions)
    for line in condition_lines:
        if ("promoción" in line.casefold() or "beneficio" in line.casefold()) and ("aplica" in line.casefold() or "válida" in line.casefold()):
            if installments and "descuento" in line.casefold() and "cuotas" not in line.casefold():
                continue
            if not installments and "cuotas" in line.casefold() and "descuento" not in line.casefold():
                continue
            if re.search(r"todos\s+los\s+d[ií]as", line, re.I):
                return "Todos los días"
            found = [day for day in WEEKDAYS if day in line.casefold()]
            if found:
                return ", ".join(found)
    if installments and "todos los días" in benefit.casefold():
        return "Todos los días"
    return "No especificado"


def card_label(bullet):
    lower = bullet.casefold()
    premium = any(token in lower for token in ("black", "infinite", "metalcard", "platinum"))
    basic = any(token in lower for token in ("clásica", "clásicas", "oro", "classic"))
    if premium and not basic:
        if "metalcard" in lower and "black" not in lower:
            return "premium", "Metalcard Premier"
        if "black premier" in lower and "metalcard" not in lower and "black, " not in lower:
            return "premium", "Black Premier"
        if "mastercard black" in lower and "premier" not in lower:
            return "premium", "Black"
        return "premium", "Black / Premier"
    return "base", "Tarjetas elegibles"


def selected_conditions(conditions):
    selected = []
    for line in benefit_bullets(conditions):
        if re.search(r"\b(tope|m[ií]nimo|no aplica|no participan|excluid|solo|[uú]nic|qr|delivery|compras v[ií]a web)\b", line, re.I):
            selected.append(line)
    return selected[:6]


def verified_cards(bullet, card_id):
    if card_id == 297:
        return "Tarjetas de crédito Mastercard Clásica, Oro, Black, Black Premier y Metalcard Premier GNB"
    match = re.search(r"tarjetas?\s+de\s+cr[eé]dito\b.*?(?:del\s+Banco\s+GNB\s+Paraguay|GNB\s+Paraguay|[.;]|$)", bullet, re.I)
    if match:
        return compact(match.group(0)).strip(" .;, ")
    if re.search(r"tarjetas?\s+de\s+cr[eé]dito", bullet, re.I):
        return "Tarjetas de crédito GNB"
    return ""


def build_rows():
    cards = json.loads(CARDS.read_text(encoding="utf-8"))["cards"]
    with REVIEW.open(encoding="utf-8-sig", newline="") as handle:
        review = {int(row["ID GNB"]): row for row in csv.DictReader(handle)}
    result = []
    issues = []
    for card in cards:
        card_id = card["id"]
        if card_id in EXISTING or card_id in EXCLUDE:
            continue
        source = review[card_id]
        summary = compact(card.get("miniDescription"))
        conditions = compact(source["Condiciones PDF"])
        benefits = compact(source["Beneficio PDF"])
        validity = compact(source["Vigencia PDF"]) or f"Hasta {card['endDate']}"
        if card_id == 52:
            benefits = "• 20% de descuento los miércoles con tarjetas de crédito GNB. • Hasta 12 cuotas sin intereses todos los días con tarjetas de crédito GNB."
            conditions = "No aplica para pagos con QR ni delivery. Tope de compra mensual: Gs. 1.000.000; tope de reintegro: Gs. 100.000."
            validity = "Desde 2026-07-01 hasta 2026-12-30"
        if card_id == 9:
            validity = "Desde 2026-10-14 hasta 2026-10-14"
        if card_id == 274:
            conditions += " La promoción aplica de lunes a sábados."
        if card_id == 377:
            validity = "Hasta 28 de noviembre de 2026. La ficha y el PDF difieren; se usa la fecha más temprana."
        if card_id == 662:
            conditions += " Aplica todos los días de la vigencia solamente a nombres o apellidos florales elegibles, con cédula física."

        bullets = benefit_bullets(benefits)
        offers = []
        for index, bullet in enumerate(bullets):
            quota = re.search(r"\b(?:hasta\s+)?(\d{1,2})\s+cuotas?\s+sin\s+intereses\b", bullet, re.I)
            rate = re.search(r"\b(?:hasta\s+)?(\d{1,3})\s*%\s*(?:de\s+)?(?:descuento|reintegro|off)\b", bullet, re.I)
            if quota:
                kind, label = card_label(bullet)
                offers.append((f"Hasta {quota.group(1)} cuotas sin intereses", bullet, True, kind, label, index))
            elif rate:
                pct = int(rate.group(1))
                if pct > 100:
                    continue
                word = "reintegro" if "reintegro" in rate.group(0).casefold() else "descuento"
                qr_bonus = re.search(r"\+\s*5\s*%.*?\bQR\b", bullet, re.I)
                other_rates = [int(value) for value in re.findall(r"\b(\d{1,3})\s*%", bullet) if int(value) not in {pct, 5}]
                if qr_bonus and other_rates and max(other_rates) < pct:
                    kind, label = card_label(bullet)
                    offers.append((f"{pct}% de {word} con QR", bullet, False, kind, label, index * 10))
                    physical = max(other_rates)
                    offers.append((f"{physical}% de {word} con tarjeta física", bullet, False, kind, label, index * 10 + 1))
                    continue
                qualifier = " con QR" if "qr" in bullet.casefold() and "tarjeta física" not in bullet.casefold() else ""
                kind, label = card_label(bullet)
                offers.append((f"{pct}% de {word}{qualifier}", bullet, False, kind, label, index))
        if not offers:
            if has_installments(summary):
                quota = re.search(r"(\d{1,2})\s+cuotas", summary, re.I)
                offers.append((f"Hasta {quota.group(1)} cuotas sin intereses", summary, True, "base", "Cuotas", 0))
            else:
                rate = re.search(r"\b(\d{1,3})\s*%", summary)
                if rate:
                    word = "reintegro" if "reintegro" in summary.casefold() else "descuento"
                    offers.append((f"{rate.group(1)}% de {word}", summary, False, "base", "Tarjetas elegibles", 0))
        if card_id == 266:
            offers = [
                ("50% reintegro en 1 embalaje al mes", bullets[0], False, "premium", "Black", 0),
                ("50% reintegro en 2 embalajes al mes", bullets[1], False, "premium", "Black Premier", 1),
                ("2 embalajes sin costo al mes", bullets[2], False, "premium", "Metalcard Premier", 2),
            ]
        if card_id == 297:
            offers = [
                ("32% descuento en caja + 10% reintegro", "Medicamentos nacionales: 32% de descuento en caja más 10% de reintegro con Mastercard GNB.", False, "base", "Medicamentos nacionales", 0),
                ("17% descuento en caja + 10% reintegro", "Medicamentos importados: 17% de descuento en caja más 10% de reintegro con Mastercard GNB.", False, "base", "Medicamentos importados", 1),
                ("Hasta 12 cuotas sin intereses", bullets[-1], True, "base", "Cuotas", 2),
            ]
        if card_id == 662:
            offers = [("Hasta 60% descuento con nombre floral elegible", bullets[0], False, "base", "Born To Bloom", 0)]
        if not offers:
            issues.append({"id": card_id, "name": card["title"], "reason": "no_quantified_offer"})
            continue

        for variant_number, (benefit, bullet, installments, kind, label, index) in enumerate(offers):
            day = day_text(summary, conditions, bullet, installments)
            if card_id == 662:
                day = "Todos los días"
            if card_id == 638 and not installments:
                day = "del 17 al 20 de cada mes; últimos 3 días de cada mes"
            if day == "No especificado":
                issues.append({"id": card_id, "name": card["title"], "reason": f"day_unknown_{index}"})
            caps = "; ".join(line for line in selected_conditions(conditions) if re.search(r"\b(tope|m[ií]nimo)\b", line, re.I))
            extra = selected_conditions(conditions)
            detail = ". ".join(part.rstrip(" .;,") for part in [bullet, *extra[:4]] if part.strip())
            if card_id == 377:
                detail += ". La ficha oficial termina el 28 de noviembre de 2026; el PDF indica el 28 de diciembre de 2026. Se usa la fecha más temprana hasta que GNB aclare la diferencia."
            branch = re.search(r"\bSucursal de (Asunci[oó]n|Ciudad del Este)\b", bullet, re.I)
            row = {
                "Comercio": compact(card["title"]),
                "Categoria": category(card["title"], summary),
                "Beneficio": benefit,
                "Dia": day,
                "Vigencia": validity,
                "Locales": f"{card['title']} - {branch.group(1)}" if branch else compact(card["title"]),
                "Montos": caps,
                "URL detalle": f"{BASE_URL}{card_id}",
                "Tarjetas verificadas": verified_cards(bullet, card_id),
                "Detalle": detail,
                "Variante": f"gnb-{card_id}-{variant_number}",
                "Tipo de variante": kind,
                "Etiqueta de variante": label,
                "Fin del período fuente": card["endDate"],
                "Últimos días del mes": 3 if card_id == 638 and not installments else "",
                "Advertencia de fuente": "",
            }
            result.append(row)
    return result, issues


def main():
    rows, issues = build_rows()
    print(f"GNB live: {len(rows)} candidate offers from {len({row['URL detalle'] for row in rows})} cards; {len(issues)} issues")
    print(json.dumps(issues[:40], ensure_ascii=False))


if __name__ == "__main__":
    main()
