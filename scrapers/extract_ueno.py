import csv
import re
from pathlib import Path

import pdfplumber
import requests


PDF_URL = "https://www.ueno.com.py/wp-content/uploads/2026/08/BENEFICIOS-ueno-agosto2026.pdf"
PDF_PATH = Path("work/ueno_beneficios_agosto2026.pdf")
OUT_CSV = Path("outputs/ueno_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/ueno_beneficios_por_categoria.md")


CATEGORY_HINTS = [
    "Supermercados",
    "Combustible",
    "Estaciones de servicio",
    "Farmacias",
    "Gastronomía",
    "Entretenimiento",
    "Shopping",
    "Tiendas",
    "Hogar",
    "Viajes",
    "Educación",
    "Salud",
    "Promos especiales",
]

PAGE_LOCAL_OVERRIDES = {
    1: "Publicidad de ueno",
    2: "Feria Palmear; Combustible; Petropar; Hoteles; Supermercados; Kingo & Ahorrazo; Farmacias; Bienestar; Gastronomía; Entretenimiento; Puka; Muv; Cuotas sin intereses; Vernier; Koala; Óptica Luce; Joyerías; Isalú; Conto; Escuela Judicial; Clubes; Deportes; Débito automático",
    3: "Salemma; Plub; Superseis; Superseis Express; Stock; Stock Express; Delimarket; Real; Gran Vía; Metro; Pronto; Colón; Marías; Hello Oven; H&V Supermercados; Molino Caaguazú; Qpets; Porkus",
    4: "El Ahorrazo; Kingo",
    5: "Copetrol; Enex; Petrobras; 3MG Estaciones de Servicios; Puma Energy; Petrochaco; Petromax",
    6: "Petropar",
    7: "Hotel Acuario; Los Arboles; Oasis Dream; Casa Blanca; Planazo; Quinta La Paloma",
    8: "Flight Nex; Virtuality",
    9: "Farmacia Vicente Scavone; Farmacenter; Biggie Farma; Drugstore; Farmatotal",
    12: "Club Internacional de Tenis",
    13: "Club Cerro Porteño - Club Social y Deportivo; Club Olimpia",
    16: "Oscar Joyas; Neusa Joyas",
    18: "Óptica Luce",
    25: "Uela; Intertours; Alula; Pago Par; u market; Deportes; Cyclesport; Club Cerro Porteño; Puma; Outdoors; Sport House; CAT; Merrell; Kappa; RND; Iron Store",
    26: "Publicidad / cierre ueno",
}

PAGE_LIMIT_RESET_OVERRIDES = {
    5: "Topes por semana: Semana 1 del 01 al 09 de agosto; Semana 2 del 10 al 16 de agosto; Semana 3 del 17 al 23 de agosto; Semana 4 del 24 al 31 de agosto.",
}

PAGE_TOPES_OVERRIDES = {
    3: "Nivel 5: 40%, tope de compra Gs. 500.000; Nivel 4: 30%, tope de compra Gs. 400.000; Nivel 3: 25%, tope de compra Gs. 300.000; Nivel 2: 15%, tope de compra Gs. 300.000; Nivel 1: 10%, tope de compra Gs. 300.000. Compra mínima Gs. 300.000.",
    5: "Nivel 5: 40%, tope de compra total Gs. 600.000, tope de compra semanal Gs. 150.000; Nivel 4: 30%, total Gs. 500.000, semanal Gs. 125.000; Nivel 3: 25%, total Gs. 300.000, semanal Gs. 75.000; Nivel 2: 15%, total Gs. 200.000, semanal Gs. 50.000; Nivel 1: 10%, total Gs. 100.000, semanal Gs. 25.000.",
    9: "Nivel 5: 15%, tope de compra Gs. 1.000.000; Nivel 4: 15%, tope de compra Gs. 700.000; Nivel 3: 15%, tope de compra Gs. 400.000; Nivel 2: 15%, tope de compra Gs. 300.000; Nivel 1: 15%, tope de compra Gs. 200.000.",
}

