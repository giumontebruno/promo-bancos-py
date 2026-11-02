import csv
import json
import tempfile
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import requests
from scrapers import new_bank_documents as docs


class BasaRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'outputs').mkdir()
        self.url = 'https://www.bancobasa.com.py/test.pdf'
        self.page = 'https://www.bancobasa.com.py/promociones-personas'
        self.now = datetime.now(timezone.utc)
        self.stamp = (self.now - timedelta(hours=2)).isoformat()
        self.item = {'name': 'Merchant', 'url': self.url}
        self.row = {'Banco': 'Basa', 'Comercio/Promoción': 'Merchant', 'URL detalle': self.url,
                    'Estado verificacion': 'official_document', 'SHA256 documento': 'a'*64,
                    'Verificado UTC': self.stamp, 'Vigencia': 'Hasta 2026-12-31'}
        self.previous = {**self.item, 'sha256': 'a'*64, 'fetched_at': self.stamp, 'state': 'published'}
        self.html = f'<div class="promo-grid"><a href="{self.url}">Merchant</a></div>'

    def retain(self, row=None, previous=None, item=None, now=None):
        return docs.retain_verified_rows(item or dict(self.item), [row or self.row],
                                         [previous or self.previous], date(2026, 11, 2), now or self.now)

    def seed(self):
        target = self.root / 'outputs/basa_beneficios_por_categoria.csv'
        with target.open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(self.row)); w.writeheader(); w.writerow(self.row)
        (self.root / 'outputs/basa_source_meta.json').write_text(json.dumps({'documents': [self.previous]}))

    def test_timeout_retains_with_real_provenance_and_partial_status(self):
        self.seed()
        with patch.object(docs, 'ROOT', self.root), patch.object(docs, 'download', side_effect=requests.Timeout('timed out')):
            rows, meta = docs.run('basa', self.page, lambda *args: self.fail('parser must not run'), html=self.html, today=date(2026,11,2))
        self.assertEqual(rows[0]['Verificado UTC'], self.stamp)
        self.assertEqual(meta['retained_rows'], 1)
        self.assertEqual(meta['fetched'], 0)
        self.assertEqual(meta['fetch_errors'], 1)
        self.assertEqual(meta['status'], 'partial')
        retained = meta['documents'][0]
        self.assertNotIn('sha256', retained)
        self.assertEqual(retained['retained_sha256'], 'a'*64)
        self.assertEqual(self.retain(previous=retained, now=self.now + timedelta(hours=73)), [])

    def test_no_expired_unverified_mismatched_or_old_evidence(self):
        for row in [dict(self.row, Vigencia='Hasta 2026-11-01'),
                    {**self.row, 'Estado verificacion': 'unconfirmed'},
                    {**self.row, 'Verificado UTC': ''}, {**self.row, 'SHA256 documento': 'b'*64}]:
            self.assertEqual(self.retain(row=row), [])
        for previous in [dict(self.previous, name='Different'), dict(self.previous, state='review_required: changed'),
                         dict(self.previous, fetched_at=(self.now-timedelta(hours=73)).isoformat()),
                         dict(self.previous, fetched_at=(self.now+timedelta(hours=1)).isoformat())]:
            self.assertEqual(self.retain(previous=previous), [])
        self.assertEqual(self.retain(item={**self.item, 'url': self.url+'?new'}), [])

    def test_document_changed_or_parse_failure_never_retains(self):
        for parser in [lambda *args: ([], 'review_required: previously reviewed document changed'),
                       lambda *args: (_ for _ in ()).throw(ValueError('parse failure'))]:
            self.seed()
            with patch.object(docs, 'ROOT', self.root), patch.object(docs, 'download', return_value=b'%PDF new'), patch.object(docs, 'native_text', return_value='new terms'):
                rows, meta = docs.run('basa', self.page, parser, html=self.html, today=date(2026,11,2))
            self.assertEqual(rows, [])
            self.assertEqual(meta['retained_rows'], 0)
            self.assertTrue(meta['authoritative_export'])
            with (self.root / 'outputs/basa_beneficios_por_categoria.csv').open(encoding='utf-8-sig') as stream:
                self.assertEqual(list(csv.DictReader(stream)), [])

    def test_recovery_replaces_retained_row_once(self):
        self.seed()
        def parser(item, text, today):
            return [{**self.row, 'SHA256 documento': item['sha256'], 'Verificado UTC': item['fetched_at']}], 'published'
        with patch.object(docs, 'ROOT', self.root), patch.object(docs, 'download', return_value=b'%PDF new'), patch.object(docs, 'native_text', return_value='new terms'):
            rows, meta = docs.run('basa', self.page, parser, html=self.html, today=date(2026,11,2))
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]['Verificado UTC'], self.stamp)
        self.assertEqual(meta['retained_rows'], 0)
        self.assertEqual(meta['fetched'], 1)

    def test_expired_or_grace_elapsed_empty_export_not_old_csv(self):
        self.row['Vigencia'] = 'Hasta 2026-11-01'
        self.seed()
        with patch.object(docs, 'ROOT', self.root), patch.object(docs, 'download', side_effect=requests.Timeout()):
            rows, meta = docs.run('basa', self.page, lambda *args: None, html=self.html, today=date(2026,11,2))
        self.assertEqual(rows, [])
        self.assertTrue(meta['authoritative_export'])

    def test_removed_index_entry_is_not_retained(self):
        self.seed()
        html = self.html.replace('test.pdf', 'other.pdf').replace('Merchant', 'Other')
        with patch.object(docs, 'ROOT', self.root), patch.object(docs, 'download', side_effect=requests.Timeout()):
            rows, meta = docs.run('basa', self.page, lambda *args: None, html=html, today=date(2026,11,2))
        self.assertEqual(rows, [])
        self.assertEqual(meta['retained_rows'], 0)

    def test_normalization_preserves_retention_deadline_separate_from_terms(self):
        from promo_backend.normalize import normalize_source_row
        row = {**self.row, 'Retenido hasta UTC': '2026-11-03T13:36:45+00:00',
               'Cantidad de descuento / beneficio': 'Hasta 12 cuotas sin intereses'}
        normalized = normalize_source_row('Basa', row)[0]
        self.assertEqual(normalized['source_retention_expires_at'], row['Retenido hasta UTC'])
        self.assertEqual(normalized['source_verification'], 'official_document')
        self.assertEqual(normalized['validity'], 'Hasta 2026-12-31')

    def test_error_classification(self):
        self.assertTrue(docs.transient_retrieval_error(requests.ConnectionError()))
        self.assertFalse(docs.transient_retrieval_error(ValueError('PDF invalid')))
        for status, expected in [(404,False),(403,False),(429,True),(500,True),(503,True)]:
            response = requests.Response(); response.status_code = status
            self.assertEqual(docs.transient_retrieval_error(requests.HTTPError(response=response)), expected)


if __name__ == '__main__': unittest.main()

class BasaEmptyAtomicity(unittest.TestCase):
    def test_completed_basa_withholding_does_not_restore_old_csv(self):
        from promo_backend import run_all as runner
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'public').mkdir(); (root/'outputs').mkdir()
            output = root/'outputs/basa_beneficios_por_categoria.csv'
            output.write_text('Comercio\nExpired old merchant\n')
            def script(name):
                if name.endswith('extract_basa.py'):
                    output.write_text('Comercio\n')
                    (root/'outputs/basa_source_meta.json').write_text(json.dumps({'status':'partial','pending':1,'fetch_errors':1,'authoritative_export':True}))
            with patch.object(runner,'ROOT',root), patch.object(runner,'run_step',side_effect=script), patch.object(runner.sys,'argv',['run_all.py','basa']):
                self.assertEqual(runner.main(),1)
            self.assertEqual(output.read_text(),'Comercio\n')
            self.assertEqual(json.loads((root/'public/source_status.json').read_text())['Basa']['status'],'partial')
