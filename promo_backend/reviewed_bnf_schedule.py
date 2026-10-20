"""Apply the narrowly reviewed PDF schedule after IDs have been assigned.

The BNF API's fallback "Todos los días" conflicts with the PDF validity.
Applying after deduplication preserves both existing benefit IDs.
"""
import hashlib


def apply_review(promotions, review):
    hashes = {r["id"]: r["raw_detail_sha256"] for r in review["reviews"]}
    for promo in promotions:
        if promo.get("id") not in hashes or promo.get("bank") != "BNF":
            continue
        if promo.get("source_url") != review["document_url"]:
            continue
        if hashlib.sha256(promo.get("raw_detail", "").encode()).hexdigest() != hashes[promo["id"]]:
            promo["source_verification"] = "unconfirmed"
            promo["source_warning"] = "Las bases cambiaron desde la revisión de días; confirmar con BNF."
            continue
        promo["promotion_days"] = ["lunes"]
        promo["day_text"] = "Lunes"
        promo["source_reviewed_at"] = review["reviewed_on"]
