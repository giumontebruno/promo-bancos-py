import csv
import html
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE = "https://www.itau.com.py"
START = f"{BASE}/beneficios"
OUT_CSV = Path("outputs/itau_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/itau_beneficios_por_categoria.md")
WORK_DIR = Path("work/itau")
MAIN_CATEGORY_IDS = {"7", "13", "39", "3", "14", "8", "9", "17", "42", "16", "51", "50"}


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def extract_day(text):
    text = clean(text)
    patterns = [
        r"aplica (?:los |el )?(lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|sábado|sabado|domingos|domingo)",
        r"todos los (lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos)",
        r"(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+a\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"todos los días",
        r"\b\d{1,2}\s+de cada mes\b",
        r"desde las\s+\d{1,2}:\d{2}\s*hs?\s*hasta las\s+\d{1,2}:\d{2}\s*hs?",
    ]
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.I):
            found.append(clean(m.group(0)))
    return "; ".join(dict.fromkeys(found)) or "No especificado"


def text_after_label(soup, label):
    for li in soup.select("li"):
        strong = li.find("strong")
        if strong and label.lower() in clean(strong.get_text()).lower():
            return clean(li.get_text(" ", strip=True).replace(clean(strong.get_text()), "", 1))
    return ""


def card_summary(card):
    name = clean((card.find("h6") or card).get_text(" "))
    discount = clean(" ".join(s.get_text(" ", strip=True) for s in card.select("small.badge")))
    return name, discount


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    start_html = session.get(START, timeout=30).text
    (WORK_DIR / "beneficios.html").write_text(start_html, encoding="utf-8")
    soup = BeautifulSoup(start_html, "html.parser")

    categories = []
    seen_categories = set()
    for a in soup.select('a[href^="/beneficios2/categoria/"]'):
        href = a.get("href")
        m = re.search(r"/categoria/(\d+)", href)
        category = clean(a.get("onclick") or a.get_text(" "))
        m_name = re.search(r"\('(.+?)'\)", category)
        category = clean(m_name.group(1) if m_name else a.get_text(" "))
        if m and m.group(1) not in seen_categories:
            if m.group(1) not in MAIN_CATEGORY_IDS:
                continue
            seen_categories.add(m.group(1))
            categories.append({"id": m.group(1), "name": category, "url": urljoin(BASE, href)})

    rows = []
    seen_details = set()
    for cat in categories:
        page = session.get(cat["url"], timeout=30).text
        (WORK_DIR / f"categoria_{cat['id']}.html").write_text(page, encoding="utf-8")
        cat_soup = BeautifulSoup(page, "html.parser")
        for card in cat_soup.select("a.item-oferta"):
            onclick = card.get("onclick", "")
            m = re.search(r"buscar\('([^']+)','([^']+)','([^']*)'\)", onclick)
            if not m:
                continue
            b, c, onclick_name = m.groups()
            key = (b, c)
            if key in seen_details:
                continue
            seen_details.add(key)
            name, card_discount = card_summary(card)
            detail_url = f"{BASE}/beneficios2/Detalle?b={b}&c={c}"
            detail = session.get(detail_url, timeout=10).text
            detail_soup = BeautifulSoup(detail, "html.parser")
            title = clean((detail_soup.find("h2") or {}).get_text(" ") if detail_soup.find("h2") else name or onclick_name)
            detail_category = clean((detail_soup.select_one(".col-md-3 span") or {}).get_text(" ") if detail_soup.select_one(".col-md-3 span") else cat["name"])
            badges = clean(" ".join(s.get_text(" ", strip=True) for s in detail_soup.select("small.badge-success")))
            paragraph = clean(" ".join(p.get_text(" ", strip=True) for p in detail_soup.select("p")))
            benefit = text_after_label(detail_soup, "beneficio")
            vigencia = text_after_label(detail_soup, "vigencia")
            payment = text_after_label(detail_soup, "medios de pago")
            bases = text_after_label(detail_soup, "bases y condiciones")
            full_text = clean(detail_soup.get_text(" ", strip=True))
            discount = clean("; ".join(v for v in [badges or card_discount, benefit] if v))

            rows.append(
                {
                    "Categoría": detail_category or cat["name"],
                    "Banco": "Itaú",
                    "Comercio/Promoción": title,
                    "Cantidad de descuento / beneficio": discount or paragraph,
                    "Día de promoción": extract_day(f"{paragraph} {bases}"),
                    "Vigencia": vigencia or paragraph,
                    "Medios de pago": payment,
                    "Detalle": paragraph,
                    "Bases y condiciones": bases,
                    "URL detalle": detail_url,
                    "URL categoría": cat["url"],
                }
            )
            time.sleep(0.02)

    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Itau - beneficios por categoria\n\n")
        f.write(f"Fuente: {START}\n\nTotal de beneficios: {len(rows)}\n\n")
        for category in sorted({r["Categoría"] for r in rows}):
            f.write(f"## {category}\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia |\n")
            f.write("|---|---|---|---|\n")
            for row in [r for r in rows if r["Categoría"] == category]:
                values = [
                    row["Comercio/Promoción"],
                    row["Cantidad de descuento / beneficio"],
                    row["Día de promoción"],
                    row["Vigencia"],
                ]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:220] for v in values) + " |\n")
            f.write("\n")

    print(f"{len(rows)} beneficios -> {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
