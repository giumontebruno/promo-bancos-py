import json
import unittest
from pathlib import Path
from promo_backend.normalize import normalize_row

class SalaryNormalizationHoldTests(unittest.TestCase):
    def test_old_cached_csv_is_quarantined_without_deleting_rows_or_raw_source(self):
        path=Path(__file__).parent / 'fixtures/ueno-salary-captured-20261030.json'
        affected=[json.loads(path.read_text(encoding='utf-8'))['row']]
        for row in affected:
            result=normalize_row('ueno bank',row)
            self.assertEqual(result['source_verification'],'unconfirmed')
            self.assertIn('personalized_invitation',result['variant_review_reason'])
            self.assertTrue(result['id'])
            self.assertTrue(result['raw_detail'])
            self.assertIn('Campana-Tu-sueldo',result['source_url'])
