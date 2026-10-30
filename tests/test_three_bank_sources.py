import json, unittest
from scrapers.extract_solar import REVIEWED_NISSEI
from pathlib import Path
from scrapers.extract_solar import build as solar_build, dates, catalog as solar_catalog
from scrapers.extract_bancop import build as bancop_build, catalog as bancop_catalog, REVIEWED_PDF_HASHES, REVIEW_FILE
REVIEWS=json.loads(REVIEW_FILE.read_text())["entries"]
from scrapers.bancop_solar_zeta_common import fetch
FIX=Path(__file__).parent/'fixtures/three_banks'
class ThreeBankSources(unittest.TestCase):
    def test_shared_month_range(self):
        self.assertEqual(dates('02 al 04 de noviembre del 2026'),('2026-11-02','2026-11-04'))
        self.assertEqual(dates('Del 31 de octubre al 1 de noviembre de 2026'),('2026-10-31','2026-11-01'))
        self.assertEqual(dates('07 de Septiembre al 31 de Diciembre'),(None,None))
    def test_solar_expired_and_undated_excluded(self):
        promos=json.loads((FIX/'solar.json').read_text());terms={p['id']:{'url':'https://api.solar.com.py/example.pdf','text':'Bases fixture'} for p in promos}
        rows,skips=solar_build(promos,terms,'2026-10-30')
        self.assertEqual(rows,[])
        self.assertTrue(all(x['reason']=='source_changed_requires_review' for x in skips))
    def test_reviewed_nissei_requires_pdf_and_record_hash(self):
        p=next(x for x in json.loads((FIX/'solar.json').read_text()) if x['id']==132)
        term={132:{'url':'https://api.solar.com.py/example.pdf','text':'Bases fixture','sha256':REVIEWED_NISSEI['pdf']}}
        rows,_=solar_build([p],term,'2026-10-30')
        self.assertTrue(all(x['Estado verificacion']=='official_document' for x in rows))
        self.assertIn('Hasta 18 cuotas',rows[0]['Cantidad de descuento / beneficio'])
        p['classic_refund']='99%'
        rows,_=solar_build([p],term,'2026-10-30')
        self.assertEqual(rows,[])
    def test_bancop_scopes_and_hash_gate(self):
        text=(FIX/'bancop-526.txt').read_text();c={'id':'526','title':'BIGGIE EXPRESS'}
        rows,reason=bancop_build(c,text,REVIEWS['526']['source_url'],REVIEWED_PDF_HASHES['526'],'2026-10-30')
        self.assertIsNone(reason);self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['Cantidad de descuento / beneficio'],'20% de reintegro')
        self.assertEqual(rows[1]['Cantidad de descuento / beneficio'],'25% de reintegro')
        self.assertNotIn('250.000',rows[0]['Montos / topes'])
        self.assertIn('800.000',rows[0]['Montos / topes'])
        self.assertEqual(rows[0]['Estado verificacion'],'verified')
        changed,reason=bancop_build(c,text,REVIEWS['526']['source_url'],'changed','2026-10-30')
        self.assertEqual(changed,[])
        self.assertEqual(reason,'source_changed_requires_review')
    def test_future_bancop_stays_future(self):
        rows,_=bancop_build({'id':'550','title':REVIEWS['550']['title']},(FIX/'bancop-550.txt').read_text(),REVIEWS['550']['source_url'],REVIEWS['550']['pdf_sha256'],today='2026-10-30')
        self.assertEqual(rows[0]['Vigencia'],'Desde 2026-10-31 hasta 2026-11-01')
        self.assertIn('Empresariales',rows[0]['Detalle'])
    def test_expired_bancop_not_imported(self):
        rows,reason=bancop_build({'id':'526','title':REVIEWS['526']['title']},(FIX/'bancop-526.txt').read_text(),REVIEWS['526']['source_url'],REVIEWS['526']['pdf_sha256'],today='2027-04-01')
        self.assertEqual(rows,[]);self.assertEqual(reason,'expired')
    def test_unknown_catalog_and_url_fail_closed(self):
        for fn in [solar_catalog,bancop_catalog]:
            with self.assertRaises(ValueError):fn('<html>No data</html>')
        with self.assertRaises(ValueError):fetch('https://example.com/test.pdf')
    def test_bancop_modal_duplicates_removed(self):
        html='<a data-target="#promo" data-id="526" data-title="Biggie"></a>'
        self.assertEqual(len(bancop_catalog(html+html)),1)
if __name__=='__main__':unittest.main()
