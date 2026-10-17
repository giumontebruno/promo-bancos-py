import json
import unittest
from scrapers.itau_reviewed_scopes import MANIFEST, reviewed_scopes, source_hash
from promo_backend.normalize import normalize_row
from promo_backend.quality import normalize_terms


class ItauReviewedScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviews = json.loads(MANIFEST.read_text(encoding='utf8'))

    def test_changed_source_is_withheld(self):
        row={'URL detalle':'example','Detalle':'20%','Vigencia':'2026'}
        review={'example':{'sha256':source_hash(row),'variants':[{'Variante':'a'}]}}
        changed={**row,'Detalle':'30%'}
        result=reviewed_scopes(changed,review)
        self.assertEqual(result[0]['Estado verificacion'],'unconfirmed')
        self.assertNotIn('Variante',result[0])
        self.assertIn('30%',result[0]['Texto original de la fuente'])

    def test_gastronomy_schedule_and_caps(self):
        gastro={u:r for u,r in self.reviews.items() if 'b=16016&' in u}
        self.assertEqual(len(gastro),10)
        for url,review in gastro.items():
            self.assertEqual([v['Porcentaje efectivo'] for v in review['variants']],['20','25'])
            expected='martes a viernes' if 'c=32010' in url else 'martes a sábados'
            self.assertTrue(all(v['Día de promoción']==expected for v in review['variants']))
            self.assertNotIn('BROTZEIT:',review['variants'][0]['Detalle'])

    def test_each_variant_has_single_purchase_cap(self):
        count=0
        for url,review in self.reviews.items():
            for variant in review['variants']:
                row={**variant,'URL detalle':url,'Comercio/Promoción':'test'}
                terms=normalize_terms(normalize_row('Itaú',row))
                limits=[x for x in terms['limits'] if x['kind']=='purchase']
                self.assertEqual(len(limits),1,(url,variant['Variante'],terms))
                self.assertTrue(terms['ends_on'])
                self.assertFalse(terms['conflicting_dates'])
                count+=1
        self.assertEqual(count,34)

    def test_salemma_does_not_add_cash_discount_to_rebate(self):
        review=next(r for u,r in self.reviews.items() if 'b=15536&' in u)
        self.assertEqual([v['Porcentaje efectivo'] for v in review['variants']],['20','15','15','15'])
        self.assertTrue(all('10% de descuento en caja' in v['Detalle'] for v in review['variants']))
        self.assertTrue(all('OCHSI' in v['Detalle'] for v in review['variants']))

    def test_explicit_detail_dates_and_shell_exclusion(self):
        for b,start in [('16584','2026-03-07'),('16914','2026-02-23')]:
            review=next(r for u,r in self.reviews.items() if f'b={b}&' in u)
            for v in review['variants']:
                terms=normalize_terms(normalize_row('Itaú',{**v,'Comercio/Promoción':'test'}))
                self.assertEqual(terms['starts_on'],start)
                if b=='16914':
                    self.assertIn('No aplica a PERSONAL BANK',v['Detalle'])
                    self.assertNotIn('PERSONAL BANK',v['Tarjetas verificadas'])

    def test_conflicting_fashion_sources_are_not_expanded(self):
        pending=[r for r in self.reviews.values() if r.get('pending')]
        self.assertEqual(len(pending),3)
        for review in pending:
            self.assertEqual(review['variants'],[])
            self.assertIn('5%',review['pending'])
            self.assertIn('10%',review['pending'])
