import unittest
from promo_backend.normalize import normalize_row
from promo_backend.quality import validity_dates


class SourceBenefitTests(unittest.TestCase):
    def test_weekday_caption_recovers_explicit_refund(self):
        p = normalize_row('Coop. Universitaria', {'Comercio':'Metro', 'Beneficio':'Todos los Martes', 'Detalle':'Descuento del 20%: Gs. 200.000. Reintegro en extracto.'})
        self.assertEqual(p['percentages'], ['20%'])
        self.assertEqual(p['benefit_type'], 'reintegro')

    def test_financing_is_not_refund_from_exclusion_boilerplate(self):
        p = normalize_row('Continental', {'Comercio':'Argor', 'Beneficio':'Ver descripción', 'Detalle':'12 cuotas sin intereses. Reintegros y cuotas no válidos con débito.'})
        self.assertEqual(p['benefit_type'], 'cuotas_sin_intereses')
        self.assertEqual(p['benefit_summary'], '12 cuotas sin intereses')

    def test_setiembre_is_september(self):
        self.assertEqual(validity_dates('Desde el 07 de julio de 2026 hasta el 29 de setiembre de 2026')['ends_on'], '2026-09-29')

    def test_catalog_has_no_bare_refund_or_campaign_as_store(self):
        import json
        from pathlib import Path
        promos = json.loads(Path('public/promotions.json').read_text(encoding='utf8'))
        for p in promos:
            if p['benefit_type'] == 'reintegro':
                self.assertTrue(p['percentages'], p['merchant_name'])
            if p['bank'] == 'Sudameris':
                self.assertNotIn(p['merchant_name'], ['GASTRONOMÍA 26', 'ZONA ESTE', 'ZONA SUR'])
        kaiseki = next(p for p in promos if p['merchant_name'] == 'KAISEKI')
        self.assertEqual(kaiseki['terms']['ends_on'], '2026-10-02')
        self.assertIn('martes', kaiseki['promotion_days'])
