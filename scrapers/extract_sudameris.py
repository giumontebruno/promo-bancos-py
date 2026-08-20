import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE = "https://www.sudameris.com.py"
START = f"{BASE}/beneficios"
OUT_DIR = Path("outputs")
WORK_DIR = Path("work")


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def section_after(text, heading):
    pattern = rf"{heading}\s*(.*?)(?:VIGENCIA|BENEFICIOS?|Categorias|Contactos|Bases y Condiciones|Promociones relacionadas|Buscador de comercios|$)"
    match = re.search(pattern, text, flags=re.I | re.S)
    return clean(match.group(1)) if match else ""


def extract_dates(vigencia):
    desde = hasta = ""
    m = re.search(r"Desde el\s+(.+?)\s+hasta el\s+(.+?)(?:\.|$)", vigencia, re.I)
    if m:
        desde, hasta = clean(m.group(1)), clean(m.group(2))
    else:
        m = re.search(r"Hasta el\s+(.+?)(?:\.|$)", vigencia, re.I)
        if m:
            hasta = clean(m.group(1))
    return desde, hasta


def extract_percent(text):
    return "; ".join(sorted(set(re.findall(r"\d{1,3}\s*%", text))))


def extract_cuotas(text):
    values = re.findall(r"(?:hasta\s+)?\d+\s+cuotas?\s+sin\s+inter[eé]s(?:es)?", text, re.I)
    return "; ".join(dict.fromkeys(clean(v) for v in values))


def extract_tope(text):
    hits = re.findall(r"(?:tope[^.:\n]*[: ]\s*)?Gs\.?\s*[\d\.]+", text, re.I)
    return "; ".join(dict.fromkeys(clean(v) for v in hits if "Gs" in v))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    WORK_DIR.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    html = session.get(START, timeout=30).text
    (WORK_DIR / "sudameris_beneficios.html").write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    links = []
    seen = set()
    for a in soup.select('a.link[href*="/beneficios/"][href$="/detalle"]'):
        url = urljoin(BASE, a.get("href"))
        if url not in seen:
            seen.add(url)
            links.append({"title": clean(a.get_text(" ")), "url": url})

    rows = []
    for item in links:
        resp = session.get(item["url"], timeout=30)
        resp.raise_for_status()
        detail_soup = BeautifulSoup(resp.text, "html.parser")
        description = detail_soup.select_one(".description-promo")
        raw_text = description.get_text("\n") if description else detail_soup.get_text("\n")
        text = clean(raw_text)
        title = clean((detail_soup.find(["h1", "h2", "h3", "h4"]) or {}).get_text(" ") if detail_soup.find(["h1", "h2", "h3", "h4"]) else item["title"])
        vigencia = section_after(raw_text, "VIGENCIA")
        beneficios = section_after(raw_text, "BENEFICIOS?")
        desde, hasta = extract_dates(vigencia)
        combined = f"{vigencia} {beneficios}"
        bases = [
            urljoin(BASE, a.get("href"))
            for a in detail_soup.select('a[href$=".pdf"], a[href*=".pdf?"]')
            if "Bases" in clean(a.get_text(" "))
        ]

        rows.append(
            {
                "Banco": "Sudameris",
                "Comercio/Promocion": title or item["title"],
                "Resumen cuadro": item["title"],
                "Vigencia": vigencia,
                "Desde": desde,
                "Hasta": hasta,
                "Beneficios": beneficios,
                "% detectado": extract_percent(combined),
                "Tope detectado": extract_tope(combined),
                "Cuotas detectadas": extract_cuotas(combined),
                "Bases y condiciones URL": "; ".join(dict.fromkeys(bases)),
                "URL": item["url"],
                "Texto completo": text,
            }
        )
        time.sleep(0.15)

    csv_path = OUT_DIR / "sudameris_promociones.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUT_DIR / "sudameris_promociones_resumen.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Sudameris promociones\n\nExtraidas desde {START}\n\nTotal: {len(rows)}\n\n")
        f.write("| Banco | Comercio/Promocion | Vigencia | Beneficios | URL |\n")
        f.write("|---|---|---|---|---|\n")
        for row in rows:
            f.write(
                "| "
                + " | ".join(
                    [
                        row["Banco"],
                        row["Comercio/Promocion"].replace("|", "/"),
                        row["Vigencia"].replace("|", "/")[:180],
                        row["Beneficios"].replace("|", "/")[:220],
                        row["URL"],
                    ]
                )
                + " |\n"
            )

    print(f"{len(rows)} promociones -> {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