PAGE_LEVEL_OVERRIDES = {
    1: "No aplica - publicidad de primera compra.",
    4: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    3: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    5: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    6: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    7: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    8: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    9: "Nivel 5: 15%; Nivel 4: 15%; Nivel 3: 15%; Nivel 2: 15%; Nivel 1: 15%.",
    10: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    11: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    12: "Nivel 1 al 5: 20%.",
    13: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    14: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    16: "Cuotas sin intereses - aplica a todos los niveles.",
    17: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    18: "Nivel 5: 30%; Nivel 4: 25%; Nivel 3: 25%; Nivel 2: 20%; Nivel 1: 20%.",
    20: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    21: "Nivel 1 al 5: 30%.",
    22: "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%.",
    23: "Nivel 1 al 5: 20%.",
    24: "Nivel 1 al 5: 10%.",
    15: "Sin reintegro por nivel - suma upys por pedidos.",
    19: "Nivel 1 al 5: 12%.",
    26: "No aplica - publicidad / cierre.",
}


def clean(text):
    text = (text or "").replace("\x00", " ")
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return re.sub(r"\s+", " ", text).strip()


def download():
    PDF_PATH.parent.mkdir(exist_ok=True)
    if not PDF_PATH.exists():
        response = requests.get(PDF_URL, timeout=30)
        response.raise_for_status()
        PDF_PATH.write_bytes(response.content)


def detect_category(text, page_no):
    upper = text.upper()
    for hint in CATEGORY_HINTS:
        if hint.upper() in upper:
            return hint
    if page_no == 1:
        return "Primera compra"
    return "Beneficios del mes"


def extract_percentages(text):
    return "; ".join(dict.fromkeys(re.findall(r"\d{1,3}\s*%", text))) or "Ver detalle"


def extract_day(text):
    patterns = [
        r"todos los días",
        r"todos los (lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos)",
        r"los (lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos)",
        r"\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
    ]
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.I):
            found.append(clean(m.group(0)))
    return "; ".join(dict.fromkeys(found)) or "No especificado"


def extract_vigencia(text):
    for pattern in [
        r"Del\s+\d{1,2}\s+al\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",
        r"Del\s+\d{1,2}\s+de\s+\w+\s+al\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",
        r"Desde\s+el\s+.*?\s+hasta\s+el\s+.*?(?:2026|2027)",
        r"Vigencia[: ]+.*?(?:2026|2027)",
        r"01\s+al\s+31\s+de\s+agosto\s+de\s+2026",
    ]:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return "Del 01 al 31 de agosto de 2026"


def extract_topes(text):
    hits = []
    for pattern in [
        r"tope[^.]{0,100}",
        r"Gs\.?\s*[\d\.]+",
        r"G\.\s*[\d\.]+",
    ]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(hits)) or "Ver bases y condiciones"


def extract_level_benefit(text, page_no):
    if page_no in PAGE_LEVEL_OVERRIDES:
        return PAGE_LEVEL_OVERRIDES[page_no]
    percentages = list(dict.fromkeys(re.findall(r"\d{1,3}\s*%", text)))
    if re.search(r"cuotas?\s+sin\s+inter[eé]s", text, flags=re.I) and not percentages:
        return "Cuotas sin intereses - aplica a todos los niveles."
    if re.search(r"1\s+al\s+5", text, flags=re.I) and percentages:
        return f"Nivel 1 al 5: {percentages[0]}."
    if "Nivel" in text and percentages:
        if all(p in percentages for p in ["40%", "30%", "25%", "15%"]):
            if "10%" in percentages:
                return "Nivel 5: 40%; Nivel 4: 30%; Nivel 3: 25%; Nivel 2: 15%; Nivel 1: 10%."
            return "Beneficio por nivel detectado; revisar tabla del PDF para asignación exacta por nivel: " + "; ".join(percentages)
        return "Beneficio por nivel detectado; revisar tabla del PDF para asignación exacta por nivel: " + "; ".join(percentages)
    return "No especificado"


