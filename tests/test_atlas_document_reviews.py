import unittest, hashlib, json
from unittest.mock import Mock, patch
from scrapers.extract_atlas import apply_document_reviews

class AtlasDocumentReviews(unittest.TestCase):
    def test_changed_document_does_not_confirm(self):
        row={'Comercio/Promoción':'Test','Detalle':'terms','Cantidad de descuento / beneficio':'20%'}
        review={'document_url':'https://example.org/terms.pdf','document_sha256':hashlib.sha256(b'original').hexdigest(),'detail_sha256':hashlib.sha256(b'terms').hexdigest(),'benefit_summary':'Hasta 20%','note':'Scoped exceptions'}
        session=Mock();session.get.return_value.content=b'changed'
        with patch('scrapers.extract_atlas.Path') as path:
            path.return_value.read_text.return_value=json.dumps({'Test':review})
            result=apply_document_reviews([row],session)[0]
        self.assertEqual(result['Estado verificacion'],'unconfirmed')
        self.assertEqual(result['Detalle'],'terms')
    def test_matching_document_retains_original_and_exceptions(self):
        row={'Comercio/Promoción':'Test','Detalle':'terms','Cantidad de descuento / beneficio':'20%'}
        review={'document_url':'https://example.org/terms.pdf','document_sha256':hashlib.sha256(b'original').hexdigest(),'detail_sha256':hashlib.sha256(b'terms').hexdigest(),'benefit_summary':'Hasta 20%','note':'Nike: 10%; Nueva Americana: 12 cuotas'}
        session=Mock();session.get.return_value.content=b'original'
        with patch('scrapers.extract_atlas.Path') as path:
            path.return_value.read_text.return_value=json.dumps({'Test':review})
            result=apply_document_reviews([row],session)[0]
        self.assertEqual(result['Estado verificacion'],'official_document')
        self.assertEqual(result['Texto original de la fuente'],'terms')
        self.assertIn('Nike: 10%',result['Detalle'])
        self.assertEqual(result['Cantidad de descuento / beneficio'],'Hasta 20%')

if __name__=='__main__':unittest.main()
