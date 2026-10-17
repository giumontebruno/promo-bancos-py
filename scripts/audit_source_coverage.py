"""Inventory every offer without interpreting inaccessible sources as expiration."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-of', default=date.today().isoformat())
    args = parser.parse_args()
    date.fromisoformat(args.as_of)
    root = Path(__file__).resolve().parents[1]
    rows = json.loads((root / 'public/promotions.json').read_text(encoding='utf-8'))
    sources = json.loads((root / 'public/source_status.json').read_text(encoding='utf-8'))
    by_bank = defaultdict(Counter)
    inventory = []
    for p in rows:
        terms = p.get('terms') or {}
        start, end = terms.get('starts_on'), terms.get('ends_on')
        if terms.get('conflicting_dates'):
            temporal = 'conflicting_dates'
        elif not end:
            temporal = 'unknown_end'
        elif end < args.as_of:
            temporal = 'past_end_in_catalog'
        elif start and start > args.as_of:
            temporal = 'future_start_in_catalog'
        else:
            temporal = 'within_catalog_dates'
        verification = p.get('source_verification') or 'source_pipeline'
        by_bank[p['bank']]['total'] += 1
        by_bank[p['bank']][temporal] += 1
        by_bank[p['bank']][verification] += 1
        inventory.append({'id': p['id'], 'bank': p['bank'], 'merchant': p['merchant_name'],
                          'temporal_classification': temporal, 'source_verification': verification,
                          'starts_on': start, 'ends_on': end,
                          'source_page_url': p.get('source_page_url'), 'source_identity_url': p.get('source_url'),
                          'source_checked_at': p.get('source_checked_at'),
                          'issues': ';'.join(terms.get('issues', []))})
    out = root / 'outputs'
    with (out / 'source_audit_inventory.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)
    report = {'as_of': args.as_of, 'total': len(rows),
              'note': 'Catalog date classification is not independent confirmation of official terms. Source fetched status is not document review.',
              'banks': {bank: {**counts, 'extraction': sources.get(bank)} for bank, counts in sorted(by_bank.items())}}
    (out / 'source_audit_coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
