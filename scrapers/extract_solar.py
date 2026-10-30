"""Solar public server-rendered promotion data. No aggregate discount arithmetic."""
import json,re
from pathlib import Path
REVIEW_FILE=Path(__file__).resolve().parents[1]/"data/solar_reviewed_catalog.json"
REVIEWS={p["id"]:p for p in json.loads(REVIEW_FILE.read_text())["campaigns"]}
from datetime import date
from concurrent.futures import ThreadPoolExecutor
try:
    from .bancop_solar_zeta_common import clean,fetch,pdf_text,digest,export
except ImportError:
    from bancop_solar_zeta_common import clean,fetch,pdf_text,digest,export
REVIEWED_NISSEI={'pdf': '814281cee724ad9cea689a164979cdbdece0bd2f99f1cbbef189506d66fd1a09', 'record': '5b359a5fd33479772a89fd1652af5011e88af4852a6edd4ae2a4ccabef3033f2'}
PAGE='https://www.solar.com.py/promociones'
MONTHS={name:i+1 for i,name in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split())}

def dates(text):
    text=clean(text).lower().replace('al el','al')
    pattern=r'(\d{1,2})\s+(?:de\s+)?('+'|'.join(MONTHS)+r')\s+(?:(?:de|del)\s+)?(20\d{2})'
    found=list(re.finditer(pattern,text))
    if not found:return None,None
    def iso(m):return date(int(m[3]),MONTHS[m[2]],int(m[1])).isoformat()
    end=iso(found[-1]);start=iso(found[0]) if len(found)>1 else None
    if not start:
        shared=re.search(r'(?:del\s+)?(\d{1,2})(?:\s+de\s+(\w+))?\s+al\s+',text)
        if shared:start=date(int(found[-1][3]),MONTHS.get(shared[2],MONTHS[found[-1][2]]),int(shared[1])).isoformat()
    return start,end

def catalog(html):
    match=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',html,re.S)
    if not match:raise ValueError('Solar public data missing')
    promos=json.loads(match[1])['props']['pageProps']['promos']
    if not isinstance(promos,list) or not 1<=len(promos)<=100:raise ValueError('Unexpected Solar catalog size')
    if len({p['id'] for p in promos})!=len(promos):raise ValueError('Duplicate Solar identifiers')
    return promos

DAY_LABELS={'daily':'Todos los días','first_purchase':'Primera compra elegible','tuesday':'Martes','thursday':'Jueves','wednesday':'Miércoles','saturday':'Sábados','monday':'Lunes','friday,saturday,sunday':'Viernes, sábados y domingos','wednesday,thursday':'Miércoles y jueves','month_days_1_to_10':'Del 1 al 10 de cada mes','date_range':'Del 2 al 4 de noviembre de 2026'}
PERIOD_LABELS={'monthly':'mensual acumulado','first_purchase':'primera compra elegible','promotion':'acumulado durante la vigencia','promotion_shared_all_merchants':'acumulado conjunto entre comercios durante la vigencia','accumulated_period_unspecified':'acumulado; período no especificado en las bases','monthly_amount_unspecified':'mensual; importe no especificado'}
def money(amount):
    return format(amount,',').replace(',','.')

