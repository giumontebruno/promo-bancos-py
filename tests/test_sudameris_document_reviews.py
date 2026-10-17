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
        row={'Bases y condiciones URL':'https://www.sudameris.com.py/descargas/documentos/6ad0efa34ca4d016036253/B%26C-MUSICHALL-19-10-26.pdf','URL':'stable'}
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
