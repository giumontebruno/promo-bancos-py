import json,re,unittest
from scrapers.extract_bancop import REVIEW_FILE
from promo_backend.normalize import normalize_row
from promo_backend.quality import normalize_terms
D=json.loads(REVIEW_FILE.read_text())['entries']
class BancopCurrencySerialization(unittest.TestCase):
    def test_all_23_explicit_same_clause_currencies_survive_normalization(self):
        changed=[]
        for entry in D.values():
            for row in entry['rows']:
                if not row.get('Justificación unidad normalizada'):continue
                changed.append(row)
                self.assertRegex(row['Detalle'],r'[Tt]ope(?: de)? reintegro\s+Gs\.?\s*\d')
                amount=re.search(r'[Tt]ope (?:de )?compra\s*:?\s*Gs\.\s*(\d[\d.]*)',row['Montos / topes'])[1].rstrip('.')
                purchase=[v for v in normalize_terms(normalize_row('Bancop',row))['limits'] if v['kind']=='purchase']
                self.assertEqual(len(purchase),1,row['Variante'])
                self.assertEqual(purchase[0]['amount'],int(amount.replace('.','')),row['Variante'])
                self.assertEqual(purchase[0]['currency'],'PYG')
        self.assertEqual(len(changed),23)
    def test_pedidosya_raw_and_amount_preserved(self):
        row=D['468']['rows'][0]
        self.assertIn('Tope de compra 250.000',row['Detalle'])
        self.assertIn('Tope de compra 250.000',D['468']['source_text'])
        self.assertIn('Tope de compra Gs. 250.000',row['Montos / topes'])
        limits=normalize_terms(normalize_row('Bancop',row))['limits']
        self.assertEqual({v['kind']:v['amount'] for v in limits},{'refund':50000,'purchase':250000})
    def test_explicit_period_not_propagated_to_refund(self):
        # Currency canonicalization must not inject periods into a different clause.
        caps=D['468']['rows'][0]['Montos / topes']
        self.assertEqual(caps,'Tope reintegro Gs 50.000. Tope de compra Gs. 250.000 por mes, por tarjeta.')
        self.assertNotIn('por mes',caps.split('Tope de compra')[0])
if __name__=='__main__':unittest.main()
