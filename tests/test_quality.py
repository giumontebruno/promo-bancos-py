import unittest
from promo_backend.quality import validity_dates, extract_limits, deduplicate, normalize_terms, favorite_aliases
from scrapers.enrich_locations_google import match_score
from scrapers.enrich_locations_google import should_enrich
from promo_backend.normalize import normalize_row


class QualityTests(unittest.TestCase):
    def test_financing_exclusion_does_not_turn_into_refund_benefit(self):
        promo = normalize_row('BNF', {'Cantidad de descuento / beneficio': '12 cuotas sin intereses',
            'Detalle': 'El reintegro no se acumula con compras financiadas.'})
        self.assertEqual(promo['benefit_type'], 'cuotas_sin_intereses')

    def test_online_store_is_not_geocoded(self):
        self.assertFalse(should_enrich({'city': 'Asuncion', 'address': 'App PLUB', 'online_only': True}))

    def test_conflicting_source_amount_has_no_calculator_limits(self):
        terms = normalize_terms({'validity': 'Septiembre 2026', 'raw_detail': 'Tope de reintegro Gs. 600.000',
            'source_warning': 'Importe contradictorio en las bases.'})
        self.assertEqual(terms['limits'], [])
        self.assertIn('source_amount_conflict', terms['issues'])

    def test_bnf_full_validity_overrides_truncated_weekday_label(self):
        promo = {'validity': 'Todos los sábados', 'raw_detail': 'Bases y Condiciones Vigencia: Todos los sábados. Del 01 al 29 de agosto de 2026. Beneficio: 30% de reintegro.'}
        self.assertEqual(normalize_terms(promo)['ends_on'], '2026-08-29')

    def test_renewed_favorite_is_only_migrated_when_unambiguous(self):
        old = {'id': 'old', 'bank': 'Bank', 'merchant_name': 'Store', 'category': 'Food'}
        new = {**old, 'id': 'new'}
        self.assertEqual(favorite_aliases([old], [new]), {'old': 'new'})
        self.assertEqual(favorite_aliases([old], [new, {**new, 'id': 'premium'}]), {})

    def test_dates_do_not_extend_conflicting_validity(self):
        self.assertTrue(validity_dates('Hasta 30 de septiembre de 2026; Hasta 31 de octubre de 2026')['conflicting_dates'])
        self.assertIsNone(validity_dates('Ver bases')['ends_on'])
        self.assertEqual(validity_dates('Septiembre 2026')['ends_on'], '2026-09-30')

    def test_limits_keep_their_label(self):
        limits = extract_limits('Tope de compra Gs. 500.000; Tope de reintegro Gs. 100.000')
        self.assertEqual([(x['kind'], x['amount']) for x in limits], [('purchase', 500000), ('refund', 100000)])
        self.assertEqual(extract_limits('Gs. 500.000 y Gs. 100.000'), [])

    def test_dedup_preserves_different_benefits_and_favorites(self):
        base = {'id': 'a', 'bank': 'Bank', 'merchant_name': 'Store', 'benefit_summary': '20% reintegro', 'validity': 'Septiembre 2026'}
        records, aliases = deduplicate([base, {**base, 'id': 'b'}, {**base, 'benefit_summary': '25% reintegro Black'}])
        self.assertEqual(len(records), 2)
        self.assertEqual(len({x['id'] for x in records}), 2)
        self.assertEqual(aliases, {'b': 'a'})

    def test_chain_name_alone_cannot_locate_a_branch(self):
        item = {'merchant_name': 'Superseis', 'address': 'Molas Lopez y San Martin', 'city': 'Asuncion'}
        other = {'displayName': {'text': 'Superseis'}, 'formattedAddress': 'Republica Argentina y Boggiani, Asuncion', 'location': {'latitude': -25.3, 'longitude': -57.6}}
        self.assertLess(match_score(item, other), 75)
        correct = {**other, 'formattedAddress': 'Molas Lopez y San Martin, Asuncion'}
        self.assertGreaterEqual(match_score(item, correct), 90)


if __name__ == '__main__':
    unittest.main()
