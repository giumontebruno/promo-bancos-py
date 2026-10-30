import json,unittest
from scrapers.extract_solar import build,REVIEWS,coverage
from pathlib import Path
FIX=Path(__file__).parent/'fixtures/solar_reviewed_catalog.json'
class SolarReviewed(unittest.TestCase):
 def setUp(self):
  self.promos=json.loads(FIX.read_text());self.terms={p['id']:{'text':'Reviewed source fixture','sha256':REVIEWS[p['id']]['pdf_sha256']} for p in self.promos}
 def test_full_review(self):
  rows,skip=build(self.promos,self.terms,'2026-10-30');self.assertEqual(len(rows),69);self.assertEqual(len(skip),7)
  meta=coverage(self.promos,rows,skip);self.assertEqual(meta['catalog_reviewed'],30);self.assertTrue(meta['catalog_review_complete']);self.assertFalse(meta['coverage_complete'])
  self.assertTrue(all(r['Estado verificacion']=='official_document' for r in rows))
 def test_pdf_year_and_installments_recovery(self):
  rows,_=build(self.promos,self.terms,'2026-10-30');quanta=next(r for r in rows if r['Variante']=='125-classic');nova=next(r for r in rows if r['Variante']=='121-classic')
  self.assertIn('2026-09-07',quanta['Vigencia']);self.assertIn('Hasta 6 cuotas',nova['Cantidad de descuento / beneficio']);self.assertIn('conjunto',nova['Montos / topes'])
 def test_card_and_period_scopes(self):
  rows,_=build(self.promos,self.terms,'2026-10-30');by={r['Variante']:r for r in rows}
  self.assertIn('Smart MasterCard',by['101-classic']['Tarjetas verificadas']);self.assertNotIn('Visa',by['101-classic']['Tarjetas verificadas'])
  self.assertIn('no especificado',by['104-classic']['Montos / topes']);self.assertIn('durante la vigencia',by['119-classic']['Montos / topes']);self.assertIn('1.500.000',by['93-classic']['Montos / topes'])
 def test_changed_pdf_or_record_fails_closed(self):
  p=next(p for p in self.promos if p['id']==125);self.terms[125]['sha256']='changed';self.assertEqual(build([p],self.terms,'2026-10-30')[0],[])
  self.terms[125]['sha256']=REVIEWS[125]['pdf_sha256'];p['duration']='2026-01-01';self.assertEqual(build([p],self.terms,'2026-10-30')[0],[])
 def test_expiry_and_specific_holds(self):
  rows,skip=build(self.promos,self.terms,'2028-01-01');self.assertEqual(rows,[]);self.assertTrue(all(s['reason']=='expired' for s in skip))
  _,skip=build(self.promos,self.terms,'2026-10-30');by={s['id']:s['reason'] for s in skip};self.assertIn('Popeyes',by[118]);self.assertIn('2027',by[123]);self.assertIn('producto',by[134])
 def test_source_to_normalized_financial_terms(self):
  from promo_backend.normalize import normalize_row
  from promo_backend.quality import normalize_terms
  rows,_=build(self.promos,self.terms,'2026-10-30')
  for row in rows:
   campaign,tier=row['Variante'].split('-');review=REVIEWS[int(campaign)];index=['classic','gold','premium'].index(tier)
   promo=normalize_row('Solar',row);terms=normalize_terms(promo)
   self.assertEqual(promo['source_verification'],'official_document')
   self.assertEqual(terms['starts_on'],review['pdf_start']);self.assertEqual(terms['ends_on'],review['pdf_end'])
   limits=terms['limits'];amount=review['purchase_cap_pyg'][index]
   if amount is None:self.assertEqual(limits,[])
   else:
    self.assertEqual(len(limits),1);self.assertEqual(limits[0]['kind'],'purchase');self.assertEqual(limits[0]['amount'],amount)
    self.assertEqual(limits[0]['period'],'mensual' if review['cap_period']=='monthly' else None)
   self.assertEqual(terms['cards'],[review['cards'][index]])
   if campaign=='101':
    self.assertEqual(review['cap_scope'],'unspecified')
    self.assertNotIn('Por cuenta de tarjeta',row['Montos / topes'])
    self.assertNotIn('incluyendo titular y adicionales',row['Detalle'])
    self.assertEqual(review['purchase_cap_pyg'],[500000,700000,1000000])
    self.assertIn('Primera compra',promo['day_text']);self.assertIn('primera',promo['raw_detail'].lower());self.assertNotIn('Todos los días',promo['day_text'])
   if campaign in ('119','121'):self.assertIn('durante la vigencia',limits[0]['evidence'])
   # Source verification is not a calculator audit. Do not fabricate pilot evidence.
   self.assertFalse(promo.get('review_evidence'))
if __name__=='__main__':unittest.main()
