import unittest
from promo_backend.quality import extract_limits
class ScopedLimitPeriods(unittest.TestCase):
    def test_monthly_synonyms_with_explicit_currency(self):
        for phrase in ('mensual', 'por mes', 'al mes'):
            self.assertEqual(extract_limits('Tope de compra Gs. 250.000 '+phrase+', por tarjeta')[0]['period'],'mensual')
    def test_monthly_purchase_does_not_make_minimum_monthly(self):
        values=extract_limits('Mínimo de compra Gs. 200.000; tope de compra Gs. 1.000.000 por mes')
        self.assertIsNone(next(x for x in values if x['kind']=='minimum')['period'])
        self.assertEqual(next(x for x in values if x['kind']=='purchase')['period'],'mensual')
    def test_dates_or_once_do_not_imply_recurring_cap(self):
        self.assertIsNone(extract_limits('Tope de reintegro Gs. 50.000 por única vez')[0]['period'])
        self.assertEqual(extract_limits('Vigencia por mes de noviembre de 2026'),[])
    def test_missing_currency_is_not_silently_inferred(self):
        self.assertEqual(extract_limits('Tope de compra 250.000 por mes'),[])
