import csv
import unittest
from pathlib import Path
from promo_backend.normalize import normalize_row

class SalaryNormalizationHoldTests(unittest.TestCase):
    def test_old_cached_csv_is_quarantined_without_deleting_rows_or_raw_source(self):
        path=Path('outputs/ueno_beneficios_por_categoria.csv')
        with path.open(encoding='utf-8-sig') as source:
            rows=list(csv.DictReader(source))
        affected=[row for row in rows if 'Campana-Tu-sueldo-esta-llegando-y-tu-50-tambien' in str(row)]
        self.assertGreater(len(affected),0)
        for row in affected:
            result=normalize_row('ueno bank',row)
            self.assertEqual(result['source_verification'],'unconfirmed')
            self.assertIn('personalized_invitation',result['variant_review_reason'])
            self.assertTrue(result['id'])
            self.assertTrue(result['raw_detail'])
            self.assertIn('Campana-Tu-sueldo',result['source_url'])
