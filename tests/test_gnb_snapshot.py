import csv,importlib.util,json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scrapers import build_gnb_live_offers as live
from promo_backend import run_all as runner
cards=[{"id":677,"termsUrl":"https://www.beneficiosbancognb.com.py/terms.pdf"}]
reviews=[{"ID GNB":"684","URL bases":"https://www.beneficiosbancognb.com.py/terms.pdf"}]

class SourceProposalTests(unittest.TestCase):
 def test_missing_and_extra_ids_are_explicit(self):
  with self.assertRaisesRegex(ValueError,r"missing_review=\[677\]; review_only=\[684\]"):
   live.validate_source_pair(cards,reviews)
 def test_reject_duplicate_changed_terms_and_changed_snapshot(self):
  card=cards[0];review={"ID GNB":"677","URL bases":card["termsUrl"],"Fecha snapshot":"old"}
  with self.assertRaisesRegex(ValueError,"duplicate"):live.validate_source_pair([card,card],[review])
  with self.assertRaisesRegex(ValueError,"terms URL mismatch"):
   live.validate_source_pair([card],[{**review,"URL bases":"https://example.invalid/changed.pdf"}])
  with self.assertRaisesRegex(ValueError,"timestamp mismatch"):
   live.validate_source_pair([card],[review],"new")
  self.assertEqual(live.validate_source_pair([card],[review],"old")[677],review)
 def test_builder_checks_before_producing_rows(self):
  with tempfile.TemporaryDirectory() as td:
   cp,rp=Path(td)/"cards.json",Path(td)/"review.csv"
   cp.write_text(json.dumps({"cards":cards}),encoding="utf8")
   with rp.open("w",encoding="utf8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(reviews[0]));writer.writeheader();writer.writerows(reviews)
   with patch.object(live,"CARDS",cp),patch.object(live,"REVIEW",rp):
    with self.assertRaisesRegex(ValueError,"out of sync"):live.build_rows()
 def test_failed_refresh_rolls_back_both_artifacts_and_records_step(self):
  with tempfile.TemporaryDirectory(dir=ROOT/"tests") as td:
   root=Path(td)
   for part in ["data","public","outputs"]:(root/part).mkdir()
   source=root/"data/gnb_live_cards.json";review=root/"outputs/gnb_live_card_review.csv";output=root/"outputs/gnb_beneficios_por_categoria.csv"
   source.write_bytes(b"old cards");review.write_bytes(b"old reviews");output.write_bytes(b"old catalog")
   def fail(script):
    if script=="scrapers/extract_gnb.py":
     source.write_bytes(b"new cards");review.write_bytes(b"new reviews")
     raise subprocess.CalledProcessError(2,["python",script])
   with patch.object(runner,"ROOT",root),patch.object(runner,"run_step",fail),patch.object(sys,"argv",["run_all.py","gnb"]):
    self.assertEqual(runner.main(),1)
   self.assertEqual(source.read_bytes(),b"old cards");self.assertEqual(review.read_bytes(),b"old reviews");self.assertEqual(output.read_bytes(),b"old catalog")
   status=json.loads((root/"public/source_status.json").read_text())["GNB"]
   self.assertEqual(status["failed_step"],"scrapers/extract_gnb.py");self.assertEqual(status["exit_code"],2)
 def test_workflow_preserves_exact_generated_snapshot(self):
  text=(ROOT/".github/workflows/refresh-promotions.yml").read_text()
  line=next(s for s in text.splitlines() if "file_pattern:" in s)
  self.assertIn("data/gnb_live_cards.json",line);self.assertNotIn("data/*.json",line)

if __name__=="__main__":unittest.main()

class ReviewedIdentityTests(unittest.TestCase):
 def test_identity_is_bound_to_exact_source_and_detail(self):
  import hashlib
  from promo_backend.normalize import apply_reviewed_promotion_ids
  promo={'id':'new','bank':'GNB','source_url':'official','raw_detail':'verified'}
  review={'generated_id':'new','stable_id':'old','bank':'GNB','source_url':'official','detail_sha256':hashlib.sha256(b'verified').hexdigest()}
  items=[dict(promo)];apply_reviewed_promotion_ids(items,[review]);self.assertEqual(items[0]['id'],'old')
  for field in ['source_url','bank','raw_detail']:
   items=[{**promo,field:'changed'}];apply_reviewed_promotion_ids(items,[review]);self.assertEqual(items[0]['id'],'new')
