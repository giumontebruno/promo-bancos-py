import csv
import json
import re
from html import unescape
from pathlib import Path

import requests


BASE = "https://www.bancontinental.com.py"
API = f"{BASE}/api/comercios?_limit=-1"
OUT_CSV = Path("outputs/continental_beneficios_por_categoria.csv")
OUT_MD = Path("outputs/continental_beneficios_por_categoria.md")
WORK_JSON = Path("work/continental_comercios.json")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("**", " ").replace("__", " ")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def first_match(text, patterns, default="No especificado"):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            return clean(m.group(1) if m.groups() else m.group(0)).strip(". ")
    return default


def extract_day(text):
    return first_match(
        text,
        [
            r"\b(Todos los días)\b",
            r"\b(Los\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos))\b",
            r"\b(Todos los\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábados|sabados|domingos))\b",
            r"\b(Primer\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)[^.]*)",
            r"\b(Tercer\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)[^.]*)",
            r"\b(?:Desde|de)\s+los\s+(.{0,50}?(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo).{0,80}?)(?:\.|\n)",
        ],
    )


def extract_vigencia(text):
    return first_match(
        text,
        [
            r"(Vigente desde\s+.*?(?:\.|$))",
            r"(Vigente hasta\s+.*?(?:\.|$))",
            r"(Válido hasta\s+.*?(?:\.|$))",
            r"(Valido hasta\s+.*?(?:\.|$))",
        ],
    )


def extract_discount(item, text):
    parts = []
    pct = item.get("porcentaje_ahorro") or {}
    if pct.get("titulo"):
        parts.append(pct["titulo"])
    for pattern in [
        r"hasta\s+\d+\s+cuotas?\s+sin\s+inter[eé]s(?:es)?",
        r"\d+\s*%\s+de\s+reintegro",
        r"\d+\s*%\s+en\s+caja",
        r"\d+\s*%\s+de\s+descuento",
    ]:
        parts.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(parts)) or "Ver descripción"


def extract_topes(text):
    hits = []
    for pattern in [
        r"l[ií]mite[^.]{0,160}",
        r"tope[^.]{0,160}",
        r"Gs\.?\s*[\d\.]+",
    ]:
        hits.extend(clean(m.group(0)) for m in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(hits)) or "No especificado"


def main():
    if WORK_JSON.exists():
        data = json.loads(WORK_JSON.read_text(encoding="utf-8-sig"))
    else:
        data = requests.get(API, timeout=30).json()
        WORK_JSON.parent.mkdir(exist_ok=True)
        WORK_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    rows = []
    for item in data:
        desc = clean(item.get("descripcion"))
        rubro = item.get("rubro") or {}
        ciudad = item.get("ciudad") or {}
        logo = item.get("logo") or {}
        rows.append(
            {
                "Categoría": rubro.get("nombre") or "Sin categoría",
                "Banco": "Continental",
                "Comercio/Promoción": clean(item.get("nombre")),
                "Cantidad de descuento / beneficio": extract_discount(item, desc),
                "Día de promoción": extract_day(desc),
                "Vigencia": extract_vigencia(desc),
                "Ciudad": ciudad.get("nombre") or "No especificado",
                "Montos / topes": extract_topes(desc),
                "Detalle": desc,
                "Logo URL": BASE + logo.get("url") if logo.get("url") else "",
                "Fuente API": API,
            }
        )

    rows.sort(key=lambda r: (r["Categoría"], r["Comercio/Promoción"]))
    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    categories = {}
    for row in rows:
        categories.setdefault(row["Categoría"], []).append(row)

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("# Continental - beneficios por categoria\n\n")
        f.write(f"Fuente: {API}\n\nTotal de beneficios/comercios: {len(rows)}\n\n")
        for category in sorted(categories):
            f.write(f"## {category} ({len(categories[category])})\n\n")
            f.write("| Comercio/Promoción | Descuento / beneficio | Día | Vigencia | Ciudad |\n")
            f.write("|---|---|---|---|---|\n")
            for row in categories[category][:80]:
                vals = [
                    row["Comercio/Promoción"],
                    row["Cantidad de descuento / beneficio"],
                    row["Día de promoción"],
                    row["Vigencia"],
                    row["Ciudad"],
                ]
                f.write("| " + " | ".join(clean(v).replace("|", "/")[:180] for v in vals) + " |\n")
            if len(categories[category]) > 80:
                f.write(f"\n_Se omitieron {len(categories[category]) - 80} filas en este resumen; están en el CSV._\n")
            f.write("\n")

    print(f"{len(rows)} beneficios -> {OUT_CSV} and {OUT_MD}")
    for cat, cat_rows in sorted(categories.items(), key=lambda kv: kv[0])[:20]:
        print(f"{cat}: {len(cat_rows)}")


if __name__ == "__main__":
    main()
