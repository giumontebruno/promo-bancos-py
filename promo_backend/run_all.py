import csv
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ('GNB', 'gnb', ['extract_gnb', 'build_gnb_live_catalog', 'build_gnb_reviewed']),
    ('Familiar', 'familiar', ['extract_familiar', 'build_familiar_table']),
    ('Sudameris', 'sudameris', ['extract_sudameris', 'build_sudameris_table']),
    ('Itaú', 'itau', ['extract_itau']),
    ('BNF', 'bnf', ['extract_bnf']),
    ('Continental', 'continental', ['extract_continental']),
    ('Atlas', 'atlas', ['extract_atlas']),
    ('Coop. Universitaria', 'universitaria', ['extract_universitaria', 'review_universitaria']),
    ('Basa', 'basa', ['extract_basa']),
    ('Interfisa', 'interfisa', ['extract_interfisa']),
    ('Bancop', 'bancop', ['extract_bancop']),
    ('Solar', 'solar', ['extract_solar']),
    ('Zeta', 'zeta', ['extract_zeta']),
    ('ueno bank', 'ueno', ['extract_ueno', 'extract_ueno_pdf_links', 'enrich_ueno_from_bases', 'extract_ueno_tables']),
]


def run_step(script):
    print(f'Running {script}', flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', script], cwd=ROOT, check=True, timeout=900)


def source_backup_paths(prefix):
    paths = [path for path in (ROOT / 'outputs').glob(f'{prefix}_*') if path.is_file()]
    if prefix == 'gnb':
        # This snapshot and the review CSV are a single extraction transaction.
        paths.append(ROOT / 'data/gnb_live_cards.json')
    return paths


NEW_SOURCE_PREFIXES = {'basa', 'interfisa', 'bancop', 'solar', 'zeta'}


def issue_count(value):
    if isinstance(value, dict):
        # Some reports group pending items by reason rather than listing them.
        if all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in value.values()):
            return sum(value.values())
        return len(value)
    if isinstance(value, list):
        return len(value)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def build_source_status(rows, prior, meta=None, migration=None, now=None):
    """Retrieval recency and complete review are separate evidence, never synonyms."""
    meta, migration = meta or {}, migration or {}
    # Offline callers use only a captured source timestamp; the live runner
    # explicitly supplies its completion timestamp after successful scripts.
    now = now or meta.get('attempted_at') or meta.get('checked_at') or migration.get('checked_at')
    row_pending = sum(row.get('Estado verificacion') == 'unconfirmed' for row in rows)
    pending_counts = {key: issue_count(meta.get(key)) for key in ('pending', 'skipped', 'import_issues')}
    pending_counts.update(meta.get('review_report_counts', {}))
    if migration:
        pending_counts['sudameris_migration_failures'] = issue_count(migration.get('failures'))
    # Reports can overlap and a document can expand into multiple rows. Keep
    # rows separate and report the largest evidence count, never sum duplicates.
    pending = max(pending_counts.values(), default=0)
    discovered = meta.get('discovered', meta.get('catalog_discovered'))
    fetched = meta.get('fetched')
    fetch_errors = issue_count(meta.get('fetch_errors'))
    retrieval_gap = meta.get('status') == 'failed' or fetch_errors > 0 or (isinstance(discovered, int) and isinstance(fetched, int) and fetched < discovered)
    blocked = meta.get('status') == 'blocked'
    cached = bool(meta.get('cache_replay'))
    incomplete = blocked or retrieval_gap or row_pending > 0 or pending > 0 or meta.get('coverage_complete') is False or meta.get('status') in {'partial', 'failed'}
    result = {'status': 'blocked' if blocked else 'partial' if incomplete else 'fetched',
              'records': len(rows), 'attempted_at': now,
              'checked_at': prior.get('checked_at') if incomplete or cached else now,
              'retrieval_status': 'blocked' if blocked else 'cached' if cached else 'partial' if retrieval_gap else 'fetched',
              'last_successful_fetch_at': prior.get('last_successful_fetch_at', prior.get('checked_at')) if blocked or retrieval_gap or cached else now,
              'pending_records': row_pending, 'pending_items': pending,
              'pending_items_semantics': 'largest_report_count_not_deduplicated_total',
              'pending_counts_by_report': pending_counts,
              'evidence_paths': meta.get('evidence_paths', []), 'coverage_complete': not incomplete}
    for key in ('discovered', 'catalog_discovered', 'fetched', 'fetch_errors', 'reason', 'cache_replay'):
        if key in meta:
            result[key] = meta[key]
    return result


