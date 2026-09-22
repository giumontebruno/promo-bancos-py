"""Turn GNB's visible benefit cards into an auditable review catalog.

The input is a browser snapshot of the site's card data, not its PDF terms.
Nothing in this file is published as a verified app promotion automatically.
"""

import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/gnb_live_cards_2026-09-22.json"
OUTPUT = ROOT / "outputs/gnb_catalogo_oficial_2026-09-22.csv"
REPORT = ROOT / "outputs/gnb_catalogo_revision_2026-09-22.json"
BASE_URL = "https://www.beneficiosbancognb.com.py/v2/beneficios/categorias/"


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def existing_page_ids():
    path = ROOT / "outputs/gnb_beneficios_por_categoria.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        urls = [row.get("URL detalle", "") for row in csv.DictReader(handle)]
    ids = set()
    for url in urls:
        match = re.search(r"/categorias/(\d+)(?:/|$)", urlparse(url).path)
        if match:
            ids.add(int(match.group(1)))
    # Reviewed PDF rows represent these source cards and sometimes expand
    # one campaign into separate merchants or card/payment variants.
    ids.update({148, 408, 598, 313, 73})
    return ids


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    cards = source["cards"]
    seen = set()
    present = existing_page_ids()
    rows = []
    today = date.fromisoformat(source["checkedAt"][:10])

    for card in cards:
        card_id = card["id"]
        if card_id in seen:
            raise ValueError(f"Duplicate source card {card_id}")
        seen.add(card_id)
        lines = [clean(line) for line in card.get("lines", []) if clean(line)]
        summary = clean(card.get("miniDescription"))
        detail = " | ".join(lines)
        flags = []
        if date.fromisoformat(card["endDate"]) < today:
            flags.append("expired")
        if re.search(r"\bcon intereses\b", f"{summary} {detail}", re.I):
            flags.append("interest_bearing")
        if card_id == 157:
            flags.append("cash_advance_fee")
        if not re.search(r"\d+\s*%|cuotas?\s+sin\s+intereses|sin costo", f"{summary} {detail}", re.I):
            flags.append("benefit_not_quantified")
        if card["startDate"] < "2026-01-01" and len(lines) > 1 and re.search(r"\b2026\b", lines[1]):
            flags.append("source_start_date_stale")
        if card["title"] in {"La Ruta Gastronómica", "Bares & Restó", "Electrónica y electrodomésticos", "Viajes", "Centros de Enseñanzas"}:
            flags.append("merchant_group_not_geocodable")
        rows.append({
            "ID GNB": card_id,
            "Comercio": clean(card["title"]),
            "Categoría GNB": clean(card["category"]),
            "Resumen publicado": summary,
            "Vigencia inicial API": card["startDate"],
            "Vigencia final API": card["endDate"],
            "Texto visible de la ficha": detail,
            "URL de la promoción": f"{BASE_URL}{card_id}",
            "Ya representada en la app": "sí" if card_id in present else "no",
            "Revisión": "; ".join(flags),
        })

    if len(rows) != source["total"]:
        raise ValueError(f"Source count mismatch: {len(rows)} != {source['total']}")
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "checked_at": source["checkedAt"],
        "source": "GNB card catalog displayed in Chrome; representation checked against reviewed app data",
        "total_source_cards": len(rows),
        "already_represented_source_cards": sum(row["Ya representada en la app"] == "sí" for row in rows),
        "source_cards_not_yet_in_app": [row["ID GNB"] for row in rows if row["Ya representada en la app"] == "no"],
        "flagged_cards": [
            {"id": row["ID GNB"], "name": row["Comercio"], "flags": row["Revisión"]}
            for row in rows if row["Revisión"]
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GNB: {len(rows)} source cards; {len(report['source_cards_not_yet_in_app'])} not yet represented in the app.")


if __name__ == "__main__":
    main()
