"""Regression coverage for offline rebuilds and stable location identities."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scrapers'))
import build_locations as builder

class LocationRebuildTests(unittest.TestCase):
    def test_reviewed_branches_have_provenance_and_no_invented_coordinates(self):
        rows = json.loads((ROOT / 'data/sudameris_reviewed_branches.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows), len({row['id'] for row in rows}))
        for row in rows:
            self.assertTrue(row['source_url'].startswith('https://www.sudameris.com.py/'))
            self.assertEqual(len(row['source_sha256']), 64)
            self.assertTrue(row['address'])
            self.assertIsNone(row['lat'])
            self.assertIsNone(row['lng'])
            self.assertEqual(row['online_only'], row['branch_scope'] == 'online')

    def test_offline_rebuild_preserves_ungeocoded_id_without_network(self):
        point = {'id': 'new-id', 'bank': 'BNF', 'category': 'Combustible', 'merchant_name': 'Local', 'address': 'Street 123', 'city': 'Asuncion', 'lat': None, 'lng': None, 'geocode_source': ''}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'locations.json'
            output.write_text(json.dumps({'locations': [dict(point, id='stable-id', google_enrichment_status='needs_review', google_candidate={'lat': -25})]}), encoding='utf-8')
            with patch.object(builder, 'ROOT', root), patch.object(builder, 'OUT_JSON', output), patch.object(builder, 'seed_locations', return_value=[]), patch.object(builder, 'build_bnf_locations', return_value=[point]), patch.object(builder, 'write_csv'), patch.object(builder, 'geocode_locations') as geocode, patch.object(sys, 'argv', ['build_locations.py', '--skip-geocoding']):
                builder.main()
            geocode.assert_not_called()
            result = json.loads(output.read_text(encoding='utf-8'))['locations']
            self.assertEqual(result[0]['id'], 'stable-id')
            self.assertIsNone(result[0]['lat'])
            self.assertEqual(result[0]['google_enrichment_status'], 'needs_review')
            self.assertEqual(result[0]['google_candidate'], {'lat': -25})

if __name__ == '__main__':
    unittest.main()
