import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parent
R=W.parent
sys.path[:0]=[str(W/"scrapers"),str(R/"scrapers")]
import location_qa_holds as holds
import enrich_locations_google as google
import build_locations as builder
BASE={"id":"test-branch","bank":"BNF","merchant_name":"Example","address":"A esq. B","city":"Asunción",
      "source_url":"https://bank.invalid/terms.pdf","category":"Farmacias","department":"Capital",
      "lat":-25.3,"lng":-57.6,"geocode_source":"google_places_text_search","google_confidence":"high",
      "google_enrichment_status":"matched","place_id":"original-candidate","needs_review":False}
def registry():
    return {"holds":[{"id":BASE["id"],"decision":"hold","identity":{k:BASE[k] for k in holds.IDENTITY_FIELDS},
                     "reason":"Street conflict","evidence":[{"file":"capture.png","sha256":"example"}],"reviewed_on":"2026-10-20"}]}

class QAHolds(unittest.TestCase):
    def test_retains_every_original_candidate_field_and_id(self):
        row=copy.deepcopy(BASE);holds.apply_holds([row],registry())
        for k,v in BASE.items():
            if k!="needs_review":self.assertEqual(row[k],v)
        self.assertTrue(row["qa_hold"]);self.assertTrue(row["needs_review"])
        self.assertFalse(row["qa_hold_detail"]["identity_changed"])
    def test_google_does_not_request_or_accept_a_new_result_for_hold(self):
        row=copy.deepcopy(BASE);holds.apply_holds([row],registry());before=copy.deepcopy(row)
        self.assertFalse(google.should_enrich(row))
        google.apply_result(row,{"lat":-25.1,"lng":-57.2,"confidence":"high"})
        self.assertEqual(row,before)
    def test_nominatim_does_not_request_held_missing_coordinate(self):
        row={**BASE,"lat":None,"lng":None};holds.apply_holds([row],registry())
        with patch.object(builder,"load_cache",return_value={}),patch.object(builder,"save_cache"),patch.object(builder,"geocode") as request:
            builder.geocode_locations([row]);request.assert_not_called()
        self.assertIsNone(row["lat"])
    def test_direct_google_on_unmarked_published_hold_reads_registry(self):
        row=json.loads((R/"public/locations.json").read_text(encoding="utf8"))["locations"]
        row=copy.deepcopy(next(x for x in row if x["id"]=="loc-bnf-cfab9be2913261c1"))
        before=(row["lat"],row["lng"])
        google.apply_result(row,{"lat":-25.1,"lng":-57.2,"confidence":"high"})
        self.assertEqual((row["lat"],row["lng"]),before)
        self.assertTrue(row["qa_hold"]);self.assertFalse(google.should_enrich(row))
    def test_missing_registry_fails_closed(self):
        with patch.object(holds,"HOLD_PATH",W/"missing-registry.json"):
            with self.assertRaises(FileNotFoundError):holds.apply_holds([copy.deepcopy(BASE)])
    def test_identity_or_pdf_change_requires_human_review_not_automatic_release(self):
        for key in holds.IDENTITY_FIELDS:
            row={**BASE,key:"changed"};holds.apply_holds([row],registry())
            self.assertTrue(row["qa_hold"]);self.assertTrue(row["qa_hold_detail"]["identity_changed"])
    def test_unrelated_location_unchanged_and_duplicate_registry_rejected(self):
        row={**BASE,"id":"other"};before=copy.deepcopy(row)
        holds.apply_holds([row],registry());self.assertEqual(row,before)
        payload=registry();payload["holds"]*=2
        with self.assertRaises(ValueError):holds.apply_holds([row],payload)
    def test_release_needs_evidence_and_does_not_approve_coordinates(self):
        row=copy.deepcopy(BASE);holds.apply_holds([row],registry())
        payload=registry();payload["holds"][0]["decision"]="released"
        with self.assertRaises(ValueError):holds.apply_holds([row],payload)
        payload["holds"][0]["release_evidence"]={"file":"subsequent-review.json"}
        holds.apply_holds([row],payload)
        self.assertNotIn("qa_hold",row);self.assertTrue(row["needs_review"])
    def test_rebuild_overrides_then_holds_then_google_is_stable(self):
        with tempfile.TemporaryDirectory(dir=W) as directory:
            root=Path(directory);(root/"data").mkdir();(root/"public").mkdir()
            review={**BASE,"lat":-25.2,"lng":-57.3,"geocode_source":"official_operator_reviewed"}
            (root/"data/bnf_scavone_reviewed_locations.json").write_text(json.dumps([review]),encoding="utf8")
            holdfile=root/"data/location_qa_holds.json";holdfile.write_text(json.dumps(registry()),encoding="utf8")
            out=root/"public/locations.json"
            with patch.object(builder,"ROOT",root),patch.object(builder,"OUT_JSON",out),patch.object(builder,"write_csv"),patch.object(builder,"seed_locations",return_value=[copy.deepcopy(BASE)]),patch.object(builder,"build_bnf_locations",return_value=[]),patch.object(holds,"HOLD_PATH",holdfile),patch.object(sys,"argv",["build_locations.py","--skip-geocoding"]):
                builder.main();first=json.loads(out.read_text(encoding="utf8"))["locations"][0]
                self.assertTrue(first["qa_hold"]);self.assertTrue(first["needs_review"])
                self.assertEqual(first["lat"],review["lat"])
                builder.main();second=json.loads(out.read_text(encoding="utf8"))["locations"][0]
                self.assertEqual(second,first);self.assertFalse(google.should_enrich(second))

if __name__=="__main__":unittest.main()
