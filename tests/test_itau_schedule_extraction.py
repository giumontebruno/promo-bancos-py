import unittest
from scrapers.extract_itau import extract_day

class ItauScheduleExtractionTests(unittest.TestCase):
    def test_all_days_in_official_benditta_sentence_are_retained(self):
        self.assertEqual(extract_day('Aplica MIERCOLES, JUEVES Y VIERNES. Tope de compra Gs. 1.000.000.'),
                         'Aplica MIERCOLES, JUEVES Y VIERNES')
    def test_does_not_cross_sentence_or_make_daily(self):
        self.assertEqual(extract_day('Aplica los lunes. Hasta diciembre.'), 'Aplica los lunes')
    def test_range_kept(self):
        self.assertIn('martes a viernes', extract_day('Aplica martes a viernes.'))