def read_source_metadata(prefix):
    path = ROOT / 'outputs' / f'{prefix}_source_meta.json'
    meta = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    evidence_paths = [str(path.relative_to(ROOT))] if path.exists() else []
    migration_path = ROOT / 'outputs/sudameris_migration_report.json'
    migration = json.loads(migration_path.read_text(encoding='utf-8')) if prefix == 'sudameris' and migration_path.exists() else {}
    if migration:
        evidence_paths.append(str(migration_path.relative_to(ROOT)))
    report_specs = {'universitaria': ('universitaria_review_report.json', 'withheld'),
                    'ueno': ('ueno_terms_review.json', None)}
    if prefix in report_specs:
        filename, key = report_specs[prefix]
        report_path = ROOT / 'outputs' / filename
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding='utf-8'))
            pending = report.get(key, []) if key else report
            meta['review_report_counts'] = {filename: issue_count(pending)}
            evidence_paths.append(str(report_path.relative_to(ROOT)))
    meta['evidence_paths'] = evidence_paths
    return meta, migration


def main():
    requested = {value.casefold() for value in sys.argv[1:]}
    groups = [group for group in GROUPS if not requested or group[0].casefold() in requested or group[1].casefold() in requested]
    if requested and not groups:
        raise SystemExit(f'Unknown promotion source: {", ".join(sys.argv[1:])}')
    status_path = ROOT / 'public/source_status.json'
    previous = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    status, failures = dict(previous), []
    for bank, prefix, scripts in groups:
        output = ROOT / 'outputs' / f'{prefix}_beneficios_por_categoria.csv'
        backups = {path: path.read_bytes() for path in source_backup_paths(prefix) if path.exists()}
        attempted_step = None
        try:
            for script in scripts:
                attempted_step = f'scrapers/{script}.py'
                run_step(attempted_step)
            with output.open(encoding='utf-8-sig') as handle:
                rows = list(csv.DictReader(handle))
            meta, migration = read_source_metadata(prefix)
            source = build_source_status(rows, previous.get(bank, {}), meta, migration, datetime.now(timezone.utc).isoformat())
            # A never-populated new integration may explicitly report blocked/partial
            # coverage. It must not erase a previously usable source dataset.
            prior_csv_rows = list(csv.DictReader(io.StringIO(backups.get(output, b'').decode('utf-8-sig'))))
            explicit_new_empty = (prefix in NEW_SOURCE_PREFIXES and not prior_csv_rows and not previous.get(bank, {}).get('records')
                                  and source['status'] in {'blocked', 'partial'} and source['coverage_complete'] is False)
            if not rows and not explicit_new_empty:
                raise ValueError('Empty source output')
            status[bank] = source
            if source['status'] != 'fetched':
                failures.append(bank)
                print(f"{bank}: {source['status']}; {source['pending_items']} items require review; retrieval={source['retrieval_status']}.", flush=True)
        except (subprocess.SubprocessError, ValueError, OSError) as error:
            for path, content in backups.items():
                path.write_bytes(content)
            # A failed monthly extraction must preserve the last usable dataset.
            for path in source_backup_paths(prefix):
                if path.is_file() and path not in backups:
                    path.unlink()
            status[bank] = {**previous.get(bank, {}), 'status': 'failed', 'retrieval_status': 'failed', 'attempted_at': datetime.now(timezone.utc).isoformat(), 'error_type': type(error).__name__}
            status[bank]['failed_step'] = attempted_step
            if isinstance(error, subprocess.CalledProcessError):
                status[bank]['exit_code'] = error.returncode
            failures.append(bank)
            print(f'{bank}: refresh failed; previous source preserved.', flush=True)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    if not requested:
        location_paths = [ROOT / 'outputs/locations.csv', ROOT / 'public/locations.json']
        location_backups = {path: path.read_bytes() for path in location_paths if path.exists()}
        try:
            run_step('scrapers/build_locations.py')
            run_step('scrapers/enrich_locations_google.py')
        except (subprocess.SubprocessError, OSError):
            for path, content in location_backups.items():
                path.write_bytes(content)
            failures.append('location_enrichment')
            print('Location refresh failed; previous geocoded catalog preserved.', flush=True)
    run_step('promo_backend/normalize.py')
    report = {'completed_at': datetime.now(timezone.utc).isoformat(), 'failed_sources': failures, 'sources': status}
    (ROOT / 'outputs/refresh_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Refresh finished: {len(failures)} failures. See outputs/refresh_report.json.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
