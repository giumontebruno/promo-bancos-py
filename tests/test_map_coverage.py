import importlib.util
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('map_audit', Path(__file__).resolve().parents[1] / 'scripts/audit_map_coverage.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MapCoverageTests(unittest.TestCase):
    def test_coordinates_reject_invalid_boolean_and_nonfinite(self):
        for lat, lng in [(None, -57), (True, -57), (math.nan, -57), (-25, math.inf), (91, -57), (-25, 181)]:
            self.assertFalse(module.valid_coordinates({'lat': lat, 'lng': lng}))
        self.assertTrue(module.valid_coordinates({'lat': -25.3, 'lng': -57.6}))

    def test_unreviewed_and_online_never_count_as_eligible(self):
        point = {'lat': -25.3, 'lng': -57.6, 'geocode_source': 'official'}
        self.assertEqual(module.exclusion(point), 'eligible_coordinates')
        for change, expected in [({'online_only': True}, 'online_only'), ({'google_enrichment_status': 'needs_review'}, 'requires_review'), ({'geocode_source': 'city_approximation'}, 'unverified_or_approximate')]:
            self.assertEqual(module.exclusion(dict(point, **change)), expected)

    def test_shared_coordinates_do_not_mean_duplicate_branch(self):
        point = {'lat': -25, 'lng': -57, 'geocode_source': 'official', 'bank': 'BNF', 'address': 'Mall', 'city': 'Asuncion'}
        report = module.audit({'locations': [dict(point, id='a', merchant_name='Store A'), dict(point, id='b', merchant_name='Store B')]})
        self.assertEqual(report['duplicate_branch_groups'], {})
        self.assertEqual(len(report['shared_coordinate_groups']), 1)
        self.assertEqual(report['status_counts']['eligible_coordinates'], 2)

    def test_generic_mall_is_quarantined(self):
        self.assertEqual(module.exclusion({'lat': -25, 'lng': -57, 'geocode_source': 'google_places_text_search', 'merchant_name': 'Farmacias', 'google_name': 'Shopping del Sol', 'google_types': ['shopping_mall']}), 'generic_merchant_matched_to_mall')

if __name__ == '__main__':
    unittest.main()
