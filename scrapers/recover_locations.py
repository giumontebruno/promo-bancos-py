"""Recover lost branch coordinates without reverting the current source records."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def recover(current, previous):
    old = {item["id"]: item for item in previous["locations"]}
    changed = 0
    for item in current["locations"]:
        candidate = old.pop(item["id"], None)
        if not candidate or item.get("geocode_source") not in {"", "city_approximation"}:
            continue
        if candidate.get("geocode_source") in {"", "city_approximation"}:
            continue
        for field in ("lat", "lng", "place_id", "formatted_address", "google_name", "google_types",
                      "geocode_source", "google_confidence", "google_enrichment_status"):
            if field in candidate:
                item[field] = candidate[field]
        item["location_verified_at"] = candidate.get("location_verified_at", previous.get("locations_updated_at", ""))
        changed += 1
    for item in old.values():
        if item.get("bank") != "BNF":
            current["locations"].append(item)
            changed += 1
    current["total_locations"] = len(current["locations"])
    current["geocoded_locations"] = sum(bool(i.get("geocode_source")) and i.get("geocode_source") != "city_approximation"
                                          for i in current["locations"])
    return changed


if __name__ == "__main__":
    path = ROOT / "public/locations.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    previous = json.loads(subprocess.check_output(["git", "show", "9e67db3:public/locations.json"], cwd=ROOT))
    count = recover(current, previous)
    current["recovered_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recovered {count} location records; dates of verification preserved.")
