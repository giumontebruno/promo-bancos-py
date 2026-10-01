import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ('GNB', 'gnb', ['extract_gnb', 'build_gnb_live_catalog', 'review_gnb_cards_with_pdf', 'build_gnb_reviewed']),
    ('Familiar', 'familiar', ['extract_familiar', 'build_familiar_table']),
    ('Sudameris', 'sudameris', ['extract_sudameris', 'build_sudameris_table']),
    ('Itaú', 'itau', ['extract_itau']),
    ('BNF', 'bnf', ['extract_bnf']),
    ('Continental', 'continental', ['extract_continental']),
    ('Atlas', 'atlas', ['extract_atlas']),
    ('Coop. Universitaria', 'universitaria', ['extract_universitaria', 'review_universitaria']),
    ('ueno bank', 'ueno', ['extract_ueno', 'extract_ueno_pdf_links', 'enrich_ueno_from_bases', 'extract_ueno_tables']),
]


def run_step(script):
    print(f'Running {script}', flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', script], cwd=ROOT, check=True, timeout=900)


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
        backups = {path: path.read_bytes() for path in (ROOT / 'outputs').glob(f'{prefix}_*') if path.is_file()}
        try:
            for script in scripts:
                run_step(f'scrapers/{script}.py')
            with output.open(encoding='utf-8-sig') as handle:
                rows = list(csv.DictReader(handle))
            if not rows:
                raise ValueError('Empty source output')
            status[bank] = {'status': 'fetched', 'checked_at': datetime.now(timezone.utc).isoformat(), 'records': len(rows)}
        except (subprocess.SubprocessError, ValueError, OSError) as error:
            for path, content in backups.items():
                path.write_bytes(content)
            # A failed monthly extraction must preserve the last usable dataset.
            for path in (ROOT / 'outputs').glob(f'{prefix}_*'):
                if path.is_file() and path not in backups:
                    path.unlink()
            status[bank] = {**previous.get(bank, {}), 'status': 'failed', 'attempted_at': datetime.now(timezone.utc).isoformat(), 'error_type': type(error).__name__}
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
