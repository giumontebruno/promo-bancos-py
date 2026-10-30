import json
import unittest
from datetime import date
from pathlib import Path
from scrapers.extract_basa import parse as basa
from scrapers.extract_interfisa import parse as interfisa
from scrapers.new_bank_documents import discover, official_url, numeric_dates

FIXTURES = Path(__file__).parent / 'fixtures' / 'basa_interfisa'
SOURCES = json.loads((FIXTURES / 'sources.json').read_text())['documents']


def fixture(stem):
    item = next(x for x in SOURCES if x['fixture'] == stem + '.txt')
    return item, (FIXTURES / item['fixture']).read_text()


class BankDocumentTests(unittest.TestCase):
    def test_basa_single_scope(self):
        rows, state = basa(*fixture('basa4'), date(2026, 10, 30))
        self.assertTrue(state.startswith('published'))
        self.assertEqual(rows[0]['Cantidad de descuento / beneficio'], '20% de reintegro')
        self.assertIn('tope de compra Gs. 200.000', rows[0]['Montos / topes'])
        self.assertNotIn('tope de reintegro', rows[0]['Montos / topes'])
        self.assertIn('Afinidad Club Libertad', rows[0]['Tarjetas verificadas'])
        self.assertEqual(rows[0]['Vigencia'], 'Hasta 2026-12-31')

    def test_basa_reviewed_multitier_keeps_scope(self):
        rows, state = basa(*fixture('basa3'), date(2026, 10, 30))
        self.assertTrue(state.startswith('published'))
        self.assertEqual(len(rows), 16)
        self.assertIn('1.500.000', rows[0]['Montos / topes'])
        self.assertIn('2.000.000', rows[1]['Montos / topes'])
        self.assertNotIn('Casa Paraná', [r['Comercio/Promoción'] for r in rows])
        rosarina = [r for r in rows if r['Comercio/Promoción'] == 'La Rosarina']
        self.assertTrue(all('2026-09-10' in r['Vigencia'] for r in rosarina))

    def test_review_invalidated_when_pdf_changes(self):
        item, text = fixture('basa3')
        rows, state = basa({**item, 'sha256': 'changed'}, text, date(2026, 10, 30))
        self.assertEqual(rows, [])
        self.assertIn('changed', state)

    def test_refund_tiers_keep_independent_caps(self):
        rows, state = interfisa(*fixture('interfisa1'), date(2026, 10, 30))
        self.assertTrue(state.startswith('published'))
        self.assertEqual(len(rows), 2)
        self.assertIn('1.250.000', rows[0]['Montos / topes'])
        self.assertNotIn('1.500.000', rows[0]['Detalle'])
        self.assertIn('1.500.000', rows[1]['Montos / topes'])
        self.assertEqual(rows[0]['Tarjetas verificadas'], 'Classic, Gold')
        self.assertIn('adicionales', rows[0]['Montos / topes'])
        self.assertIn('CERRO CORA 9005', rows[0]['Locales'])

    def test_single_future_day_and_financing(self):
        rows, state = interfisa(*fixture('interfisa2'), date(2026, 10, 30))
        self.assertTrue(state.startswith('published'))
        self.assertEqual(rows[0]['Vigencia'], 'Desde 2026-10-31 hasta 2026-10-31')
        self.assertEqual(rows[1]['Tipo de beneficio verificado'], 'cuotas_sin_intereses')
        self.assertNotIn('450.000', rows[1]['Detalle'])
        self.assertEqual(interfisa(*fixture('interfisa2'), date(2026, 11, 1)), ([], 'expired'))

    def test_source_says_2027_do_not_silently_change_year(self):
        rows, state = interfisa(*fixture('interfisa3'), date(2026, 10, 30))
        self.assertTrue(state.startswith('published'))
        self.assertIn('2027-10-31', rows[0]['Vigencia'])
        self.assertEqual(rows[0]['Día de promoción'], 'todos los viernes')
        self.assertIn('Shopping China', rows[0]['Detalle'])

    def test_identity_mismatch_stays_in_queue(self):
        item, text = fixture('interfisa1')
        rows, state = interfisa({**item, 'name': 'OTRO COMERCIO'}, text, date(2026, 10, 30))
        self.assertEqual(rows, [])
        self.assertIn('identity', state)

    def test_unknown_template_and_missing_cap_fail_closed(self):
        item, text = fixture('interfisa1')
        for text in (text.replace('Tope de compra mensual', 'Monto'), text.replace('25% de reintegro', 'Hasta 25% de reintegro')):
            rows, state = interfisa(item, text, date(2026, 10, 30))
            self.assertEqual(rows, [])
            self.assertTrue(state.startswith('review_required'))

    def test_discovery_deduplicates_pair_not_wrong_merchant(self):
        html = ''.join(f'<div class="cards-con-modal-item"><p class="text-uppercase">{name}</p><a href="/one.pdf">bases</a></div>' for name in ['A', 'A', 'B'])
        rows = discover(html, 'interfisa', 'https://www.interfisa.com.py/beneficios')
        self.assertEqual(len(rows), 2)

    def test_basa_footer_documents_not_campaigns(self):
        html = '<div class="promo-grid"><a href="/a.pdf">AUTOLAV</a></div><footer><a href="/contract.pdf">Contrato</a></footer>'
        rows = discover(html, 'basa', 'https://www.bancobasa.com.py/promociones-personas')
        self.assertEqual([r['name'] for r in rows], ['AUTOLAV'])

    def test_external_link_denied(self):
        with self.assertRaises(ValueError):
            official_url('https://example.org/a.pdf', 'https://www.interfisa.com.py/beneficios')

    def test_extra_validity_clause_is_held(self):
        item, text = fixture('interfisa1')
        for extra in (' excepto feriados', ' y solamente pagos por QR'):
            changed = text.replace('hasta el 31/10/2026', 'hasta el 31/10/2026' + extra)
            rows, state = interfisa(item, changed, date(2026, 10, 30))
            self.assertEqual(rows, [])
            self.assertIn('validity', state)

    def test_funding_or_separate_purchase_date_is_not_promotion_date(self):
        item, text = fixture('interfisa1')
        for condition in ('Requiere fondeo previo.', 'Las compras aplican el 01/11/2026.'):
            changed = text.replace('No acumulables con otras promociones.', condition)
            rows, state = interfisa(item, changed, date(2026, 10, 30))
            self.assertEqual(rows, [])
            self.assertIn('eligibility', state)

    def test_normalization_preserves_financing_and_purchase_cap_kind(self):
        from promo_backend.normalize import normalize_row
        from promo_backend.quality import normalize_terms
        item, text = fixture('basa4')
        rows, _ = basa(item, text, date(2026, 10, 30))
        normalized = normalize_row('Basa', rows[0])
        limits = normalize_terms(normalized)['limits']
        self.assertEqual(limits[0]['kind'], 'purchase')
        self.assertEqual(limits[0]['amount'], 200000)
        self.assertEqual(limits[0]['period'], 'mensual')
        rows, _ = interfisa(*fixture('interfisa2'), date(2026, 10, 30))
        financing = normalize_row('Interfisa', rows[1])
        self.assertEqual(financing['benefit_type'], 'cuotas_sin_intereses')
        self.assertEqual(financing['percentages'], [])
        self.assertEqual(normalize_terms(financing)['limits'], [])

    def test_financing_preserves_shared_purchase_cap_without_assigning_scope(self):
        rows, _ = interfisa(*fixture('interfisa3'), date(2026, 10, 30))
        financing = rows[-1]
        self.assertIn('Tope de compra mensual de Gs. 2.500.000', financing['Detalle'])
        self.assertIn('adicionales', financing['Detalle'])
        self.assertEqual(financing['Estado verificacion'], 'unconfirmed')
        self.assertIn('no está confirmada', financing['Montos / topes'])
        self.assertNotIn('no se asigna el tope', financing['Detalle'])

    def test_cache_mtime_does_not_establish_fetch_time(self):
        import tempfile, os, hashlib
        from scrapers.new_bank_documents import document_provenance
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'doc.pdf'; path.write_bytes(b'%PDF-test')
            url = 'https://www.interfisa.com.py/test.pdf'
            first = document_provenance(url, path.read_bytes(), path)
            self.assertIsNone(first['fetched_at'])
            os.utime(path, (2000000000, 2000000000))
            self.assertIsNone(document_provenance(url, path.read_bytes(), path)['fetched_at'])
            saved = {'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'fetched_at': '2026-10-30T15:00:00+00:00'}
            path.with_suffix('.metadata.json').write_text(json.dumps(saved))
            self.assertEqual(document_provenance(url, path.read_bytes(), path)['fetched_at'], saved['fetched_at'])
            path.write_bytes(b'changed')
            self.assertIsNone(document_provenance(url, path.read_bytes(), path)['fetched_at'])

    def test_dates_invalid_are_not_guessed(self):
        with self.assertRaises(ValueError):
            numeric_dates('31/02/2026')


if __name__ == '__main__':
    unittest.main()
