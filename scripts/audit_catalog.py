"""Bounded, read-only catalog diagnostics for maintenance."""
import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path


def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.lower()) if not unicodedata.combining(c))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--merchant', default='')
    parser.add_argument('--bank', default='')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--detail', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    rows = json.loads((root / 'public/promotions.json').read_text(encoding='utf-8'))
    missing = [p for p in rows if p['benefit_type'] in ['reintegro','descuento'] and not p.get('percentages')]
    print(json.dumps({'total':len(rows),'banks':dict(Counter(p['bank'] for p in rows)), 'missing_discount_percent':len(missing)}, ensure_ascii=False))
    selected = [p for p in rows if folded(args.merchant) in folded(p['merchant_name']) and folded(args.bank) in folded(p['bank'])] if args.merchant or args.bank else missing
    keys = ['id','bank','merchant_name','benefit_summary','day_text','validity','source_page_url','source_url']
    if args.detail:
        keys += ['terms','raw_detail']
    for promo in selected[:max(1,min(args.limit,50))]:
        print(json.dumps({k:promo.get(k) for k in keys},ensure_ascii=False))
    print(f'Matched {len(selected)} records; displayed {min(len(selected),max(1,min(args.limit,50)))}.')


if __name__ == '__main__':
    main()
