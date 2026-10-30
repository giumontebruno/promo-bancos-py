import csv
import json
import re
import unittest
from pathlib import Path
from scrapers.familiar_offers import split_offers
from scrapers.build_familiar_table import convert
from promo_backend.normalize import normalize_row
from promo_backend.quality import deduplicate

ROOT = Path(__file__).resolve().parents[1]

class FamiliarOfferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Independent fixture captured before regeneration.
        records = json.loads((ROOT / 'outputs/familiar_extraction_review.json').read_text())['records']
        cls.rows = {}
        for record in records:
            try:
                row = convert(record)
                cls.rows[row['Comercio']] = row
            except ValueError:
                continue

    def normalized(self,name):
        return deduplicate([normalize_row('Familiar',r) for r in split_offers(self.rows[name])])[0]

    def test_don_town_exact_eligibility_caps(self):
        rows=self.normalized('DON TOWN')
        self.assertEqual([r['percentages'] for r in rows],[['25%'],['20%']])
        self.assertEqual([r['terms']['limits'][0]['amount'] for r in rows],[800000,600000])
        self.assertEqual([r['offer_kind'] for r in rows],['premium','base'])
        self.assertEqual(rows[0]['verified_cards'],'Visa Platinum')
        self.assertNotIn('Platinum',rows[1]['verified_cards'])
        self.assertNotIn('20%',rows[0]['raw_detail'])
        self.assertNotIn('25%',rows[1]['raw_detail'])
        self.assertIn('en conjunto',rows[0]['raw_detail'])
        self.assertTrue(all(r['terms']['exclusions'] for r in rows))
        self.assertTrue(all(r['terms']['ends_on']=='2026-12-31' for r in rows))

    def test_parana_money_and_daily_financing(self):
        rows=self.normalized('PARANÁ HOGAR')
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]['percentages'],['30%'])
        self.assertEqual(rows[0]['promotion_days'],['miércoles'])
        self.assertEqual({x['kind']:x['amount'] for x in rows[0]['terms']['limits']},{'purchase':10000000,'refund':3000000})
        self.assertNotIn('InterExa',rows[0]['verified_cards'])
        for row in rows[1:]:
            self.assertEqual(row['benefit_type'],'cuotas_sin_intereses')
            self.assertEqual(row['terms']['limits'],[])
            self.assertEqual(row['percentages'],[])
            self.assertEqual(len(row['promotion_days']),7)
            self.assertNotIn('3.000.000',row['raw_detail'])

    def test_cycles_keeps_cap_after_financing_sentence(self):
        rows=self.normalized('CYCLES SHOP')
        cash=next(r for r in rows if r['percentages'])
        self.assertEqual({x['amount'] for x in cash['terms']['limits']},{5000000})

    def test_alternative_network_wording_is_preserved(self):
        for name in ['MILORD','EL FARO RESORT','MBURUCUYA HOTEL BOUTIQUE','DEL BOSQUE ROGA','CONCEPCION PALACE','PALMAROGA','FERMACO']:
            for row in self.normalized(name):
                self.assertIn('bancard',row['raw_detail'].lower(),name)

    def test_each_installment_keeps_its_own_schedule(self):
        source=dict(self.rows['PANDOLFO'])
        source['Detalle']=source['Detalle'].replace('cuotas sin intereses, todos los días.', 'cuotas sin intereses, sólo los lunes.',1)
        rows=split_offers(source)
        installments=[r for r in rows if r.get('Tipo de beneficio verificado')=='cuotas_sin_intereses']
        self.assertEqual(installments[0]['Dia'],'sólo los lunes')
        self.assertEqual(installments[1]['Dia'],'todos los días')

    def test_installment_schedule_preserves_day_lists_and_ranges(self):
        for schedule in ['todos los lunes y miércoles','sólo los lunes y viernes','de lunes a viernes']:
            source=dict(self.rows['PANDOLFO'])
            source['Detalle']=source['Detalle'].replace('cuotas sin intereses, todos los días.', 'cuotas sin intereses, '+schedule+'.',1)
            installments=[r for r in split_offers(source) if r.get('Tipo de beneficio verificado')=='cuotas_sin_intereses']
            self.assertEqual(installments[0]['Dia'],schedule)
            self.assertEqual(installments[1]['Dia'],'todos los días')

    def test_common_cashback_evidence_does_not_reinsert_other_financing(self):
        for name in ['PANDOLFO','PANDOLFO PREMIUM','PARANÁ HOGAR','AMERICA SHOP']:
            row=next(r for r in self.normalized(name) if r['percentages'])
            self.assertNotIn('cuotas sin intereses',row['raw_detail'],name)
            keys=[(x['kind'],x['amount']) for x in row['terms']['limits']]
            self.assertEqual(len(keys),len(set(keys)),name)

    def test_biggie_gold_and_platinum_cannot_merge(self):
        rows=self.normalized('BIGGIE')
        self.assertEqual([r['percentages'] for r in rows],[['20%'],['25%'],['25%']])
        self.assertEqual([r['terms']['limits'][0]['amount'] for r in rows],[1000000,1000000,1500000])
        self.assertEqual(len(set(r['id'] for r in rows)),3)

    def test_qr_stays_conditional_and_shared(self):
        rows=self.normalized('CEROGRADO-PLAZA NORTE')
        self.assertEqual(len(rows),2)
        self.assertEqual([r['percentages'] for r in rows],[['20%','5%'],['25%','5%']])
        for row in rows:
            self.assertIn('aplicación de Banco Familiar',row['benefit_summary'])
            self.assertIn('Martes Mariscal',row['raw_detail'])
            self.assertEqual(row['terms']['limits'][0]['amount'],10000000)
            self.assertEqual(row['ordinal_weekdays'],[{'ordinal':1,'day':'martes'}])

    def test_three_tiers_and_no_duplicate_common_financing(self):
        rows=self.normalized('LAS HORTENSIAS HOTEL')
        self.assertEqual([r['percentages'] for r in rows],[['30%'],['25%'],['20%'],[]])
        rows=self.normalized('JACK & JONES')
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[-1]['percentages'],[])
        self.assertEqual(len(rows[-1]['promotion_days']),7)

    def test_ambiguous_additive_benefits_stay_in_review(self):
        with self.assertRaisesRegex(ValueError,'complex_monetary'):
            split_offers(self.rows['OPTICA SANTA LUCIA'])

    def test_all_supported_rows_normalize_and_have_stable_ids(self):
        count=0
        for name,row in self.rows.items():
            if name=='OPTICA SANTA LUCIA':continue
            first=split_offers(row)
            normalized=[normalize_row('Familiar',r) for r in first]
            self.assertEqual(len({r['id'] for r in normalized}),len(normalized),name)
            self.assertEqual([r['id'] for r in normalized],[normalize_row('Familiar',r)['id'] for r in split_offers(row)])
            if len(first)>1:
                self.assertTrue(all(r.get('campaign_id') for r in normalized),name)
                self.assertEqual(len({r['campaign_id'] for r in normalized}),1,name)
            count+=len(first)
        # Compare with the independently published snapshot, not yesterday's live count.
        # Santa Lucia has one separately reviewed complex benefit and is deliberately excluded above.
        metadata=json.loads((ROOT/'outputs/familiar_source_meta.json').read_text(encoding='utf8'))
        with (ROOT/'outputs/familiar_beneficios_por_categoria.csv').open(encoding='utf-8-sig') as handle:
            published=list(csv.DictReader(handle))
        complex_rows=[r for r in published if r.get('Comercio')=='OPTICA SANTA LUCIA']
        self.assertEqual(len(complex_rows),1)
        retained=metadata.get('retained_historical_rows',0)
        self.assertEqual(len(published),metadata.get('exported_rows',metadata['published']))
        self.assertEqual(len(published),metadata['published']+retained)
        self.assertGreaterEqual(sum(r.get('Estado verificacion')=='unconfirmed' for r in published),retained)
        self.assertEqual(count,metadata['published']-len(complex_rows))

