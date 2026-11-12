"""Source-bound address inventory. No geocoding or coordinate inheritance."""
import hashlib
import json
from datetime import date

PREFIX='loc-mcd-reviewed-'

def apply(locations, root):
    result=[p for p in locations if not p.get('id','').startswith(PREFIX)]
    path=root/'data/mcdonalds_documented_branches.json'
    if not path.exists():return result
    offers={p['id']:p for p in json.loads((root/'public/promotions.json').read_text())}
    source_hashes={}
    for p in json.loads((root/'outputs/interfisa_source_meta.json').read_text()).get('documents',[]):source_hashes[p['url']]=p.get('sha256')
    for p in json.loads((root/'outputs/familiar_extraction_review.json').read_text()).get('records',[]):source_hashes[p.get('pdf_url','')]=p.get('pdf_sha256')
    for group in json.loads(path.read_text())['groups']:
        if source_hashes.get(group['source_url'])!=group['pdf_sha256'] or group['ends_on']<date.today().isoformat():continue
        valid=[]
        for offer_id,fingerprint in group['offers'].items():
            offer=offers.get(offer_id)
            if not offer or offer['bank']!=group['bank']:continue
            if group['source_url'] not in (offer.get('source_url'),offer.get('source_document_url')):continue
            if hashlib.sha256(offer['raw_detail'].encode()).hexdigest()!=fingerprint:continue
            valid.append(offer_id)
        if len(valid)!=len(group['offers']):continue
        for n,branch in enumerate(group['branches'],1):
            result.append({'id':PREFIX+group['key']+'-'+str(n),'bank':group['bank'],'category':'Gastronomía','merchant_name':group['merchant_name'],'name':group['merchant_name'],'address':branch['address'],'city':'','country':'Paraguay','source_url':group['source_url'],'source_page':branch['page'],'participation_document_sha256':group['pdf_sha256'],'promotion_ids':valid,'participation_ends_on':group['ends_on'],'participation_starts_on':group['starts_on'],'lat':None,'lng':None,'geocode_source':'','online_only':False,'address_only':True,'location_review_status':'official_address_only'})
    return result
