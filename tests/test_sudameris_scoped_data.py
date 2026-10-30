import json
import unittest
from pathlib import Path
from promo_backend.normalize import normalize_row
from promo_backend.quality import normalize_terms


class ScopedDataTests(unittest.TestCase):
    def setUp(self):
        self.review=json.loads(Path('data/sudameris_scoped_reviews.json').read_text(encoding='utf-8'))

    def test_checkout_and_refund_stay_separate_with_verified_cap(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Comercio/Promoción']=='Farmacia Ypane']
        self.assertEqual(len(rows),3)
        for row in rows:
            promo=normalize_row('Sudameris',row)
            terms=normalize_terms(promo)
            self.assertEqual(terms['limits'][0]['amount'],800000)
            self.assertNotIn('20%',promo['percentages'])

    def test_same_merchant_in_different_cities_has_distinct_identity(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Comercio/Promoción']=='Farmacia Amaia' and x['row']['Variante']=='base']
        self.assertEqual(len(rows),2)
        self.assertEqual(len({normalize_row('Sudameris',r)['id'] for r in rows}),2)
        for row in rows:self.assertEqual(normalize_terms(normalize_row('Sudameris',row))['limits'][0]['amount'],500000)

    def test_san_alberto_renewal_is_only_the_documented_merchant(self):
        rows=[x['row'] for x in self.review['additions'] if x['row']['Localidad']=='San Alberto']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['Comercio/Promoción'],'MAX SUPERMERCADO')
        self.assertEqual(rows[0]['Día de promoción'],'Último sábado de cada mes')
        terms=normalize_terms(normalize_row('Sudameris',rows[0]))
        self.assertEqual(terms['starts_on'],'2026-08-29')
        self.assertEqual(terms['ends_on'],'2026-12-31')
        self.assertEqual(terms['limits'][0]['amount'],600000)
        self.assertEqual(rows[0]['Cantidad de descuento / beneficio'],'20% de reintegro')

    def test_curuguaty_new_supermarket_starts_october_31_not_today(self):
        row=next(x['row'] for x in self.review['additions'] if x['row']['Comercio/Promoción']=='GREFRAN SUPERMERCADO')
        self.assertEqual(row['URL fuente actual'],'https://www.sudameris.com.py/descargas/documentos/zona-norte-curuguaty')
        terms=normalize_terms(normalize_row('Sudameris',row))
        self.assertEqual(terms['starts_on'],'2026-10-31')
        self.assertEqual(terms['ends_on'],'2026-12-31')
        self.assertEqual(terms['limits'][0]['amount'],500000)
        self.assertIn('Último sábado',row['Día de promoción'])
