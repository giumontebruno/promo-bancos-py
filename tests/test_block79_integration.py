import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/"docs/geo-audit/block79"
sys.path.insert(0,str(ROOT/"scrapers"))
from reviewed_geo import apply_reviews
load=lambda p:json.loads(p.read_text(encoding="utf-8"))
NEW=load(ROOT/"data/multibank_reviewed_branches_20261020.json")
FILLS=load(ROOT/"data/bnf_scavone_reviewed_locations.json")
REVIEWS=NEW+FILLS
EXCLUDED=load(WORK/"scavone-excluded.json")
STALE=("place_id","formatted_address","google_name","google_types","google_confidence","google_enrichment_status","google_last_attempt_at","google_candidate_place_id","google_candidate")

class Block79Integration(unittest.TestCase):
 def test_approved_scope_exactly_53_new_26_fills_5_excluded(self):
  self.assertEqual((len(NEW),len(FILLS),len(EXCLUDED)),(53,26,5))
  self.assertEqual(len({p["id"] for p in REVIEWS}),79)
  approved=set(load(WORK/"scavone-eligible-ids.json"))
  self.assertEqual({p["id"] for p in FILLS},approved)
  self.assertTrue({p["existing_location_id"] for p in EXCLUDED}.isdisjoint({p["id"] for p in REVIEWS}))
 def test_53_seeds_reapply_exact_identity_and_clear_stale_google_fields(self):
  rows=copy.deepcopy(NEW)
  for row in rows:
   row.update({field:"stale" for field in STALE});row.update(lat=None,lng=None,needs_review=True,location_review_status="unconfirmed")
  before=[p["id"] for p in rows];apply_reviews(rows,REVIEWS)
  self.assertEqual(before,[p["id"] for p in rows])
  for actual,review in zip(rows,NEW):
   self.assertEqual((actual["lat"],actual["lng"]),(review["lat"],review["lng"]))
   self.assertEqual(actual["promotion_ids"],review["promotion_ids"])
   self.assertEqual(actual["participation_ends_on"],review["participation_ends_on"])
   self.assertFalse(actual["needs_review"]);self.assertEqual(actual["location_review_status"],"confirmed")
   self.assertTrue(set(STALE).isdisjoint(actual))
 def test_26_scavone_matches_real_bank_branch_rows_and_preserves_all_ids(self):
  rows=load(ROOT/"outputs/bnf_branch_sources.json")
  before=[p["id"] for p in rows];apply_reviews(rows,FILLS)
  self.assertEqual(before,[p["id"] for p in rows])
  byid={p["id"]:p for p in rows}
  for r in FILLS:
   actual=byid[r["id"]]
   for key in ("lat","lng","promotion_ids","participation_ends_on","operator_source_url","geocode_source"):
    self.assertEqual(actual[key],r[key],(r["id"],key))
 def test_changed_identity_refuses_every_review_without_mutation(self):
  for r in REVIEWS:
   for key in ("id","bank","merchant_name","address","city","source_url"):
    row={**r,key:"changed", "lat":None,"lng":None}
    before=copy.deepcopy(row);apply_reviews([row],REVIEWS)
    self.assertEqual(row,before,(r["id"],key))
 def test_published_local_catalog_contains_79_once_with_exact_evidence(self):
  rows=load(ROOT/"public/locations.json")["locations"]
  counts={r["id"]:sum(p["id"]==r["id"] for p in rows) for r in REVIEWS}
  self.assertTrue(all(n==1 for n in counts.values()),counts)
  byid={p["id"]:p for p in rows}
  for r in REVIEWS:
   actual=byid[r["id"]]
   for key in ("bank","merchant_name","address","city","source_url","lat","lng","promotion_ids","participation_ends_on"):
    self.assertEqual(actual.get(key),r.get(key),(r["id"],key))
   self.assertTrue(set(STALE).isdisjoint(actual),r["id"])
   evidence=ROOT/r["review_evidence_file"]
   self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(),r["review_evidence_sha256"])
 def test_five_exclusions_keep_original_coordinates_and_are_not_reviewed(self):
  rows=load(ROOT/"public/locations.json")["locations"];byid={p["id"]:p for p in rows}
  for e in EXCLUDED:
   row=byid[e["existing_location_id"]]
   self.assertEqual((row.get("lat"),row.get("lng")),(e.get("existing_lat"),e.get("existing_lng")))
   self.assertNotEqual(row.get("reviewed_block"),"2026-10-20-block79")
   before=copy.deepcopy(row);apply_reviews([row],REVIEWS);self.assertEqual(row,before)

if __name__=="__main__":unittest.main()
