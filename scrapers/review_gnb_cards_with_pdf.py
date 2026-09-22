"""Cross-check each live GNB card against its linked official terms."""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from promo_backend.quality import validity_dates


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data/gnb_live_cards_2026-09-22.json"
MANIFEST = ROOT / "data/gnb_pdf_manifest_2026-09-22.json"
PDF_TEXT = ROOT / "data/gnb_pdf_text_2026-09-22.json"
OUTPUT = ROOT / "outputs/gnb_card_pdf_review_2026-09-22.csv"
SUMMARY = ROOT / "outputs/gnb_card_pdf_review_2026-09-22.json"


def compact(value):
    return re.sub(r"\s+", " ", value or "").strip()


def section(text, start_number, name, end_number, end_name):
    pattern = rf"\b{start_number}\s*\.\s*{name}\b\s*(.*?)\s*\b{end_number}\s*\.\s*{end_name}\b"
    match = re.search(pattern, text, re.I)
    return match.group(1).strip() if match else ""


def main():
    cards = json.loads(CARDS.read_text(encoding="utf-8"))["cards"]
    manifest = {card["id"]: card["pdf"] for card in json.loads(MANIFEST.read_text(encoding="utf-8"))}
    documents = json.loads(PDF_TEXT.read_text(encoding="utf-8"))["documents"]
    rows = []
    for card in cards:
        path = manifest[card["id"]]
        file_id = re.search(r"imagenes/(\d+)_", path).group(1)
        document = documents[file_id]
        body = compact(document.get("text", ""))
        validity = section(body, 1, "Vigencia", 2, "Condiciones")
        conditions = section(body, 2, "Condiciones", 3, "Beneficios?")
        benefit = section(body, 3, "Beneficio", 4, "Mec[aá]nica")
        if not benefit:
            benefit = section(body, 3, "Beneficios", 4, "Mec[aá]nica")
        card_text = compact(" ".join(card.get("lines", [])))
        rate_card = sorted({int(x) for x in re.findall(r"\b(\d{1,3})\s*%", card_text) if int(x) <= 100})
        rate_pdf = sorted({int(x) for x in re.findall(r"\b(\d{1,3})\s*%", benefit) if int(x) <= 100})
        pdf_end = validity_dates(validity)["ends_on"]
        flags = []
        if document.get("error"):
            flags.append("pdf_unreadable")
        if not validity or not conditions or not benefit:
            flags.append("nonstandard_sections")
        if rate_pdf and not set(rate_pdf).issubset(set(rate_card)):
            flags.append("pdf_rate_not_in_card_text")
        if pdf_end and pdf_end != card["endDate"]:
            flags.append("pdf_card_end_date_mismatch")
        if re.search(r"\bcon intereses\b", benefit, re.I):
            flags.append("interest_bearing")
        if re.search(r"\bcomisi[oó]n\b", benefit + " " + conditions, re.I) and card["id"] == 157:
            flags.append("cash_advance_fee")
        rows.append({
            "ID GNB": card["id"],
            "Comercio": compact(card["title"]),
            "Categoría web": card["category"],
            "Resumen web": compact(card["miniDescription"]),
            "Vigencia web final": card["endDate"],
            "Vigencia PDF": validity,
            "Vigencia PDF final": pdf_end or "",
            "Beneficio PDF": benefit,
            "Condiciones PDF": conditions,
            "PDF páginas": document.get("pages", 0),
            "PDF SHA256": document.get("sha256", ""),
            "URL promoción": f"https://www.beneficiosbancognb.com.py/v2/beneficios/categorias/{card['id']}",
            "URL bases": document["url"],
            "Alertas": "; ".join(flags),
        })
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "cards": len(rows),
        "pdfs": len(documents),
        "alerts": dict(Counter(flag for row in rows for flag in row["Alertas"].split("; ") if flag)),
        "nonstandard_ids": [row["ID GNB"] for row in rows if "nonstandard_sections" in row["Alertas"]],
        "rate_mismatch_ids": [row["ID GNB"] for row in rows if "pdf_rate_not_in_card_text" in row["Alertas"]],
        "date_mismatch_ids": [row["ID GNB"] for row in rows if "pdf_card_end_date_mismatch" in row["Alertas"]],
    }
    SUMMARY.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
