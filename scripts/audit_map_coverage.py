"""Read-only map coverage audit; no geocoding requests or catalog changes."""
import argparse
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').lower()) if not unicodedata.combining(c)).strip()

def valid_coordinates(item):
    lat, lng = item.get('lat'), item.get('lng')
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (lat, lng)) and -90 <= lat <= 90 and -180 <= lng <= 180

def exclusion(item):
    if item.get('online_only'):
        return 'online_only'
    if not valid_coordinates(item):
        return 'missing_or_invalid_coordinates'
    if item.get('geocode_source') in (None, '', 'city_approximation'):
        return 'unverified_or_approximate'
    if item.get('google_confidence') == 'review' or item.get('google_enrichment_status') == 'needs_review':
        return 'requires_review'
    merchant = norm(item.get('merchant_name'))
    name = norm(item.get('google_name') or item.get('name'))
    if merchant in ('farmacias', 'mayoristas', 'supermercados', 'estaciones de servicio', 'frigorificos') and 'shopping_mall' in item.get('google_types', []) and any(s in name for s in ('shopping', 'delsol', 'del sol', 'park 14')):
        return 'generic_merchant_matched_to_mall'
    return 'eligible_coordinates'

def audit(payload):
    locations = payload.get('locations', [])
    banks, identities, coordinate_groups = defaultdict(Counter), defaultdict(list), defaultdict(list)
    for item in locations:
        bank = item.get('bank') or 'unknown'
        banks[bank]['total'] += 1
        banks[bank][exclusion(item)] += 1
        if not item.get('address'):
            banks[bank]['missing_address'] += 1
        identity = '|'.join(norm(item.get(k)) for k in ('bank', 'merchant_name', 'address', 'city'))
        identities[identity].append(item.get('id'))
        if valid_coordinates(item):
            coordinate_groups[f"{item['lat']:.5f},{item['lng']:.5f}"].append({'id': item.get('id'), 'merchant': item.get('merchant_name')})
    return {
        'source_generated_at': payload.get('generated_at'),
        'total': len(locations),
        'status_counts': dict(Counter(exclusion(i) for i in locations)),
        'by_bank': dict(banks),
        'duplicate_ids': {k: v for k, v in Counter(i.get('id') for i in locations).items() if v > 1},
        'duplicate_branch_groups': {k: v for k, v in identities.items() if len(v) > 1},
        'shared_coordinate_groups': {k: v for k, v in coordinate_groups.items() if len(v) > 1},
        'note': 'Eligible coordinates are not proof of an active promotion or branch applicability. Shared coordinates are review candidates, not automatic duplicates.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--locations', type=Path, default=ROOT / 'public/locations.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit(json.loads(args.locations.read_text(encoding='utf-8')))
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('duplicate_branch_groups', 'shared_coordinate_groups')}, ensure_ascii=True))
    print(f"Duplicate branch groups: {len(report['duplicate_branch_groups'])}; shared coordinate groups: {len(report['shared_coordinate_groups'])}")

if __name__ == '__main__':
    main()
