import json
import unittest
from pathlib import Path
from scrapers.build_gnb_reviewed import build_additional
from promo_backend.normalize import normalize_row

ROOT = Path(__file__).resolve().parents[1]

class FarmacenterNovember(unittest.TestCase):
    def test_pdf_validity_and_sequential_discounts(self):
        campaign = next(c for c in json.loads((ROOT / 'data/gnb_additional_reviewed.json').read_text())['campaigns'] if c.get('merchant') == 'Farmacenter')
        self.assertEqual(campaign['starts_on'], '2026-11-02')
        self.assertEqual(campaign['ends_on'], '2026-12-28')
        self.assertEqual(campaign['source_version'], 'V1 - 30/10/2026')
        self.assertEqual(len(campaign['pdf_sha256']), 64)
        rows = [normalize_row('GNB', row) for row in build_additional({'campaigns': [campaign]})]
        self.assertEqual(len(rows), 5)
        for row, bank_rate, cash_rate in zip(rows, [15,10,15,10], [20,20,15,15]):
            self.assertEqual(row['effective_percent'], bank_rate)
            self.assertTrue(row['benefit_summary'].startswith(f'{bank_rate}% de reintegro sobre el importe final facturado'))
            self.assertIn(f'{cash_rate}% de descuento en caja',row['benefit_summary'])
            self.assertIn('Los porcentajes no se suman',row['raw_detail'])
            self.assertIn('ingresá el importe final facturado',row['raw_detail'])
            self.assertIn('titular y adicionales',row['raw_detail'])
            self.assertIn('POS Bancard',row['raw_detail'])
            self.assertEqual(row['promotion_days'], ['lunes'])
        self.assertEqual(len(rows[4]['promotion_days']),7)
        self.assertNotIn('effective_percent',rows[4])
