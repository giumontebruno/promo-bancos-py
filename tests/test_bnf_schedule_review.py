import copy
import hashlib
import unittest
from promo_backend.reviewed_bnf_schedule import apply_review


class BnfScheduleReviewTests(unittest.TestCase):
    def setUp(self):
        self.p = {"id": "base-finance", "bank": "BNF", "source_url": "https://www.bnf.gov.py/terms.pdf", "raw_detail": "Reviewed Monday PDF", "promotion_days": ["lunes", "martes"], "day_text": "Todos los días", "benefit_summary": "12 cuotas", "terms": {"ends_on": "2026-10-26"}}
        self.review = {"document_url": self.p["source_url"], "reviewed_on": "2026-10-20", "reviews": [{"id": self.p["id"], "raw_detail_sha256": hashlib.sha256(self.p["raw_detail"].encode()).hexdigest()}]}

    def test_review_corrects_days_preserving_identity_and_other_terms(self):
        before = copy.deepcopy(self.p)
        apply_review([self.p], self.review)
        self.assertEqual(self.p["promotion_days"], ["lunes"])
        self.assertEqual(self.p["day_text"], "Lunes")
        for key in ("id", "source_url", "terms", "benefit_summary", "raw_detail"):
            self.assertEqual(self.p[key], before[key])

    def test_changed_source_requires_reverification(self):
        self.p["raw_detail"] += " changed"
        apply_review([self.p], self.review)
        self.assertEqual(self.p["source_verification"], "unconfirmed")
        self.assertEqual(self.p["day_text"], "Todos los días")

    def test_other_bank_or_document_is_untouched(self):
        for field in ("bank", "source_url", "id"):
            p = dict(self.p, **{field: "other"})
            before = copy.deepcopy(p)
            apply_review([p], self.review)
            self.assertEqual(p, before)
