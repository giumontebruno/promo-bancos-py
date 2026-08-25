import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCATIONS_JSON = ROOT / "public" / "locations.json"


MANUAL_FUEL_LOCATIONS = [
    {
        "bank": "ueno bank",
        "category": "Combustible",
        "source_category": "Combustible",
        "merchant_name": "Petropar",
        "address": "Av. Dr. Felipe Molas Lopez esq. Lorenzo Perez Velloso",
        "city": "Asuncion",
        "department": "Capital",
        "country": "Paraguay",
        "source_url": "https://www.ueno.com.py/wp-content/uploads/2026/07/Promocion-Reintegro-Petropar_-AGO-2026v2.pdf",
        "lat": -25.2688,
        "lng": -57.57319,
        "geocode_source": "manual_ueno_petropar_pdf",
        "place_id": "",
        "formatted_address": "Av. Dr. Felipe Molas Lopez 1250, Asuncion 001520, Paraguay",
        "google_name": "Petropar Molas Lopez",
        "google_types": ["gas_station", "point_of_interest", "establishment"],
        "google_confidence": "manual",
        "google_enrichment_status": "matched",
    },
]


def stable_id(item):
    raw = "|".join([
        item.get("bank", ""),
        item.get("category", ""),
        item.get("merchant_name", ""),
        item.get("address", ""),
        item.get("city", ""),
    ])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"loc-manual-{digest}"


def key_for(item):
    return "|".join(str(item.get(field, "")).strip().lower() for field in ["merchant_name", "address", "city"])


def main():
    payload = json.loads(LOCATIONS_JSON.read_text(encoding="utf-8"))
    locations = payload.get("locations", [])
    by_key = {key_for(item): index for index, item in enumerate(locations)}
    added = 0
    updated = 0
    for location in MANUAL_FUEL_LOCATIONS:
        item = {"id": stable_id(location), **location}
        key = key_for(item)
        if key in by_key:
            locations[by_key[key]].update(item)
            updated += 1
        else:
            locations.append(item)
            by_key[key] = len(locations) - 1
            added += 1

    payload["locations"] = locations
    payload["total_locations"] = len(locations)
    payload["geocoded_locations"] = sum(
        1 for item in locations
        if isinstance(item.get("lat"), (int, float)) and isinstance(item.get("lng"), (int, float))
    )
    payload["manual_fuel_locations_updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    LOCATIONS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manual fuel locations patched: {added} added, {updated} updated")


if __name__ == "__main__":
    main()
