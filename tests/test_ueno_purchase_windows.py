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
