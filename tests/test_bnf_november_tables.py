import json
import unittest
from pathlib import Path
from scrapers.extract_bnf import benefit_rows
from promo_backend.normalize import normalize_row
from promo_backend.quality import deduplicate

class BnfNovemberTablesTests(unittest.TestCase):
    fixtures=json.loads((Path(__file__).parent/'fixtures/bnf-november-tables.json').read_text())
    def fixture(self,category):
        return next(x for x in self.fixtures if category in x['url'])
    def parse(self,category,text=None):
        f=self.fixture(category)
        return benefit_rows({'categoria':category,'dia':'Todos los días','pdf':f['url']},text or f['text'],[{'merchant_name':'Comercio fixture'}])
    def test_supermarket_card_tiers_dates_caps_and_exclusions(self):
        rows=self.parse('Supermercados')
        self.assertEqual(len(rows),2)
        self.assertEqual([r['Cantidad de descuento / beneficio'] for r in rows],['20% reintegro','30% reintegro'])
        norm=deduplicate([normalize_row('BNF',r) for r in rows])[0]
        self.assertEqual([r['terms']['ends_on'] for r in norm],['2026-11-26']*2)
        self.assertEqual([r['terms']['starts_on'] for r in norm],['2026-11-05']*2)
        self.assertEqual([r['promotion_days'] for r in norm],[['jueves']]*2)
        self.assertEqual([{x['kind']:x['amount'] for x in r['terms']['limits']} for r in norm],[{'purchase':1000000,'refund':200000},{'purchase':1500000,'refund':450000}])
        for row in rows:
            self.assertIn('por cuenta',row['Detalle']);self.assertIn('adicionales',row['Detalle'])
            self.assertIn('POS de Bancard',row['Detalle']);self.assertIn('financiadas',row['Detalle']);self.assertIn('Dinelco',row['Detalle'])
    def test_all_five_documents_and_pharmacy_day_from_pdf(self):
        self.assertEqual(len(self.fixtures),5)
        for category in ['Farmacias','Estaciones','Supermercados','Frigorificos','Mayoristas']:
            self.assertTrue(self.parse(category))
        self.assertEqual(self.parse('Farmacias')[0]['Día de promoción'],'Lunes')
    def test_missing_and_contradictory_tables_fail_closed(self):
        text=self.fixture('Supermercados')['text']
        for altered in [text.replace('Gs. 450.000','Gs. 500.000'),text.replace('Visa Clásica BNF','Visa Otra BNF'),text.replace('05, 12, 19, 26','05, 19, 26')]:
            with self.assertRaises(ValueError):self.parse('Supermercados',altered)
