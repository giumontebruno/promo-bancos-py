import unittest,tempfile,os,csv,json
from pathlib import Path
from scrapers.bancop_solar_zeta_common import export
class ZetaBlockedInventory(unittest.TestCase):
    def test_empty_blocked_inventory_is_not_successful_coverage(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                export('zeta',[],{'status':'blocked','coverage_complete':False,'reason':'Undated brochure'})
                self.assertEqual(list(csv.DictReader(Path('outputs/zeta_beneficios_por_categoria.csv').read_text(encoding='utf-8-sig').splitlines())),[])
                self.assertEqual(json.loads(Path('outputs/zeta_source_meta.json').read_text())['status'],'blocked')
                with self.assertRaises(RuntimeError):export('solar',[],{'status':'partial','coverage_complete':False})
                with self.assertRaises(RuntimeError):export('zeta',[],{'status':'fetched','coverage_complete':True})
            finally:os.chdir(old)
