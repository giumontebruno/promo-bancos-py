"""Discover GNB official sources without publishing unverified or QA data."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCE = 'https://www.beneficiosbancognb.com.py/v2/beneficios/categorias'


def main():
    report = {'checked_at':datetime.now(timezone.utc).isoformat(), 'source':SOURCE, 'status':'pending_review', 'links':[]}
    try:
        response = requests.get(SOURCE, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        if 'Access Denied' in soup.get_text():
            raise ValueError('Source denied access')
        links = set()
        for a in soup.select('a[href]'):
            link = urljoin(SOURCE, a['href'])
            parsed = urlparse(link)
            if parsed.hostname == 'www.beneficiosbancognb.com.py' and ('/beneficios/' in parsed.path or parsed.path.endswith('.pdf')):
                links.add(link)
        if not links:
            raise ValueError('No official promotion links')
        report['links'] = sorted(links)
    except (requests.RequestException, ValueError) as error:
        report.update(status='blocked_source', error_type=type(error).__name__)
    path = Path(__file__).resolve().parents[1] / 'outputs/gnb_extraction_review.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'GNB: {report["status"]}, {len(report["links"])} official links. No unverified cards published.')


if __name__ == '__main__':
    main()
