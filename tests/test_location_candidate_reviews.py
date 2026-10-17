import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scrapers'))
from location_reviews import apply_reviews, fingerprint

class CandidateReviewTests(unittest.TestCase):
    def test_confirmation_is_bound_to_exact_source_and_candidate(self):
        item = {'id': 'one', 'address': 'Street123', 'lat': -25, 'lng': -57, 'google_candidate': {'lat': -25, 'lng': -57}}
        review = {'id': 'one', 'status': 'confirmed', 'reason': 'Address verified', 'reviewed_on': '2026-10-17', 'evidence_sha256': fingerprint(item)}
        apply_reviews([item], {'reviews': [review]})
        self.assertEqual(item['google_confidence'], 'high')
        apply_reviews([item], {'reviews': [review]})
        self.assertEqual(item['google_confidence'], 'high')
        item['address'] = 'Different branch'
        apply_reviews([item], {'reviews': [review]})
        self.assertEqual(item['location_review_status'], 'stale_evidence')
        self.assertEqual(item['google_confidence'], 'review')
        self.assertEqual(item['google_enrichment_status'], 'needs_review')

    def test_rejected_candidate_is_preserved_but_not_confirmed(self):
        item = {'id': 'one', 'lat': -25, 'lng': -57}
        review = {'id': 'one', 'status': 'rejected', 'reason': 'Different city', 'reviewed_on': '2026-10-17', 'evidence_sha256': fingerprint(item)}
        apply_reviews([item], {'reviews': [review]})
        self.assertEqual(item['google_confidence'], 'review')
        self.assertEqual((item['lat'], item['lng']), (-25, -57))

if __name__ == '__main__':
    unittest.main()
