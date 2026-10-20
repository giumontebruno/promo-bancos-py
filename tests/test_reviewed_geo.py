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
        self.assertEqual(len(matched),78)
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

    def test_additional_reviews_preserve_bank_identity_and_operator_source(self):
        reviews=json.loads((ROOT/"data/bnf_additional_reviewed_locations.json").read_text(encoding="utf8"))
        rows=json.loads((ROOT/"outputs/bnf_branch_sources.json").read_text(encoding="utf8"))
        before={x["id"] for x in rows}
        apply_reviews(rows,reviews)
        matched=[x for x in rows if x.get("geocode_source") in {"official_catedral_locator","official_petrochaco_locator"}]
        self.assertEqual(len(matched),99)
        self.assertEqual(before,{x["id"] for x in rows})
        self.assertEqual(sum(x["geocode_source"]=="official_catedral_locator" for x in matched),97)
        for row in matched:
            expected="2026-10-28" if row["merchant_name"]=="PETROCHACO" else "2026-10-26"
            self.assertEqual(row["participation_ends_on"],expected)
            self.assertTrue(row["promotion_ids"])
    def test_official_coordinates_cannot_keep_stale_google_navigation_or_review_flags(self):
        review=self.reviews[0]
        row=dict(review,place_id="wrong-place",google_confidence="review",google_enrichment_status="needs_review",google_name="Wrong shop")
        apply_reviews([row],[review])
        for key in ("place_id","google_confidence","google_enrichment_status","google_name"):
            self.assertNotIn(key,row)
        self.assertEqual((row["lat"],row["lng"]),(review["lat"],review["lng"]))
