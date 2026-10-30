import unittest
from scrapers.extract_bnf import benefit_rows
from promo_backend.quality import validity_dates

class BnfExpiredSourceTests(unittest.TestCase):
    def test_expired_document_is_historical_not_renewed(self):
        rows = benefit_rows({'categoria':'Farmacias','dia':'Lunes','pdf':'https://www.bnf.gov.py/example.pdf'},
            'Vigencia: Todos los lunes. Del 05 al 26 de octubre de 2026. Beneficio: 10% de reintegro con Visa Clásica, Oro y Platinum BNF. Condiciones: Tope de compra: Gs. 1.000.000. Exclusiones: No débito.',
            [{'merchant_name':'Farmacia'}])
        self.assertEqual(len(rows),1)
        self.assertEqual(validity_dates(rows[0]['Vigencia'])['ends_on'],'2026-10-26')
        self.assertIn('1.000.000',rows[0]['Montos / topes'])
        self.assertIn('Visa Clásica, Oro y Platinum',rows[0]['Tarjetas verificadas'])
    def test_unknown_validity_still_fails(self):
        with self.assertRaisesRegex(ValueError,'unknown validity'):
            benefit_rows({'categoria':'Farmacias'},'Vigencia: Consultar. Beneficio: 10% de reintegro.',[])
