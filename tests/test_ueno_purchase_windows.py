import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))
from extract_ueno_tables import purchase_window

class UenoPurchaseWindowTests(unittest.TestCase):
    def test_balance_period_is_not_purchase_period(self):
        value = "Vigencia: Desde el 12 de octubre de 2026 hasta el 31 de octubre de 2026. Mantener saldo. El beneficio será aplicable exclusivamente a las compras efectuadas el día 15 de octubre de 2026, en el horario de 12:00 a 14:00 hs."
        window = purchase_window(value)
        self.assertEqual(window["validity"], "Desde 2026-10-15 hasta 2026-10-15")
        self.assertIn("12:00 a 14:00", window["day"])

    def test_future_purchase_date_with_current_deposit_date(self):
        value = "Depositar 16 de octubre 2026. 50% en compras realizadas con tarjeta de crédito y/o débito MasterCard emitidas por ueno bank exclusivamente el 18 de octubre 2026 de 14:00 h hasta 16:00 h."
        window = purchase_window(value)
        self.assertEqual(window["validity"], "Desde 2026-10-18 hasta 2026-10-18")
        self.assertIn("14:00 a 16:00", window["day"])

    def test_balance_dates_alone_never_override(self):
        self.assertIsNone(purchase_window("Mantener saldo exclusivamente el 18 de octubre 2026 hasta 16:00 h"))

    def test_conflicting_purchase_dates_are_not_arbitrarily_selected(self):
        self.assertIsNone(purchase_window("exclusivamente a las compras efectuadas el día 15 de octubre de 2026. exclusivamente a las compras efectuadas el día 18 de octubre de 2026."))

class UenoSalarySafetyTests(unittest.TestCase):
    # Official landing /beneficio-byc/oct2026/reintegro50-dom1/ links v2.
    # Same purchase-window text is retained in the 2026-10-30 v3 source capture.
    DETAIL = ('Campaña “Tu sueldo está llegando y tu 50% también” '
              'Exclusivamente desde el 28 de octubre de 2026 hasta el 31 de octubre de 2026 '
              'a las 23:59 h para transferir o depositar el saldo extra requerido. ● '
              'El beneficio de reintegro aplicará de forma única el 01 de noviembre de 2026, '
              'entre las 14:00 y las 17:00 horas. ● '
              '50% de reintegro sobre las compras efectuadas el 01 de noviembre de 2026 '
              'entre las 14:00 y las 17:00 horas. ● '
              'Por ejemplo Nivel 5 con 40% se complementará hasta alcanzar el 50%.')
    URL = ('https://www.ueno.com.py/wp-content/uploads/2026/10/'
           'Campana-Tu-sueldo-esta-llegando-y-tu-50-tambien-_-OCT-2026v3.pdf')

    def test_deposit_days_are_not_purchase_days(self):
        window = purchase_window(self.DETAIL)
        self.assertEqual(window['validity'], 'Desde 2026-11-01 hasta 2026-11-01')
        self.assertIn('14:00 a 17:00', window['day'])
        self.assertNotIn('2026-10-30', window['validity'])

    def test_example_percentage_is_not_an_offer(self):
        from extract_ueno_tables import benefit_labels
        labels = benefit_labels(self.DETAIL)
        self.assertEqual(len(labels), 1)
        self.assertIn('50%', labels[0])
        self.assertNotIn('40%', labels[0])

    def test_not_published_even_on_purchase_day_without_supported_eligibility(self):
        from extract_ueno_tables import publication_hold
        for context in ['30 Oct', '1 Nov 13:59', '1 Nov 14:00 no invitation', '1 Nov 17:01']:
            with self.subTest(context=context):
                hold = publication_hold(self.URL, self.DETAIL)
                self.assertFalse(hold['publication_allowed'])
                self.assertIn('official_notification', hold['required_review'])
                self.assertIn('personalized_cap', hold['required_review'])

    def test_revision_change_does_not_bypass_review(self):
        from extract_ueno_tables import publication_hold
        self.assertIsNotNone(publication_hold(self.URL.replace('v3.pdf', 'v4.pdf'), 'changed terms'))
        self.assertIsNone(publication_hold('https://www.ueno.com.py/other.pdf', self.DETAIL))

    def test_offline_hold_preserves_source_identity_and_history(self):
        from extract_ueno_tables import apply_publication_hold
        row = {"Bases PDF URL": self.URL, "Detalle": self.DETAIL,
               "Comercio/Promoción": "360 Sneaker Store", "Vigencia": "old raw validity"}
        held = apply_publication_hold(row)
        for key, value in row.items():
            self.assertEqual(held[key], value)
        self.assertEqual(held["Estado verificacion"], "unconfirmed")
        self.assertNotIn("Estado verificacion", row)
