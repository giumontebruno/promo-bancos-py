import json
import unittest
from pathlib import Path
from promo_backend.quality import favorite_aliases, favorite_unavailable

class FavoriteMigrationAuditTests(unittest.TestCase):
    def test_bnf_collision_suffix_change_keeps_correct_card(self):
        common={'bank':'BNF','merchant_name':'Example','category':'Supermercados','source_url':'official.pdf','validity':'2026-10','day_text':'viernes'}
        old={**common,'id':'old-classic','benefit_summary':'20% reintegro','verified_cards':'Visa Clásica'}
        current=[{**old,'id':'new-classic'},{**common,'id':'premium','benefit_summary':'30% reintegro','verified_cards':'Visa Oro y Platinum'}]
        self.assertEqual(favorite_aliases([old],current)['old-classic'],'new-classic')

    def test_all_archived_ids_and_campaigns_resolve_without_cycles(self):
        rows=json.loads(Path('public/promotions.json').read_text(encoding='utf-8'))
        archive=json.loads(Path('data/promotion_history_20261017.json').read_text(encoding='utf-8'))['offers']
        manifest=json.loads(Path('public/manifest.json').read_text(encoding='utf-8'))
        aliases=manifest['favorite_aliases']
        unavailable=manifest.get('favorite_unavailable',{})
        ids={v for p in rows for v in (p['id'],p.get('campaign_id')) if v}
        for p in archive:
            for original in filter(None,(p['id'],p.get('campaign_id'))):
                target=original;seen=set()
                while target in aliases:
                    self.assertNotIn(target,seen,original)
                    seen.add(target);target=aliases[target]
                if target not in ids:
                    self.assertIn(original,unavailable,original)
                    entry=unavailable[original]
                    self.assertEqual(entry['reason'],'not_in_current_sources')
                    self.assertEqual(entry['bank'],p['bank'])
                    self.assertEqual(entry['merchant_name'],p['merchant_name'])
                    self.assertEqual(entry['source_url'],p.get('source_url',''))
                    self.assertEqual(entry['last_known_ends_on'],(p.get('terms') or {}).get('ends_on'))
                    self.assertNotIn(original,aliases)
                    self.assertNotIn('target',entry)
                else:
                    self.assertNotIn(original,unavailable)

    def test_expired_removed_offer_keeps_alias_without_becoming_current(self):
        from promo_backend.normalize import retain_expired_history
        old = {'id': 'ended', 'bank': 'Atlas', 'merchant_name': 'Offer', 'category': 'General', 'terms': {'ends_on': '2026-10-16', 'conflicting_dates': False}}
        future = {**old, 'id': 'missing-future', 'terms': {'ends_on': '2026-12-31'}}
        current = retain_expired_history([], [old, old, future], today='2026-10-17')
        self.assertEqual(len(current), 1)
        self.assertTrue(current[0]['archived'])
        self.assertEqual(current[0]['terms']['ends_on'], '2026-10-16')
        self.assertEqual(favorite_aliases([old], current, {'legacy': 'ended'}), {'legacy': 'ended'})

    def test_missing_unknown_and_future_dates_are_not_reactivated(self):
        old=[{'id':'unknown','bank':'Atlas','merchant_name':'Martiderm','terms':{}},
             {'id':'future','bank':'CU','merchant_name':'Santa Clara','terms':{'ends_on':'2027-01-01'}}]
        current=[]
        unavailable=favorite_unavailable(old,current)
        self.assertEqual(set(unavailable),{'unknown','future'})
        self.assertIsNone(unavailable['unknown']['last_known_ends_on'])
        self.assertEqual(unavailable['future']['last_known_ends_on'],'2027-01-01')
        self.assertEqual(current,[])
        self.assertEqual(favorite_aliases(old,current),{})
        self.assertNotIn('benefit_summary',unavailable['future'])

    def test_tombstone_clears_only_when_real_id_or_resolved_alias_returns(self):
        old=[{'id':'old','bank':'B','merchant_name':'M'}]
        tomb=favorite_unavailable(old,[])
        self.assertEqual(favorite_unavailable([],[],existing=tomb),tomb)
        self.assertEqual(favorite_unavailable(old,[{'id':'old'}],existing=tomb),{})
        self.assertEqual(favorite_unavailable(old,[{'id':'new'}],{'old':'new'},tomb),{})
        with self.assertRaisesRegex(ValueError,'cycle'):
            favorite_unavailable(old,[],{'old':'next','next':'old'})
