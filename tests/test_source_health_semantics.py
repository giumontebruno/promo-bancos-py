import unittest
from promo_backend.run_all import build_source_status, GROUPS

class SourceHealthSemantics(unittest.TestCase):
    def setUp(self):
        self.now = '2026-10-30T16:00:00+00:00'
        self.prior = {'checked_at': '2026-10-20T00:00:00+00:00', 'last_successful_fetch_at': '2026-10-29T00:00:00+00:00'}
        self.rows = [{'Estado verificacion': 'verified'}]
    def status(self, meta=None, migration=None, rows=None):
        return build_source_status(self.rows if rows is None else rows, self.prior, meta, migration, self.now)
    def test_pending_omitted_items_are_partial_even_when_all_rows_verified(self):
        result = self.status({'pending': [{'reason': 'not parsed'}]})
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['checked_at'], self.prior['checked_at'])
        self.assertEqual(result['last_successful_fetch_at'], self.now)
    def test_discovery_fetch_gap_is_not_complete_retrieval(self):
        result = self.status({'discovered': 226, 'fetched': 225, 'pending': 157})
        self.assertEqual(result['retrieval_status'], 'partial')
        self.assertEqual(result['last_successful_fetch_at'], self.prior['last_successful_fetch_at'])
    def test_sudameris_migration_failures_prevent_false_fetched(self):
        self.assertEqual(self.status(migration={'failures': [{'reason': 'review'}]})['status'], 'partial')
    def test_cache_replay_never_renews_successful_fetch_or_checked_time(self):
        result = self.status({'cache_replay': True, 'pending': 3})
        self.assertEqual(result['retrieval_status'], 'cached')
        self.assertEqual(result['last_successful_fetch_at'], self.prior['last_successful_fetch_at'])
        self.assertEqual(result['checked_at'], self.prior['checked_at'])
    def test_explicit_blocked_source_is_not_successful(self):
        result = self.status({'status': 'blocked', 'coverage_complete': False}, rows=[])
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['records'], 0)
        self.assertFalse(result['coverage_complete'])
    def test_successful_complete_retrieval_and_review_advance_both_times(self):
        result = self.status({'discovered': 5, 'fetched': 5, 'pending': 0})
        self.assertEqual(result['status'], 'fetched')
        self.assertEqual(result['checked_at'], self.now)
        self.assertEqual(result['last_successful_fetch_at'], self.now)
    def test_fourteen_sources_have_distinct_registered_extractors(self):
        self.assertEqual(len(GROUPS), 14)
        for slug in ('basa', 'interfisa', 'bancop', 'solar', 'zeta'):
            self.assertIn([f'extract_{slug}'], [scripts for _, prefix, scripts in GROUPS if prefix == slug])

if __name__ == '__main__': unittest.main()

class SourceAtomicity(unittest.TestCase):
    def test_offline_without_timestamp_does_not_invent_fetch_time(self):
        result = build_source_status([{}], {})
        self.assertIsNone(result['attempted_at'])
        self.assertIsNone(result['last_successful_fetch_at'])
    def test_new_blocked_source_retained_but_nonempty_prior_is_restored(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import promo_backend.run_all as runner
        for populated in (False, True):
            with self.subTest(populated=populated), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root/'public').mkdir(); (root/'outputs').mkdir()
                output = root/'outputs/zeta_beneficios_por_categoria.csv'
                prior = 'Comercio\nOld usable merchant\n' if populated else 'Comercio\n'
                output.write_text(prior)
                def script(_):
                    if _.endswith('extract_zeta.py'):
                        output.write_text('Comercio\n')
                        (root/'outputs/zeta_source_meta.json').write_text(json.dumps({'status':'blocked','coverage_complete':False}))
                with patch.object(runner,'ROOT',root), patch.object(runner,'run_step',side_effect=script), patch.object(runner.sys,'argv',['run_all.py','zeta']):
                    self.assertEqual(runner.main(),1)
                status=json.loads((root/'public/source_status.json').read_text())['Zeta']
                self.assertEqual(status['status'], 'failed' if populated else 'blocked')
                self.assertEqual(output.read_text(), prior)
                if populated:
                    self.assertFalse((root/'outputs/zeta_source_meta.json').exists())

class AuxiliaryReviewReports(unittest.TestCase):
    def test_numeric_reason_counts_sum_instead_of_counting_categories(self):
        from promo_backend.run_all import issue_count
        self.assertEqual(issue_count({'cards':80,'terms':7}),87)
        self.assertEqual(issue_count([{'reason':'one'}, {'reason':'two'}]),2)
    def test_rows_and_report_items_are_not_added_or_confused(self):
        result = build_source_status([{'Estado verificacion':'unconfirmed'}]*10, {}, {'pending':{'cards':5,'terms':2},'skipped':[{}]*3})
        self.assertEqual(result['pending_records'],10)
        self.assertEqual(result['pending_items'],7)
        self.assertEqual(result['pending_counts_by_report']['skipped'],3)
        self.assertEqual(result['status'],'partial')
    def test_auxiliary_bank_reports_mark_verified_rows_partial_with_provenance(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import promo_backend.run_all as runner
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'outputs').mkdir()
            for prefix, filename, data, expected in [('universitaria','universitaria_review_report.json',{'withheld':[{}]*4},4),('ueno','ueno_terms_review.json',[{}]*3,3)]:
                (root/'outputs'/filename).write_text(json.dumps(data))
                with patch.object(runner,'ROOT',root): meta,migration=runner.read_source_metadata(prefix)
                result=build_source_status([{'Estado verificacion':'verified'}],{},meta,migration)
                self.assertEqual(result['status'],'partial')
                self.assertEqual(result['pending_items'],expected)
                self.assertIn('outputs/'+filename,result['evidence_paths'])
                self.assertIsNone(result['attempted_at'])