def level_type(level_text):
    if level_text.startswith("No aplica"):
        return "No aplica"
    if level_text.startswith("Cuotas sin intereses"):
        return "Sin nivel - aplica a todos"
    if level_text.startswith("Sin reintegro"):
        return "Sin nivel - aplica a todos"
    if "Nivel 1 al 5" in level_text:
        return "Mismo beneficio nivel 1 al 5"
    if "Nivel 5:" in level_text:
        return "Escala por nivel"
    return "Revisar"


def extract_locales(text, page_no):
    if page_no in PAGE_LOCAL_OVERRIDES:
        return PAGE_LOCAL_OVERRIDES[page_no]
    # Text fallback for pages whose merchant names are not embedded as images.
    likely = []
    known_words = [
        "Monchis", "Vernier", "Koala", "Conto", "Muv", "Puka", "Isalú", "Feria Palmear",
        "Escuela Judicial", "Shopping Costanera", "AF Peak Lab",
    ]
    for word in known_words:
        if re.search(re.escape(word), text, flags=re.I):
            likely.append(word)
    return "; ".join(dict.fromkeys(likely)) or "Ver detalle / logos en PDF"


def guess_title(text, category, page_no):
    text = clean(text)
    if page_no == 1:
        return "Activá tu tarjeta - primera compra"
    # Use first short all-caps-ish phrase before benefit text as a page title.
    candidates = re.split(r"(?=Hasta|Del |Beneficio|Ver bases|Vto\.|Tope)", text, maxsplit=1)
    title = candidates[0].strip()
    title = re.sub(r"^[^A-Za-zÁÉÍÓÚÑáéíóúñ]+", "", title)
    if len(title) < 5 or len(title) > 120:
        return category
    return title


def main():
    download()
    rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = clean(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            if not text:
                continue
            category = detect_category(text, idx)
            rows.append(
                (lambda level_text: {
                    "Categoría": category,
                    "Banco": "ueno bank",
                    "Comercio/Promoción": guess_title(text, category, idx),
                    "Cantidad de descuento / beneficio": extract_percentages(text),
                    "Beneficio por niveles": "Sí" if level_type(level_text) in ["Escala por nivel", "Mismo beneficio nivel 1 al 5"] else "No",
                    "Tipo de beneficio por nivel": level_type(level_text),
                    "Descuentos por nivel": level_text,
                    "Día de promoción": extract_day(text),
                    "Vigencia": extract_vigencia(text),
                    "Locales / comercios detectados": extract_locales(text, idx),
                    "Montos / topes": PAGE_TOPES_OVERRIDES.get(idx, extract_topes(text)),
                    "Reinicio de límites": PAGE_LIMIT_RESET_OVERRIDES.get(idx, ""),
                    "Detalle": text,
                    "Bases / PDF URL": PDF_URL,
                    "Página PDF": idx,
                })(extract_level_benefit(text, idx))
            )

    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    grouped = {}
    for row in rows:
        grouped.setdefault(row["Categoría"], []).append(row)
    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# ueno bank - beneficios por categoria\n\n")
        f.write(f"Fuente: {PDF_URL}\n\nTotal de páginas/promociones extraídas: {len(rows)}\n\n")
        for category in sorted(grouped):
            f.write(f"## {category}\n\n")
            f.write("| Promoción | Locales / comercios | Descuento | Tipo nivel | Niveles | Día | Vigencia | Página |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for row in grouped[category]:
                vals = [
                    row["Comercio/Promoción"],
                    row["Locales / comercios detectados"],
                    row["Cantidad de descuento / beneficio"],
                    row["Tipo de beneficio por nivel"],
                    row["Descuentos por nivel"],
                    row["Día de promoción"],
                    row["Vigencia"],
                    str(row["Página PDF"]),
                ]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:180] for v in vals) + " |\n")
            f.write("\n")

    print(f"{len(rows)} filas -> {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
