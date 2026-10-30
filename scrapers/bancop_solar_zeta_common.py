"""Bounded official-source IO shared only by the three new bank adapters."""
import csv, hashlib, io, json, re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
import requests
from pypdf import PdfReader

ALLOWED = {'www.bancop.com.py', 'www.solar.com.py', 'api.solar.com.py', 'www.zbanco.com.py'}
def clean(value):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', str(value or '')))).strip()
def fetch(url, data=None):
    if urlparse(url).scheme != 'https' or urlparse(url).hostname not in ALLOWED:
        raise ValueError('Non-official source URL')
    response = requests.post(url, data=data, timeout=30) if data is not None else requests.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > 15_000_000:
        raise ValueError('Source exceeds bounded size')
    if urlparse(response.url).hostname not in ALLOWED:
        raise ValueError('Non-official redirect')
    return response

def pdf_text(blob):
    reader = PdfReader(io.BytesIO(blob))
    if len(reader.pages)>40: raise ValueError('PDF exceeds bounded page count')
    return '\n'.join(page.extract_text() or '' for page in reader.pages)

def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()

def export(bank, rows, coverage):
    """Empty output is only a blocked Zeta inventory, never successful coverage."""
    out=Path('outputs');out.mkdir(exist_ok=True)
    coverage.update(bank=bank, attempted_at=datetime.now(timezone.utc).isoformat(), rows=len(rows))
    (out/f'{bank}_source_meta.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
    if not rows:
        if bank == 'zeta' and coverage.get('status') == 'blocked' and coverage.get('coverage_complete') is False:
            # run_all accepts this only for a never-populated source; it rolls back
            # if an existing source had usable data. Status remains blocked.
            (out/f'{bank}_beneficios_por_categoria.csv').write_text('Banco,Comercio/Promoción\n', encoding='utf-8-sig')
            return
        raise RuntimeError(f'{bank}: no verified publishable current offers; see source metadata')
    path=out/f'{bank}_beneficios_por_categoria.csv'
    temporary=path.with_suffix('.csv.tmp')
    with temporary.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader();writer.writerows(rows)
    temporary.replace(path)
