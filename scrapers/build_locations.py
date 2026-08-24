import hashlib
import json
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

import extract_bnf


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "public" / "locations.json"
OUT_CSV = ROOT / "outputs" / "locations.csv"
CACHE_PATH = ROOT / "work" / "geocoding_cache.json"
USER_AGENT = "PaybackPY/0.1 (https://github.com/giumontebruno/promo-bancos-py)"
DEFAULT_GEOCODE_LIMIT = int(os.environ.get("GEOCODE_LIMIT", "80"))

CATEGORY_MAP = {
    "Estaciones de Servicio": "Combustible",
    "Frigoríficos": "Supermercados",
}

MOJIBAKE_FIXES = {
    "�": "",
    "Asuncin": "Asuncion",
    "Asunci�n": "Asuncion",
    "Capiat�": "Capiata",
    "Minga Guaz�": "Minga Guazu",
    "Alto Paran�": "Alto Parana",
    "Itap�a": "Itapua",
    "Caaguaz�": "Caaguazu",
    "Ñemby": "Nemby",
    "San Jos": "San Jose",
    "Jos�": "Jose",
    "F�lix": "Felix",
    "L�pez": "Lopez",
    "Rodr�guez": "Rodriguez",
    "Mens�": "Mensa",
    "Garc�a": "Garcia",
}

SEED_POINTS = [
    ("Shopping del Sol", "Shopping del Sol", "Asuncion", "Capital", -25.28288, -57.56706),
    ("Paseo La Galeria", "Paseo La Galeria", "Asuncion", "Capital", -25.2819, -57.5638),
    ("Shopping Mariscal", "Shopping Mariscal", "Asuncion", "Capital", -25.2964, -57.5814),
    ("Pinedo Shopping", "Pinedo Shopping", "San Lorenzo", "Central", -25.32396, -57.52098),
    ("Shopping Mariano", "Shopping Mariano", "Mariano Roque Alonso", "Central", -25.2076, -57.5323),
    ("Multiplaza", "Multiplaza", "Asuncion", "Capital", -25.29831, -57.55011),
    ("CIT", "Club Internacional de Tenis", "Asuncion", "Capital", -25.28935, -57.60074),
    ("Asuncion Tenis Club", "Asuncion Tenis Club", "Asuncion", "Capital", -25.2871, -57.6087),
    ("Club Cerro Porteno", "Club Cerro Porteno", "Asuncion", "Capital", -25.2979, -57.6591),
    ("Club Olimpia", "Club Olimpia", "Asuncion", "Capital", -25.2912, -57.6426),
    ("Distrito Perseverancia", "Distrito Perseverancia", "Asuncion", "Capital", -25.28763, -57.58251),
    ("Casa Rica Molas Lopez", "Casa Rica Molas Lopez", "Asuncion", "Capital", -25.27381, -57.57173),
    ("Superseis Los Laureles", "Superseis Los Laureles", "Asuncion", "Capital", -25.2998, -57.5706),
]

CITY_COORDS = {
    "asuncion": (-25.2867, -57.6282),
    "fernando de la mora": (-25.3232, -57.5409),
    "san lorenzo": (-25.3397, -57.5088),
    "luque": (-25.2673, -57.4856),
    "lambare": (-25.3468, -57.6065),
    "mariano roque alonso": (-25.2076, -57.5323),
    "limpio": (-25.1661, -57.4856),
    "capiata": (-25.3552, -57.4456),
    "nemby": (-25.3949, -57.5357),
    "villa elisa": (-25.3676, -57.5927),
    "san antonio": (-25.4213, -57.5475),
    "ciudad del este": (-25.5167, -54.6167),
    "ciudad de este": (-25.5167, -54.6167),
    "minga guazu": (-25.4896, -54.7611),
    "hernandarias": (-25.4078, -54.6404),
    "presidente franco": (-25.5333, -54.6167),
    "encarnacion": (-27.3306, -55.8667),
    "coronel oviedo": (-25.4444, -56.4403),
    "caaguazu": (-25.4648, -56.0167),
    "villarrica": (-25.7500, -56.4333),
    "loma plata": (-22.3828, -59.8350),
}


