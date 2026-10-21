import json
import unittest
from pathlib import Path
from promo_backend.normalize import normalize_row
from promo_backend.quality import normalize_terms


class ScopedDataTests(unittest.TestCase):
    def setUp(self):
        self.review=json.loads(Path('data/sudameris_scoped_reviews.json').read_text(encoding='utf-8'))

    def test_checkout_and_refund_stay_separate_with_verified_cap(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Comercio/Promoción']=='Farmacia Ypane']
        self.assertEqual(len(rows),3)
        for row in rows:
            promo=normalize_row('Sudameris',row)
            terms=normalize_terms(promo)
            self.assertEqual(terms['limits'][0]['amount'],800000)
            self.assertNotIn('20%',promo['percentages'])

    def test_same_merchant_in_different_cities_has_distinct_identity(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Comercio/Promoción']=='Farmacia Amaia' and x['row']['Variante']=='base']
        self.assertEqual(len(rows),2)
        self.assertEqual(len({normalize_row('Sudameris',r)['id'] for r in rows}),2)
        for row in rows:self.assertEqual(normalize_terms(normalize_row('Sudameris',row))['limits'][0]['amount'],500000)

    def test_expired_zone_rows_are_not_renewed(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Localidad']=='San Alberto']
        self.assertEqual(len(rows),6)
        for row in rows:self.assertEqual(normalize_terms(normalize_row('Sudameris',row))['ends_on'],'2025-12-31')
