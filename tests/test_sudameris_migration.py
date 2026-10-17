import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from scrapers import extract_sudameris as scraper
from promo_backend.normalize import normalize_row


class Response:
    def __init__(self, payload):
        self.text = json.dumps(payload)


class SudamerisMigrationTests(unittest.TestCase):
    def test_pagination_collects_all_pages(self):
        pages = [Response({'data': [{'id': n, 'url': scraper.BASE + '/personas/beneficios/x'}],
                           'current_page': n, 'has_more': n == 1}) for n in (1, 2)]
        with patch.object(scraper, 'get', side_effect=pages):
            self.assertEqual([x['id'] for x in scraper.current_offers(None)], [1, 2])

    def test_repeated_page_aborts_without_publishing_partial_data(self):
        page = Response({'data': [{'id': 1, 'url': scraper.BASE + '/personas/beneficios/x'}],
                         'current_page': 1, 'has_more': True})
        with patch.object(scraper, 'get', return_value=page):
            with self.assertRaises(ValueError):
                scraper.current_offers(None)

    def test_empty_catalog_is_not_success(self):
        with patch.object(scraper, 'get', return_value=Response({'data': [], 'current_page': 1, 'has_more': False})):
            with self.assertRaises(ValueError):
                scraper.current_offers(None)

    def test_updated_public_link_does_not_change_identity(self):
        row = {'Comercio': 'KAISEKI', 'Beneficio': '20% reintegro', 'URL': 'https://official/old.pdf'}
        previous = normalize_row('Sudameris', row)
        current = normalize_row('Sudameris', {**row, 'URL fuente actual': 'https://official/current.pdf', 'Estado verificacion': 'official_document'})
        self.assertEqual(previous['id'], current['id'])
        self.assertEqual(current['source_page_url'], 'https://official/current.pdf')
        self.assertEqual(current['source_verification'], 'official_document')

    def test_campaign_title_migration_is_explicit(self):
        self.assertEqual(scraper.campaign_identity('GASTRONOMÍA 26'), scraper.campaign_identity('Gastronomía'))
        self.assertNotEqual(scraper.campaign_identity('Gastronomía Elite'), scraper.campaign_identity('Gastronomía'))
