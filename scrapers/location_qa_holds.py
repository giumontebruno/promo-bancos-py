"""Persistent human QA decisions; automatic candidates cannot release a hold."""
import copy
import json
from functools import lru_cache
from pathlib import Path

HOLD_PATH = Path(__file__).resolve().parents[1] / "data/location_qa_holds.json"
IDENTITY_FIELDS = ("bank", "merchant_name", "address", "city", "source_url")

@lru_cache(maxsize=4)
def _load_registry(path, modified, size):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_held(row):
    apply_holds([row])
    return bool(row.get("qa_hold"))


def apply_holds(locations, payload=None):
    if payload is None:
        stamp = HOLD_PATH.stat()  # Missing decisions must stop the pipeline.
        payload = _load_registry(str(HOLD_PATH), stamp.st_mtime_ns, stamp.st_size)
    reviews = payload["holds"]
    ids = [r["id"] for r in reviews]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate QA hold IDs")
    by_id = {r["id"]: r for r in reviews}
    for row in locations:
        hold = by_id.get(row.get("id"))
        if not hold:
            continue
        if hold.get("decision") not in ("hold", "released"):
            raise ValueError("QA decision must be hold or released")
        if hold["decision"] == "released":
            # Release itself is not a coordinate approval. A separate reviewed
            # source must establish the accepted point.
            if not hold.get("release_evidence"):
                raise ValueError("QA release requires evidence")
            row.pop("qa_hold", None)
            row.pop("qa_hold_detail", None)
            if row.get("location_review_status") != "confirmed":
                row["needs_review"] = True
            continue
        if not hold.get("reason") or not hold.get("evidence"):
            raise ValueError("QA hold requires reason and evidence")
        # Preserve all coordinates, IDs, navigation metadata and candidate
        # evidence. Suppression is explicit rather than deleting the point.
        row["qa_hold"] = True
        row["qa_hold_detail"] = {
            "reason": hold["reason"],
            "evidence": copy.deepcopy(hold["evidence"]),
            "reviewed_on": hold.get("reviewed_on"),
            "identity_changed": any(row.get(k) != hold["identity"].get(k) for k in IDENTITY_FIELDS),
        }
        row["needs_review"] = True
        row["location_review_status"] = "qa_hold"
    return locations
