"""Scope Universitaria benefits to the payment method and product in their PDF."""

import csv
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/universitaria_beneficios_por_categoria.csv"
REPORT = ROOT / "outputs/universitaria_review_report.json"
SUMMARY = ROOT / "outputs/universitaria_beneficios_por_categoria.md"
SNAPSHOT = ROOT / "data/universitaria_source_snapshot_2026-09-22.json"
CARDS = "Tarjetas de crédito Panal, Cabal y Mastercard de Cooperativa Universitaria"

# These entries were checked against the linked PDF, not inferred from the
# promotional image or a table's flattened OCR text.
SIMPLE = {
    "BRISTOL": "Hasta 10 cuotas sin intereses",
    "Olier": "Hasta 10 cuotas sin intereses",
    "TUPI": "Hasta 10 cuotas sin intereses",
    "Nissei": "Hasta 10 cuotas sin intereses",
    "BELLMONT BARBERÍA": "20% de descuento en servicios",
    "Farmacumbre | Caacupé": "15% de descuento",
    "Las Hortensias": "10% de descuento en alojamiento",
    "Malian": "10% de descuento en alojamiento",
    "Universidad San Ignacio de Loyola": "10% de descuento en cuotas",
    "GRUPO SAJA - BAJAJ": "10% de descuento en modelos participantes",
    "Clinica ELGUE": "Hasta 40% de descuento en odontología",
    "MediCoop Laboratorio | Caacupé": "15% de descuento en análisis clínicos",
    "OAMI Medicina Pre-Paga": "10% de descuento en planes para nuevos ingresantes",
    "SANTA CLARA": "10% de descuento en planes nuevos con débito automático",
    "El Lector": "15% de descuento en programas participantes",
    "ÓPTICA B&E - CDE": "10% de descuento en armazones y cristales",
    "Óptica Luce": "30% de descuento en artículos ópticos",
}

# PDF-specific payment tables. A changed PDF filename requires a fresh review.
PAYMENT_TABLES = {
    "FARMACIA ENERGY": (30, 15, "descuento", 5000000),
    "Farmatotal": (30, 15, "descuento", 5000000),
    "Estaciones ENERGY": (20, 10, "reintegro", 500000),
    "BURGER KING": (30, 10, "reintegro", 500000),
    "POPEYES": (30, 10, "reintegro", 500000),
    "SUBWAY": (30, 10, "reintegro", 500000),
    "Archi - La Tienda Archi": (20, 10, "reintegro", 1000000),
    "Areté Supermercados": (25, 20, "reintegro", 1000000),
    "S6 | STOCK | DELI MARKET": (25, 20, "reintegro", 1000000),
    "SUPERMERCADO GÉMINIS": (20, 10, "reintegro", 1000000),
    "Casa Paraná": (20, 15, "reintegro", 1000000),
    "EL AHORRAZO": (20, 15, "reintegro", 1000000),
    "Hipermercado Luisito": (20, 10, "reintegro", 1000000),
    "REAL": (20, 10, "reintegro", 1000000),
    "Supermercado Metro": (20, 10, "reintegro", 1000000),
}

