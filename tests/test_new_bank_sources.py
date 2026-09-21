import unittest
from scrapers.extract_familiar import parse_cards, terms_pdf


class FamiliarTests(unittest.TestCase):
    def test_preserves_payment_qualifiers_and_pagination(self):
        rows, next_url = parse_cards('''<div class="promotions-collection-item"><p fs-list-field="name">Comercio</p><p fs-list-field="description">Lunes</p><div class="text-s">30% con Platinum</div><div class="text-s">20% con Oro</div><a href="/pdfs/test">Bases</a></div><a class="w-pagination-next" href="?236ef13f_page=2">Siguiente</a>''')
        self.assertEqual(rows[0]['benefit_summary'], '30% con Platinum; 20% con Oro')
        self.assertEqual(rows[0]['review_status'], 'pending_terms_review')
        self.assertTrue(next_url.endswith('?236ef13f_page=2'))

    def test_terms_only_accept_official_cdn_pdf(self):
        self.assertEqual(terms_pdf('<iframe src="https://drive.google.com/viewer?url=https%3A%2F%2Fcdn.prod.website-files.com%2Fx.pdf"></iframe>'), 'https://cdn.prod.website-files.com/x.pdf')
        self.assertIsNone(terms_pdf('<iframe src="https://drive.google.com/viewer?url=http%3A%2F%2Flocalhost%2Fx.pdf"></iframe>'))
