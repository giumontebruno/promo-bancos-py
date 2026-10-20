"""Coordinate reviews bind operator evidence to exact bank branch identities."""
def apply_reviews(locations, reviews):
    by_id = {r["id"]: r for r in reviews}
    for row in locations:
        review = by_id.get(row.get("id"))
        if not review or any(row.get(k) != review[k] for k in ("bank", "merchant_name", "address", "city", "source_url")):
            continue
        for key, value in review.items():
            row[key] = value
        row["geocode_source"] = "official_farmacenter_locator"
        row["needs_review"] = False
        row["location_review_status"] = "confirmed"
