import unittest
from scrapers.extract_atlas import supermarket_card_scopes
from promo_backend.normalize import normalize_row
from promo_backend.quality import normalize_terms

class AtlasSupermarketScopesTests(unittest.TestCase):
    def test_monthly_purchase_cap_is_not_a_monthly_minimum(self):
        detail = ('con tarjetas de crédito Mastercard Black, Visa Infinite y Signature delSol ' '15% de reintegro con tarjetas de crédito Clásica y Oro Mínimo de compra para todas las afinidades Gs. 200.000.'
                  'Tope de compra mensual acumulado por cuenta de tarjeta Gs. 1.000.000 '
                  'para tarjetas de crédito Visa Infinite, Mastercard Black y Visa Signature '
                  'y Gs. 700.000 para tarjetas Visa Oro y Visa Clásica. Las transacciones '
                  'deben ser realizadas a través del POS de la Red Infonet. '
                  'Se excluyen las tarjetas prepagas, corporativas, gourmet card, gift card '
                  'y las afinidades Shopping Mariscal, Pinedo y Mariano.')
        row = {'Comercio/Promoción': 'Supermercados', 'Detalle': detail,
               'Cantidad de descuento / beneficio': '20% de reintegro; 15% de reintegro',
               'Vigencia': detail, 'Día de promoción': 'Todos los Viernes',
               'URL detalle': 'https://www.bancoatlas.com.py/web/beneficios'}
        variants = supermarket_card_scopes(row)
        self.assertEqual(len(variants), 2)
        for variant, amount in zip(variants, [1000000, 700000]):
            terms = normalize_terms(normalize_row('Atlas', variant))
            self.assertEqual([(x['kind'], x['amount'], x['period']) for x in terms['limits']],
                             [('minimum', 200000, None), ('purchase', amount, 'mensual')])
            self.assertIsNone(terms['ends_on'])
            self.assertIn('validity_unconfirmed', terms['issues'])
            self.assertIn('POS de la Red Infonet', variant['Detalle'])
            self.assertIn('Shopping Mariscal', variant['Detalle'])
            self.assertEqual(variant['Texto original de la fuente'], detail)
        self.assertEqual(variants[1]['Tarjetas verificadas'], 'Visa Oro y Visa Clásica')
        premium = normalize_row('Atlas', variants[0])
        premium['terms'] = normalize_terms(premium)
        self.assertEqual(premium['verified_cards'], 'Mastercard Black, Visa Infinite y Signature delSol')
        self.assertEqual(premium['terms']['cards'], [premium['verified_cards']])
        import subprocess, json
        script = """const p=JSON.parse(process.argv[1]);
        const adapter=require('./beta-web/supermarket-reviewed.js');
        const engine=require('./beta-web/supermarket-eligibility.js');
        if(adapter.matches(p)) throw Error('Atlas inherited reviewed Familiar proof');
        const result=['Visa Signature','Signature delSol'].map(card=>engine.evaluate(p,
          {dateMatches:true,card,channel:'pos',amount:300000,remainingCap:1000000,
           branch:{match:true,source:p.source_url}}));
        if(result.some(r=>r.status==='applies'||r.estimate!==null)) throw Error('Unreviewed Atlas inferred eligible');
        console.log(JSON.stringify(result.map(r=>r.status)));"""
        output = subprocess.check_output(['node', '-e', script, json.dumps(premium)], text=True)
        self.assertEqual(json.loads(output), ['needs_confirmation', 'needs_confirmation'])
        ambiguous = {**row, 'Detalle': detail.replace('Signature delSol', 'Signature')}
        self.assertEqual(supermarket_card_scopes(ambiguous)[0]['Estado verificacion'], 'unconfirmed')

    def test_missing_clause_is_held_not_guessed(self):
        rows = supermarket_card_scopes({'Comercio/Promoción': 'Supermercados', 'Detalle': 'new terms'})
        self.assertEqual(rows[0]['Estado verificacion'], 'unconfirmed')
