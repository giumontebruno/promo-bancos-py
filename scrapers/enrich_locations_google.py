import json
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
LOCATIONS_JSON = ROOT / "public" / "locations.json"
CACHE_PATH = ROOT / "work" / "google_locations_cache.json"
METRO_OUTPUT = ROOT / "outputs" / "google_locations_metro_review.json"
GOOGLE_KEY = os.environ.get("GOOGLE_MAPS_BACKEND_API_KEY") or os.environ.get("PAYBACK_GOOGLE_MAPS_API_KEY")
LIMIT = int(os.environ.get("GOOGLE_LOCATION_LIMIT", "60"))
SLEEP_SECONDS = float(os.environ.get("GOOGLE_LOCATION_SLEEP", "0.12"))

METRO_CITIES = {
    "asuncion",
    "asunción",
    "fernando de la mora",
    "san lorenzo",
    "luque",
    "lambare",
    "lambaré",
    "mariano roque alonso",
    "limpio",
    "capiata",
    "capiatá",
    "nemby",
    "ñemby",
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


def load_json(path, fallback):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return fallback


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_metro_location(item):
    city = norm(item.get("city"))
    department = norm(item.get("department"))
    return city in {norm(city) for city in METRO_CITIES} or department in {"capital", "central"}


def should_enrich(item):
    if not is_metro_location(item):
        return False
    source = item.get("geocode_source") or ""
    return source in {"", "city_approximation", "nominatim"}


def cache_key(item):
    return "|".join(norm(item.get(field)) for field in ["merchant_name", "address", "city", "department"])


def query_text(item):
    parts = [
        item.get("merchant_name"),
        item.get("address"),
        item.get("city"),
        "Paraguay",
    ]
    return ", ".join(part for part in parts if part)


def google_text_search(item):
    response = requests.post(
        "https://places.googleapis.com/v1/places:searchText",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types",
        },
        json={
            "textQuery": query_text(item),
            "regionCode": "PY",
            "locationBias": {
                "circle": {
                    "center": {"latitude": -25.2867, "longitude": -57.6282},
                    "radius": 45000,
                }
            },
            "maxResultCount": 3,
        },
        timeout=25,
    )
    if response.status_code == 403:
        raise RuntimeError("Google Places API denied the request. Enable Places API (New) and allow it in the backend key restrictions.")
    if response.status_code == 400:
        raise RuntimeError(f"Google Places API rejected the request: {response.text[:500]}")
    response.raise_for_status()
    places = response.json().get("places") or []
    if not places:
        return None
    place = places[0]
    location = place.get("location") or {}
    if "latitude" not in location or "longitude" not in location:
        return None
    return {
        "lat": round(float(location["latitude"]), 7),
        "lng": round(float(location["longitude"]), 7),
        "place_id": place.get("id", ""),
        "formatted_address": place.get("formattedAddress", ""),
        "google_name": (place.get("displayName") or {}).get("text", ""),
        "google_types": place.get("types") or [],
        "source": "google_places_text_search",
        "confidence": score_result(item, place),
    }


def google_geocode(item):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": query_text(item),
            "region": "py",
            "key": GOOGLE_KEY,
        },
        timeout=25,
    )
    if response.status_code == 403:
        raise RuntimeError("Google Geocoding API denied the request. Enable Geocoding API and allow it in the backend key restrictions.")
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "OK" or not payload.get("results"):
        return None
    result = payload["results"][0]
    location = result.get("geometry", {}).get("location", {})
    if "lat" not in location or "lng" not in location:
        return None
    return {
        "lat": round(float(location["lat"]), 7),
        "lng": round(float(location["lng"]), 7),
        "place_id": result.get("place_id", ""),
        "formatted_address": result.get("formatted_address", ""),
        "google_name": "",
        "google_types": result.get("types") or [],
        "source": "google_geocoding",
        "confidence": "medium",
    }


def score_result(item, place):
    merchant = norm(item.get("merchant_name"))
    address = norm(item.get("address"))
    found_name = norm((place.get("displayName") or {}).get("text"))
    found_address = norm(place.get("formattedAddress"))
    if merchant and merchant in found_name and address and any(token in found_address for token in address.split()[:3]):
        return "high"
    if merchant and merchant in found_name:
        return "medium"
    if address and any(token in found_address for token in address.split()[:4]):
        return "medium"
    return "review"


def enrich_one(item, cache):
    key = cache_key(item)
    if key in cache:
        return cache[key]
    result = google_text_search(item)
    if not result:
        result = google_geocode(item)
    cache[key] = result
    time.sleep(SLEEP_SECONDS)
    return result


def apply_result(item, result):
    if not result:
        item["google_enrichment_status"] = "not_found"
        return item
    item["lat"] = result["lat"]
    item["lng"] = result["lng"]
    item["place_id"] = result.get("place_id", "")
    item["formatted_address"] = result.get("formatted_address", "")
    item["google_name"] = result.get("google_name", "")
    item["google_types"] = result.get("google_types", [])
    item["geocode_source"] = result.get("source", "google")
    item["google_confidence"] = result.get("confidence", "review")
    item["google_enrichment_status"] = "matched"
    return item


def main():
    if not GOOGLE_KEY:
        print("GOOGLE_MAPS_BACKEND_API_KEY is not set. Skipping Google location enrichment.")
        return
    payload = load_json(LOCATIONS_JSON, {})
    locations = payload.get("locations") or []
    cache = load_json(CACHE_PATH, {})
    enriched = 0
    reviewed = []
    for item in locations:
        if not should_enrich(item):
            continue
        try:
            result = enrich_one(item, cache)
        except RuntimeError as error:
            print(str(error))
            break
        apply_result(item, result)
        if result:
            enriched += 1
            if result.get("confidence") == "review":
                reviewed.append(item)
        if enriched >= LIMIT:
            break
    payload["google_enriched_locations"] = sum(1 for item in locations if str(item.get("geocode_source", "")).startswith("google_"))
    payload["geocoded_locations"] = sum(
        1 for item in locations
        if isinstance(item.get("lat"), (int, float)) and isinstance(item.get("lng"), (int, float))
    )
    payload["google_enrichment_focus"] = "Asunción y Gran Asunción"
    payload["locations_updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    save_json(LOCATIONS_JSON, payload)
    save_json(CACHE_PATH, cache)
    save_json(METRO_OUTPUT, reviewed[:100])
    print(f"Google-enriched {enriched} locations. Total Google locations: {payload['google_enriched_locations']}")


if __name__ == "__main__":
    main()