def build(promos,terms,today=None):
    today=today or date.today().isoformat();rows=[];skipped=[]
    for p in promos:
        i=p['id'];r=REVIEWS.get(i);term=terms.get(i,{})
        def skip(reason):skipped.append({'id':i,'reason':reason})
        if not r:
            skip('new_campaign_requires_review');continue
        if term.get('sha256')!=r['pdf_sha256'] or digest(json.dumps(p,sort_keys=True,ensure_ascii=False))!=r['record_sha256']:
            skip('source_changed_requires_review');continue
        if not term.get('text') or term['text'].startswith('ERROR'):
            skip('terms_unreadable');continue
        if r['pdf_end']<today:
            skip('expired');continue
        if r['status']!='verified':
            skip(r['status']+': '+'; '.join(r['issues']));continue
        for n,key in enumerate(['classic','gold','premium']):
            refund=r['refund_percent'][n];quota=r['max_interest_free_installments'];cap=r['purchase_cap_pyg'][n]
            components=[]
            if refund:components.append(str(refund)+'% de reintegro')
            if quota:components.append('Hasta '+str(quota)+' cuotas sin intereses')
            if not components:continue
            captext=('Tope de compra: Gs. '+money(cap)+'. ' if cap is not None else 'Importe del tope de compra no especificado. ')
            captext+=PERIOD_LABELS.get(r['cap_period'],'Período no especificado')+'. '
            if r['cap_scope']=='credit_account_including_holder_and_additionals':captext+='Por cuenta de tarjeta, incluyendo titular y adicionales. '
            detail=r['cards'][n]+'. '+r['restrictions']+'. Canal: '+r['channel']+'. '+captext
            # Carry source exclusions literally; never reinterpret odd channel wording.
            text=term['text'];exclusion=text.split('3. Exclusiones',1)
            detail+=' Condiciones textuales: '+clean(text.split('3. Exclusiones',1)[0])
            if len(exclusion)>1:detail+=' Exclusiones de las bases: '+clean(exclusion[1].split('4.',1)[0])
            rows.append({'Banco':'Solar','Categoría':clean(p.get('sectors')) or 'Sin categoría','Comercio/Promoción':p['title'],
                'Cantidad de descuento / beneficio':'; '.join(components),'Día de promoción':DAY_LABELS[r['recurrence']],
                'Vigencia':f"Desde {r['pdf_start']} hasta {r['pdf_end']}",'Montos / topes':captext,'Detalle':detail,
                'URL detalle':r['source_url'],'URL fuente actual':PAGE,'Variante':f"{i}-{key}",
                'Tarjetas verificadas':r['cards'][n],'Estado verificacion':'official_document','Advertencia de fuente':'',
                'Topes revisados por variante':'yes','Texto original de la fuente':json.dumps(p,ensure_ascii=False),
                'SHA256 documento':term['sha256']})
    return rows,skipped

def coverage(promos,rows,skipped):
    return {'status':'partial' if skipped else 'ok','catalog_discovered':len(promos),'catalog_reviewed':sum(p['id'] in REVIEWS for p in promos),
            'catalog_review_complete':all(p['id'] in REVIEWS for p in promos),
            'verified_campaigns':len({r['Variante'].split('-')[0] for r in rows}),
            'reviewed_at_utc':json.loads(REVIEW_FILE.read_text())['checked_at_utc'],
            'review_registry':'data/solar_reviewed_catalog.json',
            'campaign_decisions':[{'id':p['id'],'status':('verified' if any(r['Variante'].startswith(str(p['id'])+'-') for r in rows) else next((x['reason'] for x in skipped if x['id']==p['id']),'not_exported'))} for p in promos],
            'skipped':skipped,'coverage_complete':not skipped,
            'reason':'All known catalog campaigns individually reviewed; expired/ineligible and specific ambiguous campaigns excluded. Changed sources fail closed.'}

def main():
    promos=catalog(fetch(PAGE).text)
    def get_term(p):
        doc=p.get('terms_and_conditions_document') or {};url=(doc.get('meta') or {}).get('download_url') or p.get('terms_and_conditions_url')
        try:
            blob=fetch(url).content
            return p['id'],{'url':url,'text':pdf_text(blob),'sha256':digest(blob)}
        except Exception as exc:return p['id'],{'url':url,'text':'ERROR '+str(exc)}
    with ThreadPoolExecutor(max_workers=4) as pool:terms=dict(pool.map(get_term,promos))
    rows,skipped=build(promos,terms)
    export('solar',rows,coverage(promos,rows,skipped))
if __name__=='__main__':main()
