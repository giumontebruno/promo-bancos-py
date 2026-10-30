import csv
import json
import re
import unittest
from pathlib import Path

from scrapers.review_universitaria import review, reviewed_rows


ROOT = Path(__file__).resolve().parents[1]


class UniversitariaReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = json.loads((ROOT / "data/universitaria_live_cards.json").read_text(encoding="utf-8"))
        cls.source = source
        cls.rows, cls.withheld = review(source)
        cls.by_name = {}
        for row in cls.rows:
            cls.by_name.setdefault(row["Comercio/Promoción"], []).append(row)

    def test_every_published_card_has_a_quantified_benefit_and_source(self):
        # The current capture has 52 cards; reconcile each to variants or a
        # documented withheld reason instead of imposing September's count.
        source_pairs = {(r["Comercio/Promoción"], r["Bases y condiciones URL"]) for r in self.source}
        published_pairs = {(r["Comercio/Promoción"], r["Bases y condiciones URL"]) for r in self.rows}
        withheld_pairs = {(r["merchant"], r["source"]) for r in self.withheld}
        self.assertEqual(source_pairs, published_pairs | withheld_pairs)
        self.assertFalse(published_pairs & withheld_pairs)
        self.assertTrue(all(r["reason"] for r in self.withheld))
        self.assertEqual(len(self.rows), sum(len(reviewed_rows(r)[0]) for r in self.source))
        for row in self.rows:
            benefit = row["Cantidad de descuento / beneficio"]
            self.assertRegex(benefit, r"\d{1,3}\s*%|\d{1,2}\s+cuotas")
            self.assertTrue(row["Bases y condiciones URL"].startswith("https://www.universitaria.coop/"))
            self.assertNotEqual(benefit.casefold(), "descuento")

    def test_current_payment_caps_are_read_from_official_document(self):
        for name, purchase, qr, physical in [
            ("BURGER KING", "200.000", "60.000", "20.000"),
            ("POPEYES", "200.000", "60.000", "20.000"),
            ("SUBWAY", "200.000", "60.000", "20.000"),
            ("Estaciones ENERGY", "300.000", "60.000", "30.000"),
        ]:
            rows = self.by_name[name]
            self.assertEqual(len(rows), 2)
            for row, refund in zip(rows, [qr, physical]):
                self.assertIn("compra mensual por cuenta: Gs. " + purchase, row["Montos / topes"])
                self.assertIn("descuento: Gs. " + refund, row["Montos / topes"])
                self.assertIn("No aplica", row["Texto fuente original"])
        source = next(r for r in self.source if r["Comercio/Promoción"] == "BURGER KING")
        changed = dict(source, Detalle="QR 30% tarjeta física 10%; consultar condiciones")
        self.assertEqual(reviewed_rows(changed)[0], [])

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
        # The daily refresh has its own source capture; the 2026-09 fixture above
        # is deliberately fixed and need not equal today's published catalog.
        report = json.loads((ROOT / "outputs/universitaria_review_report.json").read_text(encoding="utf-8"))
        retained=report.get("retained_historical_rows",0)
        self.assertEqual(len(saved), report.get("exported_rows",report["published_variants"]))
        self.assertEqual(len(saved),report["published_variants"]+retained)
        self.assertGreaterEqual(sum(r.get("Estado verificacion")=="unconfirmed" for r in saved),retained)
        self.assertTrue(all(row["Bases y condiciones URL"].startswith("https://www.universitaria.coop/") for row in saved))
        variants = [row["Variante"] for row in saved if row["Variante"]]
        self.assertEqual(len(variants), len(set(variants)))
        self.assertFalse(any(re.search(r"^todos los|^en productos seleccionados$", row["Cantidad de descuento / beneficio"], re.I)
                             for row in saved))


if __name__ == "__main__":
    unittest.main()

class CurrentSupermarketScopeTests(unittest.TestCase):
    def test_october_supermarkets_scoped_by_payment(self):
        from scrapers.review_universitaria import reviewed_rows
        from promo_backend.normalize import normalize_row
        from promo_backend.quality import normalize_terms
        row = {'Comercio/Promoción': 'SUPERSEIS / STOCK / DELIMARKET',
               'Bases y condiciones URL': 'https://www.universitaria.coop/assets_front/img/promos/bases-y-condiciones1790768981.pdf',
               'Detalle': 'PANAL QR, CABAL QR Y MASTERCARD QR 20%. PAGO CON TC FISICA con las 3 marcas 10%. Límite de compra de Gs. 500.000 por cuenta y por mes.',
               'Día de promoción': 'Todos los viernes',
               'Vigencia': 'Desde 2026-10-01 hasta 2026-12-25'}
        rows, reason = reviewed_rows(row)
        self.assertEqual(reason, '')
        self.assertEqual(len(rows), 2)
        for index, r in enumerate(rows):
            self.assertIn('Panal, Cabal y Mastercard', r['Tarjetas verificadas'])
            terms = normalize_terms(normalize_row('Coop. Universitaria', r))
            self.assertIn(('purchase', 500000, 'mensual'), [(x['kind'], x['amount'], x['period']) for x in terms['limits']])
            self.assertIn(('refund', [100000, 50000][index], 'mensual'), [(x['kind'], x['amount'], x['period']) for x in terms['limits']])
            self.assertIn('compartido', r['Detalle'])
        row['Bases y condiciones URL'] = 'https://www.universitaria.coop/changed.pdf'
        self.assertEqual(reviewed_rows(row)[0], [])
