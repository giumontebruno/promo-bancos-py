import copy,hashlib,json,unittest
from pathlib import Path
from promo_backend.reviewed_shell import apply_review
from promo_backend.normalize import load_promotions
from promo_backend.quality import deduplicate
ROOT=Path(__file__).resolve().parents[1]
class ShellReviewTests(unittest.TestCase):
 def setUp(self):
  self.review=json.loads((ROOT/'data/itau_shell_october_review.json').read_text(encoding='utf8'))
 def test_refresh_reapplies_date_without_merging_variants(self):
  promos,_=deduplicate(load_promotions());other=copy.deepcopy([p for p in promos if p['id'] not in self.review['offers']]);apply_review(promos,self.review)
  rows=[p for p in promos if p['id'] in self.review['offers']]
  self.assertEqual(len(rows),2);self.assertEqual({p['terms']['ends_on'] for p in rows},{'2026-10-26'})
  self.assertEqual({p['terms']['limits'][0]['amount'] for p in rows},{150000,500000})
  self.assertEqual(other,[p for p in promos if p['id'] not in self.review['offers']])
 def test_changed_evidence_cannot_silently_renew(self):
  promos,_=deduplicate(load_promotions());p=next(p for p in promos if p['id'] in self.review['offers']);p['raw_detail']+=' changed';apply_review([p],self.review);self.assertEqual(p['source_verification'],'unconfirmed')
 def test_exact_approved_stations_and_scope(self):
  rows=json.loads((ROOT/'data/itau_shell_reviewed_branches.json').read_text(encoding='utf8'))
  self.assertEqual(len(rows),71);self.assertEqual(len({p['id'] for p in rows}),71)
  for p in rows:
   self.assertEqual(set(p['promotion_ids']),set(self.review['offers']));self.assertEqual(p['participation_ends_on'],'2026-10-26');self.assertEqual(p['geocode_source'],'official_shell_locator');self.assertTrue(p['operator_source_url'].startswith('https://find.shell.com/'))
if __name__=='__main__':unittest.main()
