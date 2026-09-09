import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone, timedelta
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
    last_attempt = item.get("google_last_attempt_at")
    if item.get("google_enrichment_status") in {"needs_review", "not_found"} and fresh(last_attempt, 7):
        return False
    return source in {"", "city_approximation", "nominatim"} or item.get("google_confidence") == "review" or (source.startswith("google") and not fresh(item.get("location_verified_at"), 28))


def fresh(timestamp, days):
    try:
        stamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return stamp.astimezone(timezone.utc) > datetime.now(timezone.utc) - timedelta(days=days)
    except (TypeError, ValueError, AttributeError):
        return False


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
    ranked = sorted(places, key=lambda place: match_score(item, place), reverse=True)
    place = ranked[0]
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
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
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
        "confidence": "review",
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


STOP_WORDS = {"av", "avda", "avenida", "calle", "ruta", "km", "esq", "esquina", "casi", "entre",
              "de", "del", "la", "las", "los", "el", "y", "sa", "s", "a", "dr", "gral"}
GENERIC_MERCHANTS = {"farmacias", "mayoristas", "supermercados", "estaciones de servicio", "frigorificos"}


def meaningful_tokens(value):
    return {token for token in re.findall(r"[a-z0-9]+", norm(value)) if token not in STOP_WORDS and len(token) > 2}


def match_score(item, place):
    location = place.get("location") or {}
    lat, lng = location.get("latitude"), location.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return 0
    if not (-25.6 < lat < -25.0 and -57.9 < lng < -57.2):
        return 0
    merchant = norm(item.get("merchant_name"))
    name = norm((place.get("displayName") or {}).get("text"))
    address = meaningful_tokens(item.get("address"))
    found_address = meaningful_tokens(place.get("formattedAddress"))
    overlap = len(address & found_address) / len(address) if address else 0
    name_tokens = meaningful_tokens(merchant)
    name_match = bool(name_tokens) and name_tokens <= meaningful_tokens(name)
    generic = merchant in GENERIC_MERCHANTS
    if "shopping_mall" in (place.get("types") or []) and generic:
        return 0
    city = norm(item.get("city"))
    if city and city not in norm(place.get("formattedAddress")):
        return 0
    # Chain name alone cannot distinguish its branches; street evidence is required.
    if overlap >= 0.65 and len(address & found_address) >= 2 and (name_match or generic):
        return 90 if name_match else 75
    return 30 if name_match else 0


def score_result(item, place):
    score = match_score(item, place)
    return "high" if score >= 90 else "medium" if score >= 75 else "review"


def enrich_one(item, cache):
    key = cache_key(item)
    if key in cache and cache[key] and fresh(cache[key].get("checked_at"), 28) and cache[key].get("confidence") != "review":
        return cache[key]
    result = google_text_search(item)
    if not result:
        result = google_geocode(item)
    cache[key] = result
    time.sleep(SLEEP_SECONDS)
    return result


def apply_result(item, result):
    item["google_last_attempt_at"] = datetime.now(timezone.utc).isoformat()
    if not result:
        item["google_enrichment_status"] = "not_found"
        return item
    if result.get("confidence") == "review":
        item["google_enrichment_status"] = "needs_review"
        item["google_confidence"] = "review"
        item["google_candidate_place_id"] = result.get("place_id", "")
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
    item["needs_review"] = False
    item["location_verified_at"] = result.get("checked_at", "")
    return item


def main():
    if not GOOGLE_KEY:
        raise RuntimeError("GOOGLE_MAPS_BACKEND_API_KEY is not set; location enrichment was not performed.")
    payload = load_json(LOCATIONS_JSON, {})
    locations = payload.get("locations") or []
    cache = load_json(CACHE_PATH, {})
    enriched = 0
    attempted = 0
    reviewed = []
    failed = False
    for item in locations:
        if not should_enrich(item):
            continue
        if attempted >= LIMIT:
            break
        attempted += 1
        try:
            result = enrich_one(item, cache)
        except (RuntimeError, requests.RequestException):
            print("Google location request failed. Check API enablement, billing and backend key restrictions.")
            failed = True
            break
        apply_result(item, result)
        if result:
            enriched += int(result.get("confidence") != "review")
            if result.get("confidence") == "review":
                reviewed.append(item)
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
    save_json(ROOT / "outputs/google_enrichment_report.json", {"attempted": attempted, "matched": enriched,
              "review_count": len(reviewed), "request_failed": failed,
              "updated_at": datetime.now(timezone.utc).isoformat()})
    print(f"Google-enriched {enriched} locations. Total Google locations: {payload['google_enriched_locations']}")
    if failed:
        raise RuntimeError("Google enrichment incomplete; successful matches were preserved.")


if __name__ == "__main__":
    main()
