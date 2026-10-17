import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scrapers import extract_bnf

class BnfRevalidationTests(unittest.TestCase):
    def test_existing_pdf_is_revalidated_without_destroying_it_on_bad_response(self):
        class Response:
            content=b'%PDF-new official bytes'
            def raise_for_status(self): pass
        with tempfile.TemporaryDirectory() as tmp, patch.object(extract_bnf,'PDF_DIR',Path(tmp)):
            p=Path(tmp)/'terms.pdf';p.write_bytes(b'%PDF-old bytes')
            with patch.object(extract_bnf.requests,'get',return_value=Response()) as get:
                extract_bnf.download_pdf('https://www.bnf.gov.py/terms.pdf')
                get.assert_called_once()
            self.assertEqual(p.read_bytes(),Response.content)
            Response.content=b'<html>temporarily unavailable</html>'
            with patch.object(extract_bnf.requests,'get',return_value=Response()):
                with self.assertRaises(ValueError):
                    extract_bnf.download_pdf('https://www.bnf.gov.py/terms.pdf')
            self.assertEqual(p.read_bytes(),b'%PDF-new official bytes')