if __name__=='__main__':unittest.main()

class CopetrolCapTests(unittest.TestCase):
    def test_caps_scoped_to_cards_and_network_is_retained(self):
        from promo_backend.quality import normalize_terms
        row = {'Comercio': 'COPETROL', 'URL detalle': 'https://www.familiar.com.py/pdfs/promocionesybeneficios-copetrol-bases-y-condiciones',
               'Detalle': 'Los clientes recibirán 20% de reintegro en el extracto. Límite de compra mensual por tarjeta Gs. 600.000 para las tarjetas de crédito Visa Platinum y 400.000 para las tarjetas de crédito Visa o MasterCard Oro/Gold, Visa o Mastercard Clásica, Positiva Visa, Positiva Bancardcheck. *Los límites de compra se aplican en conjunto para todas las estaciones de servicio adheridas a la promoción “Estaciones de servicio”. *La PROMOCIÓN será válida únicamente cuando los pagos fueren hechos a través de POS Infonet/Bancard y la APP Copetrol.*',
               'Beneficio': '20% de reintegro', 'Tarjetas verificadas': 'old unsplit cards', 'Dia': 'los días martes', 'Vigencia': 'Desde 2026-01-06 hasta 2026-12-29'}
        variants = split_offers(row)
        self.assertEqual(len(variants), 2)
        for variant, amount in zip(variants, [600000, 400000]):
            terms = normalize_terms(normalize_row('Familiar', variant))
            self.assertEqual([(x['amount'], x['period']) for x in terms['limits']], [(amount, 'mensual')])
            self.assertIn('APP Copetrol', variant['Detalle'])
            self.assertIn('en conjunto', variant['Detalle'])
            self.assertEqual(variant['Texto original de la fuente'], row['Detalle'])
        self.assertEqual(variants[0]['Tarjetas verificadas'], 'Visa Platinum')
        self.assertNotIn('Platinum', variants[1]['Tarjetas verificadas'])
