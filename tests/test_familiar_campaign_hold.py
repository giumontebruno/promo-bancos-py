import unittest
from promo_backend.normalize import normalize_row


class FamiliarCampaignHoldTests(unittest.TestCase):
    def test_cached_mariscal_row_cannot_publish_mariano_terms(self):
        row = {
            'Comercio': 'FARMACIA CATEDRAL-SHOPPING MARISCAL',
            'Beneficio': '20% de reintegro',
            'Texto original de la fuente': 'BASES Y CONDICIONES PROMOCIÓN “JUEVES MARIANO”',
            'URL detalle': 'https://www.familiar.com.py/pdfs/promocionesybeneficios-martes-mariscal',
        }
        held = normalize_row('Familiar', row)
        self.assertEqual(held['source_verification'], 'unconfirmed')
        self.assertEqual(held['variant_review_reason'], 'shopping_campaign_terms_mismatch')
        corrected = normalize_row('Familiar', {**row, 'Texto original de la fuente': 'MARTES MARISCAL'})
        self.assertNotEqual(corrected.get('source_verification'), 'unconfirmed')
        self.assertEqual(held['id'], corrected['id'])
        mariano = normalize_row('Familiar', {**row, 'Comercio': 'FARMACIA CATEDRAL-SHOPPING MARIANO'})
        self.assertNotEqual(mariano.get('source_verification'), 'unconfirmed')
