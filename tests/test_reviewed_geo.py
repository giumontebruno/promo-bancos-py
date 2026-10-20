import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scrapers"))
from reviewed_geo import apply_reviews

class ReviewedGeoTests(unittest.TestCase):
    def setUp(self):
        self.reviews=json.loads((ROOT/"data/bnf_farmacenter_reviewed_locations.json").read_text(encoding="utf8"))
    def test_exact_matches_restore_coordinates_and_scope_without_changing_ids(self):
        source=json.loads((ROOT/"outputs/bnf_branch_sources.json").read_text(encoding="utf8"))
        original_ids=[p["id"] for p in source]
        apply_reviews(source,self.reviews)
        self.assertEqual(original_ids,[p["id"] for p in source])
        matched=[p for p in source if p.get("geocode_source")=="official_farmacenter_locator"]
        self.assertEqual(len(matched),40)
        for p in matched:
            self.assertEqual(p["participation_ends_on"],"2026-10-26")
            self.assertEqual(p["promotion_ids"],["fff06c1bdd0c75f5","fff06c1bdd0c75f5-b44596db"])
            self.assertTrue(p["operator_source_url"].startswith("https://www.farmacenter.com.py/tiendas/"))
    def test_changed_address_or_bank_evidence_does_not_apply_coordinates(self):
        for key in ("address","city","source_url","bank"):
            p=dict(self.reviews[0],lat=None,lng=None,**{key:"changed"})
            before=copy.deepcopy(p)
            apply_reviews([p],self.reviews)
            self.assertEqual(p,before)