def clean_text(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    for bad, good in MOJIBAKE_FIXES.items():
        text = text.replace(bad, good)
    return text.strip(" .")


def strip_accents(value):
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def slug(value):
    normalized = strip_accents(clean_text(value)).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "local"


def stable_id(*parts):
    digest = hashlib.sha1("|".join(clean_text(part) for part in parts).encode("utf-8")).hexdigest()[:10]
    return f"loc-{digest}"


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def geocode(query, cache, remaining):
    key = strip_accents(query).lower()
    if key in cache:
        return cache[key], remaining
    if remaining <= 0:
        return None, remaining
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1, "countrycodes": "py"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    result = None
    if data:
        result = {
            "lat": round(float(data[0]["lat"]), 6),
            "lng": round(float(data[0]["lon"]), 6),
            "label": data[0].get("display_name", ""),
        }
    cache[key] = result
    time.sleep(1.1)
    return result, remaining - 1


def row_to_location(promo, row, index):
    category = CATEGORY_MAP.get(promo["categoria"], promo["categoria"])
    source_category = promo["categoria"]
    if len(row) >= 5:
        merchant = clean_text(row[1])
        address = clean_text(row[2])
        city = clean_text(row[3])
        department = clean_text(row[4])
    else:
        merchant = clean_text(source_category)
        address = clean_text(row[1] if len(row) > 1 else "")
        city = clean_text(row[2] if len(row) > 2 else "")
        department = clean_text(row[3] if len(row) > 3 else "")
    if merchant.lower().startswith(("avda", "avenida", "calle", "ruta", "km", "dr.")):
        merchant = clean_text(promo.get("marcas") or source_category)
    return {
        "id": stable_id("BNF", source_category, merchant, address, city, index),
        "bank": "BNF",
        "category": category,
        "source_category": source_category,
        "merchant_name": merchant,
        "address": address,
        "city": city,
        "department": department,
        "country": "Paraguay",
        "source_url": promo["pdf"],
        "lat": None,
        "lng": None,
        "geocode_source": "",
    }


def seed_locations():
    locations = []
    for name, address, city, department, lat, lng in SEED_POINTS:
        locations.append({
            "id": stable_id("seed", name, address, city),
            "bank": "Varios",
            "category": "Referencia",
            "source_category": "Referencia",
            "merchant_name": name,
            "address": address,
            "city": city,
            "department": department,
            "country": "Paraguay",
            "source_url": "",
            "lat": lat,
            "lng": lng,
            "geocode_source": "manual",
        })
    return locations


def build_bnf_locations():
    locations = []
    for promo in extract_bnf.PROMOS:
        pdf_path = extract_bnf.download_pdf(promo["pdf"])
        for index, row in enumerate(extract_bnf.table_rows(pdf_path), start=1):
            locations.append(row_to_location(promo, row, index))
    return locations


def geocode_locations(locations):
    cache = load_cache()
    remaining = DEFAULT_GEOCODE_LIMIT
    for item in locations:
        if item["lat"] is not None and item["lng"] is not None:
            continue
        if not item["address"] or item["address"].lower().startswith("app "):
            continue
        queries = [
            f"{item['merchant_name']}, {item['address']}, {item['city']}, Paraguay",
            f"{item['address']}, {item['city']}, Paraguay",
        ]
        for query in queries:
            result, remaining = geocode(query, cache, remaining)
            if result:
                item["lat"] = result["lat"]
                item["lng"] = result["lng"]
                item["geocode_source"] = "nominatim"
                break
            if remaining <= 0:
                break
        if remaining <= 0:
            break
    save_cache(cache)


def apply_city_approximations(locations):
    for item in locations:
        if item["lat"] is not None and item["lng"] is not None:
            continue
        key = strip_accents(clean_text(item["city"])).lower()
        coords = CITY_COORDS.get(key)
        if not coords:
            continue
        jitter_seed = int(hashlib.sha1(item["id"].encode("utf-8")).hexdigest()[:8], 16)
        lat_offset = ((jitter_seed % 17) - 8) * 0.0012
        lng_offset = (((jitter_seed // 17) % 17) - 8) * 0.0012
        item["lat"] = round(coords[0] + lat_offset, 6)
        item["lng"] = round(coords[1] + lng_offset, 6)
        item["geocode_source"] = "city_approximation"


def sort_key(item):
    has_coords = 0 if item["lat"] is not None and item["lng"] is not None else 1
    return (has_coords, item["bank"], item["category"], item["city"], item["merchant_name"])


def write_csv(locations):
    import csv

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "bank", "category", "merchant_name", "address", "city",
        "department", "lat", "lng", "geocode_source", "source_url",
    ]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in locations:
            writer.writerow({field: item.get(field, "") for field in fields})


def main():
    locations = seed_locations() + build_bnf_locations()
    seen = set()
    unique = []
    for item in locations:
        key = (item["bank"], slug(item["merchant_name"]), slug(item["address"]), slug(item["city"]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    geocode_locations(unique)
    apply_city_approximations(unique)
    unique.sort(key=sort_key)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "provider": "BNF PDF tables + cached OpenStreetMap Nominatim geocoding",
        "total_locations": len(unique),
        "geocoded_locations": sum(1 for item in unique if item["lat"] is not None and item["lng"] is not None),
        "locations": unique,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(unique)
    print(f"{payload['geocoded_locations']}/{payload['total_locations']} locations with coordinates -> {OUT_JSON}")


if __name__ == "__main__":
    main()
