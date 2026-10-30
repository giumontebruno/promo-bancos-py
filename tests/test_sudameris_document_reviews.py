import unittest
import hashlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scrapers'))
from build_sudameris_table import reviewed_document_rows

class ReviewedDocumentsTests(unittest.TestCase):
    def test_document_hash_change_blocks_review(self):
        row={'Bases y condiciones URL':'https://www.sudameris.com.py/descargas/documentos/6ad6300056cc7842366125/B%26C-MUSICHALL-19-10-2026.pdf','URL':'stable'}
        class Response:
            content=b'changed official document'
            def raise_for_status(self): pass
        with patch('build_sudameris_table.requests.get',return_value=Response()):
            with self.assertRaisesRegex(ValueError,'Reviewed PDF changed'):
                reviewed_document_rows(row)

    def test_audio_exception_is_separate_from_general_discount(self):
        import json
        reviews=json.loads(Path('data/sudameris_document_reviews.json').read_text(encoding='utf-8'))
        music=next(r for r in reviews if r['merchant'].startswith('Music'))
        self.assertEqual([x[0] for x in music['offers']],['base','audio','financing'])
        self.assertIn('excepto equipos de audio',music['offers'][0][1])
        self.assertIn('5%',music['offers'][1][1])

    def test_generic_unconfirmed_row_does_not_erase_card_variants(self):
        from build_sudameris_table import retain_unconfirmed_rows
        common={'URL':'official','Comercio/Promoción':'Merchant'}
        old=[{**common,'Variante':'base','Estado verificacion':'official_document'},
             {**common,'Variante':'premium','Estado verificacion':'official_document'}]
        rows=retain_unconfirmed_rows([{**common,'Estado verificacion':'unconfirmed'}],old)
        self.assertEqual(len(rows),3)
        self.assertEqual([r.get('Variante') for r in rows],[None,'base','premium'])
        self.assertTrue(all(r['Estado verificacion']=='unconfirmed' for r in rows))
        self.assertTrue(all(r['Estado verificacion']=='official_document' for r in old))

    def test_verified_replacement_does_not_retain_superseded_variants(self):
        from build_sudameris_table import retain_unconfirmed_rows
        common={'URL':'official','Comercio/Promoción':'Merchant'}
        current={**common,'Variante':'base','Estado verificacion':'official_document'}
        rows=retain_unconfirmed_rows([current],[{**common,'Variante':'old'}])
        self.assertEqual(rows,[current])

    def test_current_biggie_scope_preserves_minimum_purchase_cap_and_channel(self):
        import json
        reviews=json.loads(Path('data/sudameris_document_reviews.json').read_text(encoding='utf-8'))
        r=next(r for r in reviews if r['merchant']=='Biggie Express')
        self.assertEqual(r['start'],'2026-07-01')
        self.assertEqual(r['end'],'2026-12-31')
        self.assertEqual(r['minimum_purchase_pyg'],50000)
        self.assertIn('700.000',r['cap'])
        self.assertIn('solo válido para compras en locales físicos',r['conditions'])
        self.assertEqual(r['day'],'01 de cada mes')
        self.assertEqual(r['sha256'],'c7a110aa9cc202b3d9ce0c8743be7366c2b5bda8ff871e9e0a9586eacac70cd3')
