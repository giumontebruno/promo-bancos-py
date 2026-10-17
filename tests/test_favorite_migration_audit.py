import json
import unittest
from pathlib import Path
from promo_backend.quality import favorite_aliases

class FavoriteMigrationAuditTests(unittest.TestCase):
    def test_bnf_collision_suffix_change_keeps_correct_card(self):
        common={'bank':'BNF','merchant_name':'Example','category':'Supermercados','source_url':'official.pdf','validity':'2026-10','day_text':'viernes'}
        old={**common,'id':'old-classic','benefit_summary':'20% reintegro','verified_cards':'Visa Clásica'}
        current=[{**old,'id':'new-classic'},{**common,'id':'premium','benefit_summary':'30% reintegro','verified_cards':'Visa Oro y Platinum'}]
        self.assertEqual(favorite_aliases([old],current)['old-classic'],'new-classic')

    def test_all_archived_ids_and_campaigns_resolve_without_cycles(self):
        rows=json.loads(Path('public/promotions.json').read_text(encoding='utf-8'))
        archive=json.loads(Path('data/promotion_history_20261017.json').read_text(encoding='utf-8'))['offers']
        aliases=json.loads(Path('public/manifest.json').read_text(encoding='utf-8'))['favorite_aliases']
        ids={v for p in rows for v in (p['id'],p.get('campaign_id')) if v}
        for p in archive:
            for original in filter(None,(p['id'],p.get('campaign_id'))):
                target=original;seen=set()
                while target in aliases:
                    self.assertNotIn(target,seen,original)
                    seen.add(target);target=aliases[target]
                self.assertIn(target,ids,original)

    def test_expired_removed_offer_keeps_alias_without_becoming_current(self):
        from promo_backend.normalize import retain_expired_history
        old = {'id': 'ended', 'bank': 'Atlas', 'merchant_name': 'Offer', 'category': 'General', 'terms': {'ends_on': '2026-10-16', 'conflicting_dates': False}}
        future = {**old, 'id': 'missing-future', 'terms': {'ends_on': '2026-12-31'}}
        current = retain_expired_history([], [old, old, future], today='2026-10-17')
        self.assertEqual(len(current), 1)
        self.assertTrue(current[0]['archived'])
        self.assertEqual(current[0]['terms']['ends_on'], '2026-10-16')
        self.assertEqual(favorite_aliases([old], current, {'legacy': 'ended'}), {'legacy': 'ended'})
