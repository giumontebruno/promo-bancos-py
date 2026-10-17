import unittest
from scrapers.extract_continental import scoped_segments


class ContinentalScopeTests(unittest.TestCase):
    def test_cards_do_not_inherit_later_expiry(self):
        text = ('Los sábados y domingos, en Comercio. - 35% de reintegro con Privilege. '
                'Límite de compra de Gs. 2.000.000. - 25% de reintegro con Black. '
                'Vigente hasta el 24 de octubre de 2026. Además: - 20% de reintegro con Oro. '
                'Exclusivo en POS Dinelco. Vigente hasta el 10 de julio de 2027. '
                'No aplica para pagos online.')
        scopes = scoped_segments(text)
        self.assertEqual(len(scopes), 3)
        self.assertIn('2026', scopes[0][1])
        self.assertNotIn('2027', scopes[0][0])
        self.assertNotIn('Black', scopes[0][0])
        self.assertNotIn('Exclusivo en POS Dinelco', scopes[0][0])
        self.assertIn('domingos', scopes[2][2])
        self.assertIn('No aplica para pagos online', scopes[0][0])

    def test_expired_discount_does_not_inherit_financing(self):
        scopes = scoped_segments('Todos los días. - 15% en caja. Vigente hasta el 30 de abril del 2026 '
            'Todos los días. - Hasta 12 cuotas sin intereses. Vigente hasta el 31 de diciembre del 2026 (*) No participan prepagas.')
        self.assertEqual(len(scopes), 2)
        self.assertNotIn('cuotas', scopes[0][0])
        self.assertNotIn('15%', scopes[1][0])
        self.assertIn('abril', scopes[0][1])

    def test_caps_and_locales_are_not_cross_assigned(self):
        scopes = scoped_segments('Los sábados. - 20% de reintegro con Oro. Vigente hasta el 18 octubre del 2026. '
            '- 35% de reintegro con Privilege. Vigente hasta el 24 de octubre de 2026. '
            'Límites de compras: - Reintegros del 20% con límite de compra de Gs. 500.000. '
            '- Reintegros del 35% con límite de compra de Gs. 2.000.000. Locales adheridos: Centro. Las promociones aplican presencialmente.')
        self.assertEqual(len(scopes), 2)
        self.assertNotIn('2.000.000', scopes[0][0])
        self.assertNotIn('500.000', scopes[1][0])
        self.assertTrue(all('Locales adheridos: Centro' in s[0] for s in scopes))

    def test_financing_uses_own_days(self):
        scopes = scoped_segments('Los sábados. - 25% de reintegro. Vigente hasta el 16 de enero de 2027. '
            'Además, todos los días: - Hasta 6 cuotas sin intereses. Vigente hasta el 13 de octubre de 2027.')
        self.assertIn('todos los días', scopes[1][2])
        self.assertNotIn('sábados', scopes[1][2])

    def test_short_interval_has_explicit_year(self):
        scopes = scoped_segments('Del 29 al 31 de octubre, en Koala. - 10% de reintegro. Vigente hasta el 31 de octubre de 2026. '
            'Además todos los días: - Hasta 12 cuotas sin intereses. Vigente hasta el 31 de agosto de 2027.')
        self.assertEqual(scopes[0][1], 'Desde el 29 de octubre de 2026 hasta el 31 de octubre de 2026')

    def test_unmixed_row_is_unchanged(self):
        self.assertEqual(scoped_segments('20% de reintegro. Vigente hasta el 31 de diciembre de 2026.'), [])
