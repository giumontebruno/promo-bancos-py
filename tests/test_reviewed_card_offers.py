import unittest
from promo_backend.normalize import REVIEWED_CARD_OFFERS, reviewed_card_offers
from promo_backend.quality import normalize_terms
import hashlib

class ReviewedCardOfferTests(unittest.TestCase):
    def test_source_hash_gate_and_campaign_identity(self):
        for review in REVIEWED_CARD_OFFERS:
            import json
            from pathlib import Path
            rows=json.loads(Path('tests/fixtures/reviewed-card-campaigns.json').read_text(encoding='utf-8'))
            sample=next(r for r in rows if r['source_url']==review['source_url'] and r['merchant_name']==review['merchant_name'])
            raw=sample['raw_detail']
            self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),review['detail_sha256'])
            promo=dict(sample)
            offers=reviewed_card_offers(promo)
            self.assertEqual(len(offers),len(review['offers']))
            self.assertEqual({r['campaign_id'] for r in offers},{sample['id']})
            self.assertEqual(len({r['id'] for r in offers}),len(offers))
            changed={**promo,'raw_detail':raw+' Fuente actualizada.'}
            rejected=reviewed_card_offers(changed)
            self.assertEqual(len(rejected),1)
            self.assertIn('fuente cambió',rejected[0]['source_warning'])
            self.assertEqual(normalize_terms(rejected[0])['status'],'needs_review')

if __name__=='__main__':
    unittest.main()
