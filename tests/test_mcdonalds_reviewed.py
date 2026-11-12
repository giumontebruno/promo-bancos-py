import unittest
from pathlib import Path
from datetime import date
from scrapers.extract_interfisa import parse
from promo_backend.normalize import normalize_row

class McDonaldsInterfisa(unittest.TestCase):
    def test_name_punctuation_and_optional_points_section(self):
        text=(Path(__file__).parent/'fixtures/basa_interfisa/interfisa-mcdonalds.txt').read_text(encoding='utf-8')
        item={'name':"MC DONALD'S",'url':'https://www.interfisa.com.py/storage/app/media/PDF%20PROMOCIONES/BYC_Mcdonalds.pdf','category':'Gastronomía'}
        rows,status=parse(item,text,date(2026,11,12))
        self.assertEqual(status,'published');self.assertEqual(len(rows),2)
        for row,rate,cap in zip(rows,[25,30],['250.000','300.000']):
            self.assertEqual(row['Cantidad de descuento / beneficio'],f'{rate}% de reintegro')
            self.assertIn(cap,row['Montos / topes'])
            self.assertIn('adicionales',row['Detalle'])
            self.assertIn('Bancard',row['Detalle'])
            self.assertIn('Empresariales',row['Detalle'])
            self.assertIn('PLAZA NORTE',row['Locales'])
            self.assertNotIn('Interpuntos',row['Locales'])
            self.assertNotIn('Todas las sucursales',row['Locales'])
            p=normalize_row('Interfisa',row)
            self.assertEqual(len(p['promotion_days']),7)
            self.assertIn('2027-06-01',p['validity'])
        wrong,_=parse({**item,'name':'Burger King'},text,date(2026,11,12))
        self.assertEqual(wrong,[])

class McDonaldsFamiliar(unittest.TestCase):
    def test_three_locations_two_tiers_and_fail_closed(self):
        import json
        from scrapers.familiar_gastro_reviewed import build
        source=json.loads((Path(__file__).resolve().parents[1]/'outputs/familiar_extraction_review.json').read_text(encoding='utf-8'))
        rows=[]
        for record in source['records']:
            result=build(record)
            if result is None:continue
            self.assertEqual(len(result),2)
            with self.assertRaises(ValueError):build({**record,'pdf_sha256':'changed'})
            with self.assertRaises(ValueError):build({**record,'terms_text':'changed'})
            rows+=result
        self.assertEqual(len(rows),6)
        self.assertEqual(len({r['Comercio'] for r in rows}),3)
        self.assertEqual({r['Beneficio'] for r in rows},{'25% de reintegro','20% de reintegro'})
        for r in rows:
            self.assertIn('Sólo McDonald',r['Locales'])
            self.assertIn('500.000',r['Montos'])
            self.assertIn('por tarjeta',r['Montos'])
            self.assertIn('No asumir un cupo adicional',r['Detalle'])
            self.assertIn('Bancard',r['Detalle'])
            self.assertEqual(len(normalize_row('Familiar',r)['promotion_days']),5)
