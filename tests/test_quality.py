import unittest
from promo_backend.quality import validity_dates, extract_limits, deduplicate
from scrapers.enrich_locations_google import match_score


class QualityTests(unittest.TestCase):
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
