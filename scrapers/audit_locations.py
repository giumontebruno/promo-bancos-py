import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCATIONS_JSON = ROOT / "public" / "locations.json"
REPORT_JSON = ROOT / "outputs" / "locations_quality_report.json"
REPORT_CSV = ROOT / "outputs" / "locations_review_queue.csv"

METRO_CITIES = {
    "asuncion",
    "fernando de la mora",
    "san lorenzo",
    "luque",
    "lambare",
    "mariano roque alonso",
    "limpio",
    "capiata",
    "nemby",
    "villa elisa",
    "san antonio",
}


def strip_accents(value):
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def norm(value):
    return re.sub(r"\s+", " ", strip_accents(str(value or "")).lower()).strip()


def is_metro(item):
    return norm(item.get("city")) in METRO_CITIES or norm(item.get("department")) in {"capital", "central"}


def distance_km(a, b):
    lat1, lon1 = math.radians(float(a["lat"])), math.radians(float(a["lng"]))
    lat2, lon2 = math.radians(float(b["lat"])), math.radians(float(b["lng"]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def review_reason(item):
    source = item.get("geocode_source") or ""
    confidence = item.get("google_confidence") or ""
    if source in {"", "city_approximation"}:
        return "Coordenada aproximada o faltante"
    if confidence == "review":
        return "Google encontro un resultado, pero el nombre/direccion requiere revision"
    if source == "nominatim":
        return "Ubicacion tomada de OpenStreetMap, conviene validar con Google"
    return ""


def merchant_key(item):
    return "|".join(norm(item.get(field)) for field in ["merchant_name", "address", "city"])


def find_close_conflicts(locations):
    by_name = defaultdict(list)
    for item in locations:
        if not isinstance(item.get("lat"), (int, float)) or not isinstance(item.get("lng"), (int, float)):
            continue
        by_name[norm(item.get("merchant_name"))].append(item)
    conflicts = []
    for items in by_name.values():
        if len(items) < 2:
            continue
        for index, current in enumerate(items):
            for other in items[index + 1:]:
                if merchant_key(current) == merchant_key(other):
                    continue
                if distance_km(current, other) < 0.04:
                    conflicts.append({
                        "merchant_name": current.get("merchant_name"),
                        "location_a": current.get("address"),
                        "location_b": other.get("address"),
                        "city": current.get("city") or other.get("city"),
                        "distance_m": round(distance_km(current, other) * 1000),
                    })
    return conflicts[:100]


def main():
    payload = json.loads(LOCATIONS_JSON.read_text(encoding="utf-8"))
    locations = payload.get("locations") or []
    review_rows = []
    source_counts = Counter(item.get("geocode_source") or "missing" for item in locations)
    confidence_counts = Counter(item.get("google_confidence") or "not_google" for item in locations)
    for item in locations:
        reason = review_reason(item)
        if not reason:
            continue
        review_rows.append({
            "reason": reason,
            "bank": item.get("bank", ""),
            "category": item.get("category", ""),
            "merchant_name": item.get("merchant_name", ""),
            "address": item.get("address", ""),
            "city": item.get("city", ""),
            "department": item.get("department", ""),
            "geocode_source": item.get("geocode_source", ""),
            "google_confidence": item.get("google_confidence", ""),
            "google_name": item.get("google_name", ""),
            "formatted_address": item.get("formatted_address", ""),
            "lat": item.get("lat", ""),
            "lng": item.get("lng", ""),
            "source_url": item.get("source_url", ""),
        })
    review_rows.sort(key=lambda row: (
        0 if norm(row["city"]) in METRO_CITIES else 1,
        row["reason"],
        row["bank"],
        row["category"],
        row["merchant_name"],
    ))
    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "total_locations": len(locations),
        "metro_locations": sum(1 for item in locations if is_metro(item)),
        "with_coordinates": sum(1 for item in locations if isinstance(item.get("lat"), (int, float)) and isinstance(item.get("lng"), (int, float))),
        "precise_or_google_locations": sum(1 for item in locations if (item.get("geocode_source") or "") not in {"", "city_approximation"}),
        "needs_review": len(review_rows),
        "needs_review_metro": sum(1 for row in review_rows if norm(row["city"]) in METRO_CITIES or norm(row["department"]) in {"capital", "central"}),
        "source_counts": dict(source_counts),
        "confidence_counts": dict(confidence_counts),
        "close_conflicts": find_close_conflicts(locations),
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0].keys()) if review_rows else ["reason"])
        writer.writeheader()
        writer.writerows(review_rows)
    print(f"{report['with_coordinates']}/{report['total_locations']} with coordinates")
    print(f"{report['needs_review']} need review ({report['needs_review_metro']} metro)")
    print(f"Review queue -> {REPORT_CSV}")


if __name__ == "__main__":
    main()
