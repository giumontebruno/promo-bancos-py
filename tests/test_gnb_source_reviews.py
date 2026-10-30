import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from scrapers import build_gnb_live_offers as live

class GnbSourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.cards=json.loads((Path(__file__).parent/'fixtures/gnb-source-review-20261030.json').read_text())
        self.reviews=live.source_reviews()
    def test_review_is_bound_to_semantics_not_only_id(self):
        for card in self.cards:
            self.assertIsNotNone(live.matched_review(card,self.reviews))
            for field in ['title','startDate','endDate','miniDescription','lines','termsUrl']:
                changed=copy.deepcopy(card);changed[field]='changed'
                self.assertIsNone(live.matched_review(changed,self.reviews),field)
    def test_sweepstakes_has_no_guaranteed_discount(self):
        card=next(c for c in self.cards if c['id']==688)
        review=live.matched_review(card,self.reviews)
        self.assertEqual(review['exclude_reason'],'excluded_sweepstakes_not_discount')
        self.assertNotIn('percent',review)
    def test_geox_review_preserves_restricted_window(self):
        card=next(c for c in self.cards if c['id']==74)
        review=live.matched_review(card,self.reviews)
        self.assertEqual(review['validity'],'Desde 2026-10-29 hasta 2026-11-01')
        self.assertIn('2025-10-10',review['warning'])
    def test_changed_document_blocks_reuse_even_when_url_is_same(self):
        from scrapers import build_gnb_reviewed as builder
        class Response:
            content=b'%PDF-changed terms'
            def raise_for_status(self): pass
        with patch.object(builder.requests,'get',return_value=Response()):
            with self.assertRaisesRegex(ValueError,'reviewed terms changed'):
                builder.verify_review_documents(self.cards)
    def test_unknown_card_does_not_download_arbitrary_documents(self):
        from scrapers import build_gnb_reviewed as builder
        with patch.object(builder.requests,'get') as get:
            self.assertEqual(builder.verify_review_documents([{'id':999}]),[])
            get.assert_not_called()
    def test_real_fixture_build_excludes_prize_and_limits_geox_dates(self):
        import tempfile,csv
        reviews=json.loads((Path(__file__).parent/'fixtures/gnb-source-review-rows-20261030.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            cards_path=Path(tmp)/'cards.json';review_path=Path(tmp)/'review.csv'
            cards_path.write_text(json.dumps({'cards':self.cards}))
            with review_path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(reviews[0]));w.writeheader();w.writerows(reviews)
            with patch.object(live,'CARDS',cards_path),patch.object(live,'REVIEW',review_path):
                rows,issues=live.build_rows()
            self.assertEqual(len(rows),2)
            self.assertEqual(issues[0]['reason'],'excluded_sweepstakes_not_discount')
            for row in rows:
                self.assertEqual(row['Comercio'],'Geox')
                self.assertEqual(row['Vigencia'],'Desde 2026-10-29 hasta 2026-11-01')
                self.assertEqual(row['Dia'],'Todos los días')
                self.assertEqual(row['Montos'],'')
                self.assertEqual(row['Locales'],'Geox')
                self.assertIn('No participan',row['Detalle'])
    def test_tonina_conflicting_cap_is_not_chosen(self):
        import tempfile,csv
        card=json.loads((Path(__file__).parent/'fixtures/gnb-tonina-source-20261030.json').read_text())
        decision=live.matched_review(card,self.reviews)
        self.assertTrue(decision['cap_conflict'])
        # Exact reviewed fixture; current API is not needed for this regression.
        review={'ID GNB':'52','URL bases':card['termsUrl'],'Condiciones PDF':'',
                'Beneficio PDF':'','Vigencia PDF':''}
        with tempfile.TemporaryDirectory() as tmp:
            cp=Path(tmp)/'cards.json';rp=Path(tmp)/'review.csv'
            cp.write_text(json.dumps({'cards':[card]}))
            with rp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(review));w.writeheader();w.writerow(review)
            with patch.object(live,'CARDS',cp),patch.object(live,'REVIEW',rp):
                rows,issues=live.build_rows()
            self.assertEqual(len(rows),2)
            discount=next(r for r in rows if '20%' in r['Beneficio'])
            self.assertEqual(discount['Estado verificacion'],'unconfirmed')
            self.assertEqual(discount['Montos'],'')
            self.assertNotIn('100.000',discount['Detalle'])
            self.assertNotIn('50.000',discount['Detalle'])
            self.assertIn('50.000',discount['Advertencia de fuente'])
            self.assertIn('100.000',discount['Advertencia de fuente'])
            self.assertEqual(discount['Dia'],'miércoles')