SPECIAL = {
    "CIAE & ASOC.": [
        (25, "descuento", "programa Detective Financiero Kid IV"),
        (15, "descuento", "otros cursos participantes; la tasa varía entre 10% y 15%"),
    ],
    "Universidad Autónoma de Asunción (UAA)": [
        (20, "descuento", "pago anticipado de un año académico o programas de posgrado"),
        (10, "descuento", "pago anticipado de un semestre"),
    ],
    "Universidad Centro Médico Bautista": [
        (10, "descuento", "cuotas mensuales de grado, excepto Medicina"),
        (15, "descuento", "semestre de grado, cuotas de posgrado o cursos internacionales"),
        (20, "descuento", "dos semestres de grado o programa completo de posgrado"),
    ],
    "Universidad UCOM": [
        (10, "descuento", "diplomados y carreras de grado"),
        (5, "descuento", "programas de posgrado"),
    ],
    "Farmacenter": [
        (40, "descuento", "QR en productos seleccionados y suplementos deportivos"),
        (30, "descuento", "QR"),
        (25, "descuento", "tarjeta física"),
    ],
    "Farmacia Catedral": [
        (50, "descuento", "QR en productos seleccionados"),
        (35, "descuento", "QR en medicamentos seleccionados"),
        (30, "descuento", "QR en medicamentos y productos varios"),
        (25, "descuento", "tarjeta física en medicamentos y productos varios"),
    ],
    "Farmaoliva": [
        (40, "descuento", "QR en productos seleccionados"),
        (30, "descuento", "QR en medicamentos nacionales"),
        (25, "descuento", "QR en medicamentos importados"),
        (25, "descuento", "tarjeta física en medicamentos y productos varios"),
    ],
    "Punto Farma": [
        (45, "descuento", "QR en productos no farmacéuticos seleccionados"),
        (35, "descuento", "QR en medicamentos nacionales"),
        (30, "descuento", "QR en medicamentos importados"),
        (30, "descuento", "tarjeta física en productos de farmacia y otros"),
    ],
    "MEYERLAB": [
        (15, "descuento", "análisis clínicos"),
        (5, "descuento", "diferencias no cubiertas por seguro médico privado"),
    ],
    "JOSE A. CARRON": [
        (30, "descuento", "lentes oftalmológicos y anteojos de sol"),
        (15, "descuento", "lentes de contacto protésicos y anuales"),
        (5, "descuento", "lentes de contacto descartables"),
    ],
    "ÓPTICA VISIÓN": [
        (20, "descuento", "anteojos ópticos"),
        (15, "descuento", "lentes de contacto"),
        (15, "descuento", "monturas solares"),
    ],
    "ÓPTICA jNESSI": [
        (15, "descuento", "armazones y lentes de sol"),
        (5, "descuento", "cristales"),
    ],
    "ÓPTICA CARRON": [
        (20, "descuento", "armazones con cristales o armazones de sol"),
        (15, "descuento", "cristales solamente"),
    ],
    "Universidad Columbia": [
        (10, "descuento", "cuotas de Derecho pagadas antes del vencimiento"),
        (15, "descuento", "cuotas de otras carreras habilitadas pagadas antes del vencimiento"),
    ],
}

REVIEWED_PDF = {
    "Farmacenter": "bases-y-condiciones1783348467.pdf",
    "Farmacia Catedral": "bases-y-condiciones1784292469.pdf",
    "Farmaoliva": "bases-y-condiciones1783347827.pdf",
    "Punto Farma": "bases-y-condiciones1783699874.pdf",
    "UNIVERSIDAD CATÓLICA": "bases-y-condiciones1784911866.pdf",
}

UNQUANTIFIED = {
    "La Ponde S.A.": "Precio preferencial de lotes sin precio de referencia ni tasa de descuento",
    "AFS": "Financiación sujeta a intereses vigentes; no indica descuento verificable",
}


def money(amount):
    return f"Gs. {amount:,}".replace(",", ".")


def variant(row, benefit, index, *, day=None, scope="", purchase_cap=None, refund_cap=None):
    out = dict(row)
    out["Cantidad de descuento / beneficio"] = benefit
    out["Día de promoción"] = day or row["Día de promoción"]
    scope_detail = scope.rstrip(".")
    if scope_detail.casefold() in benefit.casefold():
        scope_detail = ""
    limits = []
    if purchase_cap:
        limits.append(f"Límite de compra mensual por cuenta: {money(purchase_cap)}.")
    if refund_cap:
        limits.append(f"Tope mensual de reintegro o descuento: {money(refund_cap)}.")
    out["Montos / topes"] = " ".join(limits)
    out["Detalle"] = " ".join(filter(None, [
        benefit + ".",
        scope_detail + "." if scope_detail else "",
        CARDS + ".",
        out["Montos / topes"],
    ]))
    out["Tarjetas verificadas"] = CARDS
    merchant_key = re.sub(r"[^a-z0-9]+", "-", row["Comercio/Promoción"].casefold()).strip("-")
    out["Variante"] = f"cu-{Path(urlparse(row['Bases y condiciones URL']).path).stem}-{merchant_key}-{index}"
    out["Tipo de variante"] = "base"
    out["Etiqueta de variante"] = scope or "Tarjetas de crédito"
    return out


