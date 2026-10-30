"""Discover Bancop's public modals and parse only explicitly scoped PDF clauses."""
import re,json
from pathlib import Path
from copy import deepcopy
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
try:
    from .bancop_solar_zeta_common import fetch,digest,export
except ImportError:
    from bancop_solar_zeta_common import fetch,digest,export
REVIEWED_PDF_HASHES={'526': '1a885aac45e2338c292cfc4317568e03e1270d823d7d0f1030a63c9cca2680ab', '468': '60c455e2800a44c550dca9d051523c915d261ca6abcb52b9c39c27f66148c975', '550': 'c2051aaf7741606cf43d00b39ac4a29c8077949cac6da2f2ed01b8e1f4ccde11'}
PAGE='https://www.bancop.com.py/promociones'
MODAL='https://www.bancop.com.py/ajax/promocion.php'

def catalog(html):
    found={}
    for element in BeautifulSoup(html,'html.parser').select('[data-target="#promo"][data-id][data-title]'):
        ident=element['data-id']
        if not ident.isdigit():raise ValueError('Invalid public promo identifier')
        found[ident]={'id':ident,'title':element['data-title']}
    if not 1<=len(found)<=120:raise ValueError('Unexpected Bancop catalog size')
    return list(found.values())

REVIEW_FILE=Path(__file__).resolve().parents[1]/'data/bancop_reviewed_catalog.json'

def build(card,text,url,sha256='',today=None):
    """Only reviewed merchant-scoped records may publish. No generic PDF fallback."""
    today=today or date.today().isoformat()
    entry=json.loads(REVIEW_FILE.read_text(encoding='utf-8'))['entries'].get(card['id'])
    if not entry:return [],'new_campaign_requires_review'
    if entry['pdf_sha256']!=sha256 or entry['source_url']!=url:
        return [],'source_changed_requires_review'
    if entry['title']!=card['title']:return [],'catalog_identity_changed'
    if entry['status']!='verified':return [],entry['reason']
    rows=[]
    for stored in entry['rows']:
        row=deepcopy(stored)
        # Reviewed data uses ISO rather than locale-dependent text.
        ends=re.search(r'hasta (\d{4}-\d{2}-\d{2})',row['Vigencia'],re.I)[1]
        if ends<today:continue
        row['Texto original de la fuente']=entry.get('source_text','')
        rows.append(row)
    return rows,None if rows else 'expired'

def main():
    cards=catalog(fetch(PAGE).text)
    def process(card):
        try:
            html=fetch(MODAL,{'id':card['id']}).text
            links=[a['href'] for a in BeautifulSoup(html,'html.parser').select('a[href]') if a['href'].lower().endswith('.pdf')]
            if len(set(links))!=1:return [],dict(card,reason='missing_or_multiple_terms')
            blob=fetch(links[0]).content
            rows,reason=build(card,'',links[0],digest(blob))
            return rows,dict(card,reason=reason) if reason else None
        except Exception as exc:return [],dict(card,reason=str(exc))
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(process,cards))
    rows=[row for batch,_ in results for row in batch]
    export('bancop',rows,{'status':'partial','catalog_discovered':len(cards),'skipped':[issue for _,issue in results if issue],
        'coverage_complete':False,'reason':'All 58 initial cards individually reviewed. Missing-year and wrong-merchant documents quarantined; changed/new campaigns require review.'})
if __name__=='__main__':main()
