import csv
import json
import re
import unittest
from pathlib import Path

from scrapers.review_universitaria import review


ROOT = Path(__file__).resolve().parents[1]


class UniversitariaReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = json.loads((ROOT / "data/universitaria_live_cards.json").read_text(encoding="utf-8"))
        cls.rows, cls.withheld = review(source)
        cls.by_name = {}
        for row in cls.rows:
            cls.by_name.setdefault(row["Comercio/Promoción"], []).append(row)

    def test_every_published_card_has_a_quantified_benefit_and_source(self):
        self.assertGreaterEqual(len(self.rows), 80)
        self.assertEqual({item["merchant"] for item in self.withheld}, {"AFS", "La Ponde S.A."})
        for row in self.rows:
            benefit = row["Cantidad de descuento / beneficio"]
            self.assertRegex(benefit, r"\d{1,3}\s*%|\d{1,2}\s+cuotas")
            self.assertTrue(row["Bases y condiciones URL"].startswith("https://www.universitaria.coop/"))
            self.assertNotEqual(benefit.casefold(), "descuento")

    def test_current_pharmacy_payment_and_product_variants(self):
        pharmacy = self.by_name["Farmacia Catedral"]
        self.assertEqual([row["Cantidad de descuento / beneficio"] for row in pharmacy], [
            "Hasta 50% de descuento con QR en productos seleccionados",
            "35% de descuento con QR en medicamentos seleccionados",
            "30% de descuento con QR en medicamentos y productos varios",
            "25% de descuento con tarjeta física en medicamentos y productos varios",
        ])
        self.assertTrue(all(row["Día de promoción"].casefold().endswith("viernes") for row in pharmacy))
        self.assertTrue(all("Gs. 3.000.000" in row["Montos / topes"] for row in pharmacy))

    def test_monthly_university_and_daily_financing_are_not_misdated(self):
        catholic = self.by_name["UNIVERSIDAD CATÓLICA"]
        self.assertEqual({row["Día de promoción"] for row in catholic}, {"del 1 al 5 de cada mes"})
        self.assertTrue(all("20%" not in row["Cantidad de descuento / beneficio"] for row in catholic))
        cellshop = self.by_name["Cellshop Importados Paraguay"]
        self.assertEqual(len(cellshop), 1)
        self.assertEqual(cellshop[0]["Cantidad de descuento / beneficio"], "Hasta 10 cuotas sin intereses")
        self.assertEqual({row["Día de promoción"] for row in self.by_name["Todo Cubierta"]},
                         {"Lunes, martes y jueves", "Miércoles y viernes", "Todos los días"})

    def test_saved_output_matches_review_and_has_distinct_variants(self):
        with (ROOT / "outputs/universitaria_beneficios_por_categoria.csv").open(encoding="utf-8-sig", newline="") as handle:
            saved = list(csv.DictReader(handle))
        self.assertEqual(len(saved), len(self.rows))
        variants = [row["Variante"] for row in saved if row["Variante"]]
        self.assertEqual(len(variants), len(set(variants)))
        self.assertFalse(any(re.search(r"^todos los|^en productos seleccionados$", row["Cantidad de descuento / beneficio"], re.I)
                             for row in saved))


if __name__ == "__main__":
    unittest.main()