def reviewed_rows(row):
    name = row["Comercio/Promoción"]
    document = Path(urlparse(row["Bases y condiciones URL"]).path).name
    if name in UNQUANTIFIED:
        return [], UNQUANTIFIED[name]
    if name in REVIEWED_PDF and document != REVIEWED_PDF[name]:
        return [], "Cambió el PDF oficial; requiere nueva lectura de la tabla"

    if name in PAYMENT_TABLES:
        qr, physical, kind, purchase = PAYMENT_TABLES[name]
        if not all(re.search(rf"\b{rate}\s*%", row["Detalle"]) for rate in (qr, physical)):
            return [], "La tabla del PDF ya no coincide con las tasas revisadas"
        return [
            variant(row, f"{'Hasta ' if name in {'FARMACIA ENERGY', 'Farmatotal'} else ''}{qr}% de {kind} con QR", 0,
                    scope="Pago con QR en la app Universitaria", purchase_cap=purchase, refund_cap=purchase * qr // 100),
            variant(row, f"{physical}% de {kind} con tarjeta física", 1, scope="Pago con tarjeta de crédito física", purchase_cap=purchase,
                    refund_cap=None if name == "Hipermercado Luisito" else purchase * physical // 100),
        ], ""

    if name in SPECIAL:
        result = []
        for index, (rate, kind, scope) in enumerate(SPECIAL[name]):
            if name not in REVIEWED_PDF and not re.search(rf"\b{rate}\s*%", row["Detalle"]):
                return [], f"No se encontró el {rate}% revisado en el PDF"
            purchase = 10000000 if name == "Punto Farma" else 5000000 if name in {
                "Farmacenter", "Farmacia Catedral", "Farmaoliva"
            } else None
            result.append(variant(row, f"{'Hasta ' if rate in {45, 50} else ''}{rate}% de {kind} con {scope}" if scope.startswith(("QR", "tarjeta")) else f"{rate}% de {kind} en {scope}",
                                  index, scope=scope, purchase_cap=purchase,
                                  refund_cap=purchase * rate // 100 if purchase and name in {"Farmacenter", "Farmaoliva"} else None))
        return result, ""

    if name == "Todo Cubierta":
        return [
            variant(row, "5% de descuento en cubiertas", 0, day="Lunes, martes y jueves", scope="Compras de cubiertas"),
            variant(row, "10% de descuento en cubiertas", 1, day="Miércoles y viernes", scope="Compras de cubiertas"),
            variant(row, "20% de descuento en alineación, balanceo y rotación", 2, day="Todos los días", scope="Servicios de alineación, balanceo y rotación"),
            variant(row, "Hasta 6 cuotas sin intereses", 3, day="Todos los días", scope="Compras con tarjetas de crédito"),
        ], ""

    if name == "ELECTROBAN":
        return [
            variant(row, "5% de descuento en productos HD Play", 0, day="Todos los días", scope="Línea HD Play"),
            variant(row, "Hasta 10 cuotas sin intereses", 1, day="Todos los días", scope="Compras con tarjetas de crédito"),
        ], ""
    if name == "UNIVERSIDAD CATÓLICA":
        return [
            variant(row, "10% de descuento en cuotas", 0, day="del 1 al 5 de cada mes",
                    scope="Pago de cuotas con QR o tarjeta física; el 20% para semestres terminó el 31 de agosto de 2026"),
            variant(row, "Hasta 10 cuotas sin intereses", 1, day="del 1 al 5 de cada mes",
                    scope="Pago de cuotas de la universidad con tarjetas de crédito"),
        ], ""
    if name == "UNIVERSIDAD AMERICANA":
        return [variant(row, "Hasta 10 cuotas sin intereses", 0, day="Durante el período de inscripción",
                        scope="Diplomado Business Intelligence; el precio para socios ya incluye el 7% de descuento")], ""
    if name == "Avenida Autocentro":
        return [
            variant(row, "20% de descuento", 0, day="Todos los días", scope="Sobre precio de lista vigente"),
            variant(row, "Hasta 6 cuotas sin intereses", 1, day="Todos los días", scope="Compras con tarjetas de crédito"),
        ], ""
    if name == "Essen":
        return [
            variant(row, "30% de descuento en combos promocionales", 0, day="Todos los días", scope="Combos promocionales"),
            variant(row, "Hasta 6 cuotas sin intereses", 1, day="Todos los días", scope="Compras con tarjetas de crédito"),
        ], ""
    if name == "Cellshop Importados Paraguay":
        return [variant(row, "Hasta 10 cuotas sin intereses", 0, day="Todos los días",
                        scope="El 10% de descuento solo corresponde a fechas especiales no anunciadas")], ""
    if name == "Ferrex":
        return [variant(row, "Hasta 6 cuotas sin intereses", 0, day="Todos los días",
                        scope="Los descuentos se anuncian para fechas específicas, sin calendario vigente en el PDF")], ""
    if name in SIMPLE:
        benefit = SIMPLE[name]
        marker = re.search(r"(\d{1,2})\s*%", benefit)
        if marker and not re.search(rf"\b{marker[1]}\s*%", row["Detalle"]):
            return [], f"No se encontró el {marker[1]}% revisado en el PDF"
        if "cuotas sin intereses" in benefit and not re.search(r"\b(?:diez\s*\(10\)|10)\s+cuotas\s+sin\s+intereses", row["Detalle"], re.I):
            return [], "No se encontró la financiación revisada en el PDF"
        return [variant(row, benefit, 0, scope="Beneficio indicado en las bases")], ""

    benefit = row["Cantidad de descuento / beneficio"]
    if re.search(r"\b\d{1,3}\s*%|\b\d{1,2}(?:\s*\([^)]+\))?\s+cuotas", benefit):
        return [row], ""
    return [], "El título no identifica una tasa o cantidad de cuotas verificable"


def review(rows):
    output, withheld = [], []
    for row in rows:
        variants, reason = reviewed_rows(row)
        output.extend(variants)
        if reason:
            withheld.append({"merchant": row["Comercio/Promoción"],
                             "source": row["Bases y condiciones URL"], "reason": reason})
    return output, withheld


def main():
    if "--snapshot-committed" in sys.argv:
        source = subprocess.run(
            ["git", "show", "HEAD:outputs/universitaria_beneficios_por_categoria.csv"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8-sig", check=True,
        )
        captured = list(csv.DictReader(io.StringIO(source.stdout)))
        SNAPSHOT.write_text(json.dumps(captured, ensure_ascii=False, indent=2), encoding="utf-8")
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        original = list(csv.DictReader(handle))
    if any(row.get("Variante") for row in original):
        original = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    rows, withheld = review(original)
    if not rows:
        raise ValueError("Universitaria review produced no publishable benefits")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with SOURCE.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Cooperativa Universitaria - promociones por categoria", "",
        "Fuente: https://www.universitaria.coop/promociones", "",
        f"Total de beneficios verificados: {len(rows)}", "",
    ]
    for category in sorted({row["Categoría"] for row in rows}):
        lines.extend([
            f"## {category}", "",
            "| Comercio/Promoción | Beneficio | Día | Vigencia | Bases |",
            "|---|---|---|---|---|",
        ])
        for row in (item for item in rows if item["Categoría"] == category):
            cells = [row[key].replace("|", "\\|") for key in (
                "Comercio/Promoción", "Cantidad de descuento / beneficio",
                "Día de promoción", "Vigencia",
            )]
            lines.append(f"| {' | '.join(cells)} | [PDF]({row['Bases y condiciones URL']}) |")
        lines.append("")
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    REPORT.write_text(json.dumps({
        "source_cards": len(original), "published_variants": len(rows),
        "withheld": withheld,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Universitaria: {len(original)} source cards, {len(rows)} scoped benefits, {len(withheld)} withheld")


if __name__ == "__main__":
    main()
