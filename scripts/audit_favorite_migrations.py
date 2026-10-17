"""Audit every archived promotion and saved campaign key against current favorites."""
import json
from pathlib import Path
from collections import Counter

def main():
    root=Path(__file__).resolve().parents[1]
    rows=json.loads((root/'public/promotions.json').read_text(encoding='utf-8'))
    old=json.loads((root/'data/promotion_history_20261017.json').read_text(encoding='utf-8'))['offers']
    aliases=json.loads((root/'public/manifest.json').read_text(encoding='utf-8'))['favorite_aliases']
    ids={value for p in rows for value in (p['id'],p.get('campaign_id')) if value}
    details=[]
    for p in old:
        for original in dict.fromkeys(filter(None,(p['id'],p.get('campaign_id')))):
            target=original;seen=set()
            while target in aliases and target not in seen:
                seen.add(target);target=aliases[target]
            status='preserved' if original in ids else 'alias' if target in ids else 'unresolved'
            details.append({'old_id':original,'bank':p['bank'],'merchant':p['merchant_name'],
                            'source_url':p['source_url'],'target':target,'status':status})
    report={'archived_records':len(old),'saved_key_checks':len(details),
            'statuses':dict(Counter(d['status'] for d in details)),'details':details}
    (root/'outputs/favorite_migration_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='details'}))
    for d in details:
        if d['status']=='unresolved':print(json.dumps(d,ensure_ascii=False))

if __name__=='__main__':main()
