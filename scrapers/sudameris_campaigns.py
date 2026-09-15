"""Read merchant rows from campaign PDFs instead of publishing campaign banners."""
import io
import re
from datetime import datetime

import pdfplumber
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def merchant_rows(pdf_bytes, source_url, campaign):
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        common = clean(pdf.pages[0].extract_text())
        for page in pdf.pages[1:]:
            for table in page.extract_tables():
                for cells in table:
                    values = [clean(cell) for cell in cells if clean(cell)]
                    if len(values) != 5 or not re.search(r'\d+\s*%', values[2]):
                        continue
                    merchant, days, benefit, cap, validity = values
                    dates = re.findall(r'\b(\d{1,2})\.(\d{2})\.(\d{2})\b', validity)
                    if len(dates) != 2:
                        raise ValueError(f'Missing dates for {merchant}')
                    try:
                        start, end = [datetime(2000+int(y), int(m), int(d)).date().isoformat() for d,m,y in dates]
                        validity = f'Desde {start} hasta {end}'
                    except ValueError:
                        # Keep the source error explicit; never invent a start date.
                        d, m, y = dates[1]
                        end = datetime(2000+int(y), int(m), int(d)).date().isoformat()
                        validity = f'Inicio no confirmado ({dates[0][0]}.{dates[0][1]}.{dates[0][2]} en el PDF). Hasta {end}'
                    note = re.search(r'\(.*\)', merchant)
                    name = clean(re.sub(r'\(.*\)', '', merchant))
                    category = 'Gastronomía' if 'GASTRONOM' in campaign.upper() else 'Otros'
                    location = 'Zona Este - Ciudad del Este' if campaign == 'ZONA ESTE' else 'Zona Sur - Encarnación' if campaign == 'ZONA SUR' else ''
                    rows.append({
                        'Categoría': category, 'Banco': 'Sudameris', 'Comercio/Promoción': name,
                        'Cantidad de descuento / beneficio': benefit,
                        'Día de promoción': days.replace('Vieres', 'Viernes'), 'Vigencia': validity,
                        'Montos / topes': f'Tope de compra mensual: {cap}',
                        'Localidad': location, 'URL': source_url,
                        'Detalle': f'{benefit}. {note[0] if note else ""} {common}',
                    })
    if not rows:
        raise ValueError(f'No merchant table found for {campaign}')
    return rows


def expand_campaign(row):
    detail = requests.get(row['URL'], timeout=30)
    detail.raise_for_status()
    soup = BeautifulSoup(detail.text, 'html.parser')
    urls = [urljoin(row['URL'], a['href']) for a in soup.select('a[href$=".pdf"]')]
    if not urls:
        raise ValueError('Campaign has no PDF: ' + row['Comercio/Promocion'])
    response = requests.get(urls[0], timeout=45)
    response.raise_for_status()
    return merchant_rows(response.content, urls[0], row['Comercio/Promocion'])
