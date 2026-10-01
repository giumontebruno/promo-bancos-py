"""Extract GNB's official benefit API through a real browser.

GNB's Akamai policy rejects ordinary HTTP clients, while the public site loads
the same JSON without authentication. Playwright is therefore used only as the
transport; the stored data remains the bank's official API response.
"""

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.beneficiosbancognb.com.py/v2/beneficios/categorias"
API_PATH = "/v2/apis/rewards/rewards/v1/benefits/benefits?pageSize=500"
CARDS = ROOT / "data/gnb_live_cards.json"
REVIEW = ROOT / "outputs/gnb_live_card_review.csv"
REPORT = ROOT / "outputs/gnb_extraction_review.json"


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def text_lines(markup):
    soup = BeautifulSoup(markup or "", "html.parser")
    lines = []
    for node in soup.select("p, li"):
        value = clean(node.get_text(" ", strip=True))
        if value and value not in lines:
            lines.append(value)
    return lines


def media_path(value):
    match = re.search(r'(imagenes/[^";}]+)', str(value or ""), re.I)
    if not match:
        return ""
    return "/".join(quote(part, safe="%()'_,.-") for part in match.group(1).split("/"))


def quantified(lines):
    candidates = lines[2:] if len(lines) > 2 else lines
    return [
        line for line in candidates
        if re.search(r"\b\d{1,3}\s*%|\b\d{1,2}\s+cuotas?\s+sin\s+inter[eé]s|\bsin costo\b", line, re.I)
    ]


def fetch_catalog():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(SOURCE, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(1_200)
            return page.evaluate(
                """async path => {
                  const response = await fetch(path, {headers: {Accept: 'application/json'}});
                  if (!response.ok) throw new Error(`GNB API ${response.status}`);
                  return response.json();
                }""",
                API_PATH,
            )
        finally:
            browser.close()


def main():
    payload = fetch_catalog()
    cards = []
    reviews = []
    checked_at = datetime.now(timezone.utc).isoformat()
    for item in payload.get("data", []):
        lines = text_lines(item.get("description"))
        card_id = int(item["id"])
        terms_path = media_path((item.get("termsAndConditionsImage") or {}).get("imageLink"))
        image_path = media_path((item.get("image") or {}).get("imageLink"))
        terms_url = f"https://www.beneficiosbancognb.com.py/{terms_path}" if terms_path else ""
        detail_url = f"{SOURCE}/{card_id}"
        card = {
            "id": card_id,
            "title": clean(item.get("title")),
            "startDate": item.get("startDate") or "",
            "endDate": item.get("endDate") or "",
            "miniDescription": max(
                (clean(item.get("miniDescription")), lines[0] if lines else ""),
                key=len,
            ),
            "category": clean((item.get("category") or {}).get("name")),
            "lines": lines,
            "termsUrl": terms_url,
            "imageUrl": f"https://www.beneficiosbancognb.com.py/{image_path}" if image_path else "",
        }
        cards.append(card)
        benefit_lines = quantified(lines)
        conditions = [line for line in lines if line not in benefit_lines]
        validity = next((line for line in lines if re.search(r"\b(?:del|desde|hasta)\b.*\b20\d{2}\b", line, re.I)), "")
        reviews.append({
            "ID GNB": card_id,
            "Comercio": card["title"],
            "Categoría web": card["category"],
            "Resumen web": card["miniDescription"],
            "Vigencia web final": card["endDate"],
            "Vigencia PDF": validity,
            "Vigencia PDF final": card["endDate"],
            "Beneficio PDF": " • ".join(benefit_lines),
            "Condiciones PDF": " • ".join(conditions),
            "PDF páginas": "",
            "PDF SHA256": "",
            "URL promoción": detail_url,
            "URL bases": terms_url or detail_url,
            "Alertas": "terms_link_missing" if not terms_url else "",
        })

    total = int((payload.get("pagination") or {}).get("totalElements", len(cards)))
    if len(cards) != total or len(cards) < 100:
        raise ValueError(f"Incomplete GNB catalog: {len(cards)} of {total}")
    if len({card["id"] for card in cards}) != len(cards):
        raise ValueError("Duplicate GNB card IDs")

    CARDS.write_text(
        json.dumps({"checkedAt": checked_at, "total": total, "cards": cards}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(reviews[0]))
        writer.writeheader()
        writer.writerows(reviews)
    REPORT.write_text(json.dumps({
        "checked_at": checked_at,
        "source": SOURCE,
        "api": API_PATH,
        "status": "fetched_in_browser",
        "cards": len(cards),
        "terms_links": sum(bool(card["termsUrl"]) for card in cards),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GNB: {len(cards)} official cards extracted; {sum(bool(card['termsUrl']) for card in cards)} terms links.")


if __name__ == "__main__":
    main()
