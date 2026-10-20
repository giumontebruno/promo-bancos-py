"""Coordinate reviews bind operator evidence to exact bank branch identities."""
def apply_reviews(locations, reviews):
    by_id = {r["id"]: r for r in reviews}
    for row in locations:
        review = by_id.get(row.get("id"))
        if not review or any(row.get(k) != review[k] for k in ("bank", "merchant_name", "address", "city", "source_url")):
            continue
        # Operator coordinates replace an earlier Google candidate. Keep its
        # evidence in the review manifest, never its navigation ID or flags.
        for field in ("place_id", "formatted_address", "google_name", "google_types",
                      "google_confidence", "google_enrichment_status",
                      "google_last_attempt_at", "google_candidate_place_id", "google_candidate"):
            row.pop(field, None)
        for key, value in review.items():
            row[key] = value
        row["geocode_source"] = review.get("geocode_source", "official_farmacenter_locator")
        row["needs_review"] = False
        row["location_review_status"] = "confirmed"
