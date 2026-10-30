import json,unittest
from scrapers.extract_bancop import REVIEW_FILE,build
D=json.loads(REVIEW_FILE.read_text())['entries']
class BancopReviewedCatalog(unittest.TestCase):
    def test_every_discovered_card_has_decision(self):
        self.assertEqual(len(D),58)
        self.assertEqual(sum(e['status']=='verified' for e in D.values()),52)
        self.assertTrue(all(e['rows'] or e['reason'] for e in D.values()))
    def test_live_hash_gate_all_records(self):
        rows=[]
        for e in D.values():
            result,reason=build({'id':e['id'],'title':e['title']},'',e['source_url'],e['pdf_sha256'],'2026-10-30')
            rows+=result
            if e['status']=='blocked':self.assertEqual(reason,e['reason'])
            changed,_=build({'id':e['id'],'title':e['title']},'',e['source_url'],'different','2026-10-30')
            self.assertEqual(changed,[])
        self.assertEqual(len(rows),68)
    def test_neuland_merchant_scope_not_mixed(self):
        library=D['457']['rows'][0]
        self.assertEqual(library['Cantidad de descuento / beneficio'],'15% de reintegro')
        self.assertNotIn('25%',library['Detalle'])
        self.assertNotIn('Del reintegro se excluyen',library['Detalle'])
        supermarket=D['456']['rows']
        self.assertEqual(len(supermarket),2)
        self.assertTrue(all('Del reintegro se excluyen' in r['Detalle'] for r in supermarket))
        self.assertEqual(D['457']['rows'][1]['Comercio/Promoción'],'Minishop Neuland')
    def test_nissei_wrong_merchant_quarantined(self):
        self.assertEqual(D['487']['status'],'blocked')
        self.assertIn('Visuar',D['487']['reason'])
    def test_missing_year_never_assumed(self):
        for i in ['539','544','543','547','541']:
            self.assertFalse(D[i]['rows']);self.assertIn('año',D[i]['reason'])
    def test_product_and_channel_qualifiers(self):
        self.assertIn('Hasta 20%',D['505']['rows'][0]['Cantidad de descuento / beneficio'])
        self.assertIn('según modelo',D['505']['rows'][0]['Cantidad de descuento / beneficio'])
        self.assertIn('comisión',D['495']['rows'][0]['Cantidad de descuento / beneficio'])
        self.assertIn('No delivery',D['527']['rows'][0]['Detalle'])
        self.assertIn('por mes',D['516']['rows'][0]['Montos / topes'])
        self.assertNotIn('Encarnación',D['515']['rows'][0]['Locales'])
    def test_finance_not_cashback(self):
        for i in ['472','469','491','546','549','486','512','548','489','531','488','538','503','504','495','496']:
            self.assertTrue(all('%' not in r['Cantidad de descuento / beneficio'] for r in D[i]['rows']))
if __name__=='__main__':unittest.main()
