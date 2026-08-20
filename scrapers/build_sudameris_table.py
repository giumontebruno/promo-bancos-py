import csv
import re
from pathlib import Path


IN = Path("outputs/sudameris_promociones.csv")
OUT_CSV = Path("outputs/sudameris_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/sudameris_beneficios_por_categoria.md")


CATEGORIES = [
    ("Supermercados", ["LUISITO", "REAL SUPERMERCADOS", "FRIGOMAS"]),
    ("Farmacias", ["FARMACENTER", "FARMACIA", "BIGGIE FARMA", "DRUGSTORE"]),
    ("Combustible", ["COPETROL", "COPEMARKET", "ENEX", "ECOP", "ESTACIONES DE SERVICIO", "CCU"]),
    ("Gastronomía", ["GASTRONOM", "RESTAURANTE", "PARU", "CONCEPTS", "BISTRO", "SERENDIPITY", "HORNALLA", "CANTINA", "BIGGIE EXPRESS"]),
    ("Viajes y turismo", ["TRAVEL", "DTP", "POSADA", "YACHT", "HOTEL", "PAQUETE", "ALOJAMIENTO"]),
    ("Moda", ["BABY COTTONS", "ADOLFO DOMINGUEZ", "CARO CUORE", "RAPSODIA", "ESTANCIAS", "YOUNIQUE"]),
    ("Hogar", ["MATERASSI", "PARANA HOGAR", "COLCHONES", "LINCOLN"]),
    ("Deportes y clubes", ["CLUB", "LIVE FITNESS", "DEPORTIVO", "NÁUTICO", "NAUTICO"]),
    ("Entretenimiento y experiencias", ["MCLAREN", "F1", "DISTRITO PERSEVERANCIA"]),
    ("Cuotas y tarjetas", ["CUOTAS", "TARJETAS EMPRESARIALES", "COMPRAS EN EL EXTERIOR", "SUDAMERIS GO"]),
    ("Solidaridad", ["DONACIÓN", "DONACION", "TECHO"]),
]


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip().strip(":").strip()


def category_for(row):
    haystack = f"{row['Comercio/Promocion']} {row['Beneficios']} {row['Texto completo']}".upper()
    for category, keys in CATEGORIES:
        if any(key in haystack for key in keys):
            return category
    return "Otros"


def extract_day(row):
    text = clean(f"{row['Vigencia']} {row['Texto completo']}")
    patterns = [
        r"Todos los (lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos)",
        r"(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+a\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"Martes a domingo",
        r"Miércoles a sábado",
        r"Viernes y sábados",
        r"primer (lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"Solo el primer (lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)",
        r"\b\d{1,2}\s+de cada mes\b",
        r"\bTodos los días\b",
    ]
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            found.append(clean(match.group(0)))
    return "; ".join(dict.fromkeys(found)) or "No especificado"


def extract_vigencia(row):
    vigencia = clean(row["Vigencia"])
    text = clean(row["Texto completo"])
    if vigencia and len(vigencia) > 8 and "según las" not in vigencia.lower():
        return vigencia
    for pattern in [
        r"Periodo de campaña:\s*(.*?)(?:\.| Beneficio)",
        r"Vigencia:\s*(.*?)(?:\.| Beneficio)",
        r"vigencia desde\s+(.*?)(?:\.|$)",
        r"Desde el\s+.*?hasta el\s+.*?(?:2026|2025)",
        r"Del\s+\d{1,2}/\d{1,2}\s+al\s+\d{1,2}/\d{1,2}/\d{4}",
    ]:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return vigencia or "No especificado"


def extract_discount(row):
    bits = []
    for col in ["% detectado", "Cuotas detectadas", "Tope detectado"]:
        value = clean(row.get(col, ""))
        if value:
            bits.append(value)
    benefit = clean(row["Beneficios"]) or clean(row["Texto completo"])
    amounts = re.findall(r"(?:Gs\.?\s*[\d\.]+|USD\s*\d+)", benefit, flags=re.I)
    for amount in amounts:
        if amount not in bits:
            bits.append(clean(amount))
    if bits:
        return "; ".join(dict.fromkeys(bits))
    return benefit[:180] if benefit else "No especificado"


def main():
    with IN.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    table = []
    for row in rows:
        table.append(
            {
                "Categoría": category_for(row),
                "Banco": "Sudameris",
                "Comercio/Promoción": clean(row["Comercio/Promocion"]),
                "Cantidad de descuento / beneficio": extract_discount(row),
                "Día de promoción": extract_day(row),
                "Vigencia": extract_vigencia(row),
                "Detalle": clean(row["Beneficios"]) or clean(row["Texto completo"]),
                "URL": row["URL"],
            }
        )

    table.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        writer.writeheader()
        writer.writerows(table)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Sudameris - beneficios por categoria\n\n")
        f.write(f"Total de promociones: {len(table)}\n\n")
        for category in sorted({r["Categoría"] for r in table}):
            f.write(f"## {category}\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia |\n")
            f.write("|---|---|---|---|\n")
            for row in [r for r in table if r["Categoría"] == category]:
                values = [
                    row["Comercio/Promoción"],
                    row["Cantidad de descuento / beneficio"],
                    row["Día de promoción"],
                    row["Vigencia"],
                ]
                f.write("| " + " | ".join(v.replace("|", "/")[:220] for v in values) + " |\n")
            f.write("\n")

    print(f"Tabla creada: {OUT_CSV}")
    print(f"Resumen creado: {OUT_MD}")


if __name__ == "__main__":
    main()
