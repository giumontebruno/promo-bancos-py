import unittest
from scrapers.extract_atlas import normalized_validity
from scrapers.extract_bnf import benefit_rows
from promo_backend.quality import validity_dates

class AtlasDates(unittest.TestCase):
    def test_explicit_forms(self):
        for text,start,end in [
            ('Vigente todos los días del 01/06 al 31/12 del 2026.', '2026-06-01','2026-12-31'),
            ('Vigente todos los últimos jueves hasta el 31/12 del 2026.',None,'2026-12-31'),
            ('Vigente el 30 y 31 de octubre de 2026.', '2026-10-30','2026-10-31'),
            ('Promoválida el día 23 de octubre del 2026.', '2026-10-23','2026-10-23'),
            ('Vigente el 17 de octubre de 2026.', '2026-10-17','2026-10-17'),
            ('Promo válida el 21/10/2026 en tiendas adheridas.', '2026-10-21','2026-10-21')]:
            with self.subTest(text=text):
                result=validity_dates(normalized_validity(text))
                self.assertEqual((result['starts_on'],result['ends_on']),(start,end))
    def test_no_inferred_year_or_gap(self):
        for text in ['Vigente hasta el 31 de diciembre.', 'Vigente el 10 y 30 de octubre de 2026.', 'Vigente el 32 de octubre de 2026.']:
            self.assertEqual(normalized_validity(text),text)

class BnfScopes(unittest.TestCase):
    def test_shared_account_scope_preserved(self):
        text='Vigencia: Todos los viernes hasta el 31 de diciembre de 2099. Beneficio: 30% de reintegro con tarjetas Visa Oro y Platinum BNF. Condiciones: • Tope de compra mensual por cuenta de tarjeta de crédito (incluye titular y adicionales) Gs. 1.000.000, el cual aplica al conjunto de salones adheridos al Rubro: Frigoríficos. • Tope de reintegro máximo mensual Gs. 300.000, el cual aplica al conjunto de locales adheridos. Exclusiones: No aplica débito.'
        row=benefit_rows({'categoria':'Frigoríficos','dia':'Viernes','pdf':'https://example.org/terms.pdf'},text,[{'merchant_name':'Comercio'}])[0]
        self.assertIn('incluye titular y adicionales',row['Detalle'])
        self.assertIn('al conjunto de salones adheridos al Rubro: Frigoríficos',row['Detalle'])
        self.assertIn('al conjunto de locales adheridos',row['Montos / topes'])

class ItauDiscovery(unittest.TestCase):
    def test_includes_card_and_regional_categories(self):
        from bs4 import BeautifulSoup
        from scrapers.extract_itau import discover_categories
        soup=BeautifulSoup('<a href="/beneficios2/categoria/22">Mastercard Debit</a><a href="/beneficios2/categoria/60">Neuland</a><a href="/beneficios2/categoria/22">Repeated</a>', 'html.parser')
        self.assertEqual([c['id'] for c in discover_categories(soup)],['22','60'])
    def test_empty_discovery_fails(self):
        from bs4 import BeautifulSoup
        from scrapers.extract_itau import discover_categories
        with self.assertRaises(ValueError): discover_categories(BeautifulSoup('<h1>Unavailable</h1>', 'html.parser'))

if __name__=='__main__': unittest.main()
