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
            evidence, failures = builder.verify_review_documents(self.cards)
            self.assertEqual(evidence, [])
            self.assertEqual({f['id'] for f in failures}, {c['id'] for c in self.cards})
            self.assertTrue(all(f['reason'] == 'reviewed_terms_changed' for f in failures))
    def test_unknown_card_does_not_download_arbitrary_documents(self):
        from scrapers import build_gnb_reviewed as builder
        with patch.object(builder.requests,'get') as get:
            self.assertEqual(builder.verify_review_documents([{'id':999}]),([], []))
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

    def test_denied_document_does_not_abort_other_exact_review(self):
        import hashlib,requests
        from scrapers import build_gnb_reviewed as builder
        cards=self.cards
        reviews=copy.deepcopy(self.reviews)
        body=b'%PDF-fixture approved terms'
        for decision in reviews: decision['pdf_sha256']=hashlib.sha256(body).hexdigest()
        class Response:
            content=body
            def raise_for_status(self): pass
        denied=requests.Response();denied.status_code=403
        error=requests.HTTPError('403 Forbidden',response=denied)
        with patch.object(builder,'source_reviews',return_value=reviews),patch.object(builder.requests,'get',side_effect=[error,Response()]) as get:
            evidence,failures=builder.verify_review_documents(cards)
        self.assertEqual(get.call_count,2)
        self.assertEqual([f['id'] for f in failures],[cards[0]['id']])
        self.assertEqual(failures[0]['http_status'],403)
        self.assertEqual(failures[0]['reason'],'document_fetch_failed')
        self.assertEqual([e['id'] for e in evidence],[cards[1]['id']])
        self.assertNotIn('checked_at',failures[0])

    def test_failed_lottery_is_omitted_and_geox_survives(self):
        import tempfile,csv
        reviews=json.loads((Path(__file__).parent/'fixtures/gnb-source-review-rows-20261030.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            cp=Path(tmp)/'cards.json';rp=Path(tmp)/'review.csv'
            cp.write_text(json.dumps({'cards':self.cards}))
            with rp.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(reviews[0]));w.writeheader();w.writerows(reviews)
            with patch.object(live,'CARDS',cp),patch.object(live,'REVIEW',rp):
                rows,issues=live.build_rows(blocked_card_ids={688})
                held_rows,held_issues=live.build_rows(blocked_card_ids={74})
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r['Comercio']=='Geox' for r in rows))
            self.assertEqual(issues[0]['id'],688)
            self.assertEqual(issues[0]['reason'],'review_document_unverified')
            self.assertEqual(held_rows,[])
            self.assertTrue(any(i['id']==688 and i['reason']=='excluded_sweepstakes_not_discount' for i in held_issues))
            self.assertTrue(any(i['id']==74 and i['reason']=='review_document_unverified' for i in held_issues))

    def test_document_failure_is_partial_source_never_fresh_complete(self):
        from promo_backend.run_all import build_source_status
        failure={'id':688,'reason':'document_fetch_failed','http_status':403}
        prior={'checked_at':'2026-10-29T12:00:00Z','last_successful_fetch_at':'2026-10-29T12:00:00Z'}
        status=build_source_status([{'Comercio':'Geox'}],prior,
            meta={'fetch_errors':[failure],'pending':[failure],'coverage_complete':False,'status':'partial'},now='2026-10-30T18:00:00Z')
        self.assertEqual(status['status'],'partial')
        self.assertEqual(status['retrieval_status'],'partial')
        self.assertFalse(status['coverage_complete'])
        self.assertEqual(status['last_successful_fetch_at'],prior['last_successful_fetch_at'])
        self.assertEqual(status['pending_items'],1)

    def test_main_publishes_unaffected_rows_with_explicit_failure_metadata(self):
        import tempfile,csv
        from scrapers import build_gnb_reviewed as builder
        failure={'id':688,'reason':'document_fetch_failed','http_status':403,
                 'source_url':'https://example.invalid/review.pdf'}
        unaffected={'Comercio':'Una ficha independiente','URL detalle':live.BASE_URL+'999'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'outputs').mkdir()
            (root/'data/gnb_live_cards.json').write_text(json.dumps({'cards':self.cards,'checkedAt':'2026-10-30T17:21:00Z','total':2}))
            for name in ('gnb_reviewed_offers.json','gnb_restaurants_reviewed.json','gnb_additional_reviewed.json','gnb_page_reviewed.json'):
                (root/'data'/name).write_text('{}')
            with patch.object(builder,'ROOT',root),patch.object(builder,'verify_review_documents',return_value=([],[failure])),patch.object(builder,'build',return_value=[]),patch.object(builder,'build_additional',return_value=[]),patch.object(builder,'build_page_campaigns',return_value=[]),patch.object(builder,'build_live_rows',return_value=([unaffected],[{'id':688,'reason':'review_document_unverified'}])) as live_build:
                builder.main()
            live_build.assert_called_once_with(blocked_card_ids={688})
            with (root/'outputs/gnb_beneficios_por_categoria.csv').open(encoding='utf-8-sig') as handle:
                rows=list(csv.DictReader(handle))
            meta=json.loads((root/'outputs/gnb_source_meta.json').read_text())
            self.assertEqual(rows,[unaffected])
            self.assertEqual(meta['document_failures'],[failure])
            self.assertEqual(meta['fetch_errors'],[failure])
            self.assertEqual(meta['status'],'partial')
            self.assertFalse(meta['coverage_complete'])
