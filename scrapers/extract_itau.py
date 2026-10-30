import csv
import html
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

try:
    from scrapers.itau_reviewed_scopes import reviewed_scopes
except ModuleNotFoundError:
    from itau_reviewed_scopes import reviewed_scopes


BASE = "https://www.itau.com.py"
START = f"{BASE}/beneficios"
OUT_CSV = Path("outputs/itau_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/itau_beneficios_por_categoria.md")
WORK_DIR = Path("work/itau")


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def extract_day(text):
    text = clean(text)
    day = r"(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|sábado|sabado|domingos|domingo)"
    patterns = [
        rf"aplica (?:los |el )?{day}(?:\s*(?:,\s*(?:y\s+)?|\by\s+|\ba\s+){day})*",
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


def discover_categories(soup):
    categories = []
    seen_categories = set()
    for a in soup.select('a[href^="/beneficios2/categoria/"]'):
        href = a.get("href")
        m = re.search(r"/categoria/(\d+)", href)
        category = clean(a.get("onclick") or a.get_text(" "))
        m_name = re.search(r"\('(.+?)'\)", category)
        category = clean(m_name.group(1) if m_name else a.get_text(" "))
        if m and m.group(1) not in seen_categories:
            seen_categories.add(m.group(1))
            categories.append({"id": m.group(1), "name": category, "url": urljoin(BASE, href)})

    if not categories:
        raise ValueError("Itaú: no official categories found; preserving previous export")
    return categories


def fetch(session, url, timeout=30):
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def cached_fetch(session, url, timeout=30):
    if url == START:
        path = WORK_DIR / 'beneficios.html'
    elif '/categoria/' in url:
        path = WORK_DIR / ('categoria_' + url.rsplit('/', 1)[1] + '.html')
    else:
        query = parse_qs(urlparse(url).query)
        path = WORK_DIR / f"detail_{query['b'][0]}_{query['c'][0]}.html"
    return path.read_text(encoding='utf-8')


def main(use_cache=False):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    get = cached_fetch if use_cache else fetch
    start_html = get(session, START)
    (WORK_DIR / "beneficios.html").write_text(start_html, encoding="utf-8")
    soup = BeautifulSoup(start_html, "html.parser")

    categories = discover_categories(soup)

    rows = []
    seen_details = set()
    for cat in categories:
        page = get(session, cat["url"])
        (WORK_DIR / f"categoria_{cat['id']}.html").write_text(page, encoding="utf-8")
        cat_soup = BeautifulSoup(page, "html.parser")
        category_cards = cat_soup.select("a.item-oferta")
        if not category_cards:
            raise ValueError(f"Itaú: empty or inaccessible category {cat['url']}; preserving previous export")
        for card in category_cards:
            onclick = card.get("onclick", "")
            m = re.search(r"buscar\('([^']+)','([^']+)','([^']*)'\)", onclick)
            if not m:
                raise ValueError(f"Itaú: unrecognized benefit card in {cat['url']}; preserving previous export")
            b, c, onclick_name = m.groups()
            key = (b, c)
            if key in seen_details:
                continue
            seen_details.add(key)
            name, card_discount = card_summary(card)
            detail_url = f"{BASE}/beneficios2/Detalle?b={b}&c={c}"
            detail = get(session, detail_url, timeout=30)
            (WORK_DIR / f"detail_{b}_{c}.html").write_text(detail, encoding="utf-8")
            detail_soup = BeautifulSoup(detail, "html.parser")
            title = clean((detail_soup.find("h2") or {}).get_text(" ") if detail_soup.find("h2") else name or onclick_name)
            detail_category = clean((detail_soup.select_one(".col-md-3 span") or {}).get_text(" ") if detail_soup.select_one(".col-md-3 span") else cat["name"])
            badges = clean(" ".join(s.get_text(" ", strip=True) for s in detail_soup.select("small.badge-success")))
            paragraph = clean(" ".join(p.get_text(" ", strip=True) for p in detail_soup.select("p")))
            benefit = text_after_label(detail_soup, "beneficio")
            vigencia = text_after_label(detail_soup, "vigencia")
            payment = text_after_label(detail_soup, "medios de pago")
            bases = text_after_label(detail_soup, "bases y condiciones")
            if not detail_soup.find("h2") or not (benefit or payment or bases):
                raise ValueError(f"Itaú: incomplete benefit detail {detail_url}; preserving previous export")
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

    if not rows:
        raise ValueError("Itaú: empty catalog; preserving previous export")
    rows = [variant for row in rows for variant in reviewed_scopes(row)]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
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
