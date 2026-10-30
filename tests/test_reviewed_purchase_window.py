import unittest
from promo_backend.quality import normalize_terms

class ReviewedPurchaseWindowTests(unittest.TestCase):
    def test_reviewed_purchase_window_can_follow_funding_filename_month(self):
        result = normalize_terms({'source_purchase_validity': 'Desde 2026-11-01 hasta 2026-11-01', 'source_period_end': '2026-10-31'})
        self.assertEqual(result['starts_on'], '2026-11-01')
        self.assertEqual(result['ends_on'], '2026-11-01')
