import json
import unittest
import re
from urllib.parse import urlparse, unquote
from pathlib import Path

class AuditIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path('public/promotions.json').read_text(encoding='utf-8'))

    def test_ids_are_unique_after_migration_and_variant_expansion(self):
        ids=[p['id'] for p in self.rows]
        self.assertEqual(len(ids),len(set(ids)))

    def test_campaign_rows_keep_merchant_specific_end_dates(self):
        rows=[p for p in self.rows if p['bank']=='Sudameris']
        k=next(p for p in rows if p['id']=='adf5bc3eb1fc7e00')
        patio=next(p for p in rows if p['merchant_name']=='PATIO COLONIAL' and p.get('source_verification')=='official_document')
        self.assertEqual(k['terms']['ends_on'],'2026-12-31')
        self.assertEqual(patio['terms']['ends_on'],'2026-08-02')
        # The official bank renamed its PDF in October; a literal old basename
        # must not invalidate an otherwise source-linked merchant date contract.
        parsed=urlparse(k['source_page_url'])
        self.assertEqual(parsed.hostname,'www.sudameris.com.py')
        self.assertRegex(unquote(parsed.path).lower(),r'(?:gastronimia|gastronomia)[^/]*\.pdf$')
        self.assertNotEqual(k['source_url'],k['source_page_url'])

    def test_reviewed_music_hall_keeps_audio_and_financing_separate(self):
        # Historical review contract: the live campaign legitimately became unconfirmed.
        # Fixture provenance is recorded alongside the captured 2026-10-24 snapshot.
        rows=json.loads((Path(__file__).parent/'fixtures/music-hall-reviewed-20261024.json').read_text(encoding='utf-8'))
        self.assertTrue(all(p.get('source_verification')=='official_document' for p in rows))
        self.assertEqual(len(rows),3)
        self.assertEqual({p['terms']['starts_on'] for p in rows},{'2026-10-19'})
        self.assertEqual({p['terms']['ends_on'] for p in rows},{'2026-10-24'})
        audio=next(p for p in rows if p['offer_kind']=='audio')
        self.assertEqual(audio['percentages'],['5%'])
        financing=next(p for p in rows if p['offer_kind']=='financing')
        self.assertEqual(financing['benefit_type'],'cuotas_sin_intereses')

    def test_unconfirmed_music_hall_does_not_inherit_reviewed_campaign(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/music-hall-reviewed-20261024.json').read_text(encoding='utf-8'))
        reviewed_ids={p['id'] for p in fixture}
        campaign_ids={p['campaign_id'] for p in fixture}
        for row in self.rows:
            if row['id'] in reviewed_ids and row.get('source_verification')!='official_document':
                self.assertNotIn(row.get('campaign_id'),campaign_ids)
