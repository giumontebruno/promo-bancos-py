import json
import unittest
from pathlib import Path
from promo_backend.quality import normalize_terms

class ReviewScopeTests(unittest.TestCase):
    def test_purchase_window_wins_over_balance_maintenance_period(self):
        p={'raw_detail':'Vigencia: Desde 2026-10-12 hasta 2026-10-31. Condiciones: mantener saldo.',
           'validity':'Desde 2026-10-15 hasta 2026-10-15',
           'source_purchase_validity':'Desde 2026-10-15 hasta 2026-10-15'}
        terms=normalize_terms(p)
        self.assertEqual((terms['starts_on'],terms['ends_on']),('2026-10-15','2026-10-15'))

    def test_other_benefit_limit_does_not_leak_into_reviewed_variant(self):
        p={'raw_detail':'Para reintegro: Tope de compra mensual Gs. 1.000.000.',
           'caps_and_minimums':'', 'limits_reviewed_for_variant':True,
           'validity':'Hasta 2026-12-31'}
        self.assertEqual(normalize_terms(p)['limits'],[])
        p['caps_and_minimums']='Tope de compra mensual Gs. 200.000.'
        self.assertEqual(normalize_terms(p)['limits'][0]['amount'],200000)

    def test_separate_merchant_expirations_survive_club_campaign(self):
        reviews=json.loads(Path('data/sudameris_document_reviews.json').read_text(encoding='utf-8'))
        expired=[r for r in reviews if any(n in r['merchant'].lower() for n in ('burguero','asadito aquino','catas nómadas','casita gourmet'))]
        self.assertEqual(len(expired),4)
        self.assertTrue(all(r['end']<'2026-10-16' for r in expired))

    def test_ordinal_promotions_keep_monthly_restrictions(self):
        from promo_backend.normalize import detect_ordinal_weekdays
        for day,ordinal,name in [('Primer viernes de cada mes',1,'viernes'),('Último lunes de cada mes',-1,'lunes')]:
            self.assertIn({'ordinal':ordinal,'day':name},detect_ordinal_weekdays(day))
