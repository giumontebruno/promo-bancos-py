"""Apply only evidence-bound human-reviewed location candidates."""
import hashlib
import json

def fingerprint(item):
    fields = {key: item.get(key) for key in ('id', 'merchant_name', 'address', 'city', 'source_url', 'lat', 'lng', 'google_candidate_place_id', 'google_candidate')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def apply_reviews(locations, payload):
    reviews = {row['id']: row for row in payload.get('reviews', [])}
    for item in locations:
        review = reviews.get(item['id'])
        if not review:
            continue
        matches = fingerprint(item) == review['evidence_sha256']
        item['location_review_status'] = review['status'] if matches else 'stale_evidence'
        item['location_review_reason'] = review['reason'] if matches else 'Source or candidate changed; review required again.'
        item['location_reviewed_on'] = review['reviewed_on']
        if matches and review['status'] == 'confirmed':
            item['google_confidence'] = 'high'
            item['google_enrichment_status'] = 'reviewed_verified'
        else:
            item['google_confidence'] = 'review'
            item['google_enrichment_status'] = 'needs_review'
    return locations
