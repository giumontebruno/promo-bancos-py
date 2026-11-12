import copy,json,tempfile,unittest
from pathlib import Path
from scrapers.documented_branch_inventory import apply,PREFIX
ROOT=Path(__file__).resolve().parents[1]
class DocumentedBranches(unittest.TestCase):
 def test_exact_33_addresses_no_geography_and_repeat_stable(self):
  rows=apply([],ROOT);self.assertEqual(len(rows),33);self.assertEqual(len({r['id'] for r in rows}),33)
  self.assertEqual(len([r for r in rows if r['bank']=='Interfisa']),30)
  self.assertEqual(len([r for r in rows if r['bank']=='Familiar']),3)
  for r in rows:
   self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertEqual(r['geocode_source'],'');self.assertEqual(len(r['promotion_ids']),2)
  injected=copy.deepcopy(rows);injected[0]['lat']=-25;injected[0]['lng']=-57
  self.assertEqual(apply(injected,ROOT),rows)
 def test_changed_source_or_offer_cannot_retain_stale_inventory(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   paths=['data/mcdonalds_documented_branches.json','public/promotions.json','outputs/interfisa_source_meta.json','outputs/familiar_extraction_review.json']
   for p in paths:
    target=root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/p).read_bytes())
   rows=apply([],root)
   p=root/'outputs/interfisa_source_meta.json';d=json.loads(p.read_text())
   for doc in d['documents']:
    if 'BYC_Mcdonalds.pdf' in doc['url']:doc['sha256']='changed'
   p.write_text(json.dumps(d));self.assertEqual(len(apply(rows,root)),3)
   p=root/'public/promotions.json';d=json.loads(p.read_text())
   for offer in d:
    if offer['bank']=='Familiar' and offer['merchant_name'].startswith("McDonald's -"):offer['raw_detail']='changed'
   p.write_text(json.dumps(d));self.assertEqual(apply(rows,root),[])
