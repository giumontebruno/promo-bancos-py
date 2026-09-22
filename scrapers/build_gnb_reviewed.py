"""Build explicitly reviewed GNB offers; never infer coverage from inaccessible pages."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(data):
    rows = []
    money = lambda value: f'{value:,}'.replace(',', '.')
    branches = '; '.join(f'{name}: {address}, {city}' for name, address, city, _ in data.get('branches', []))
    for entry in data['merchants']:
        details = entry if isinstance(entry, dict) else {'name': entry}
        merchant = details['name']
        locations = branches or f"Todas las sucursales de {merchant}. Ciudad indicada en las bases: {details['city']}."
        for offer in data['offers']:
            caps = f"Tope de compra mensual por cuenta: Gs. {money(data['purchase_cap'])}. Tope de reintegro mensual por cuenta: Gs. {money(offer['refund_cap'])}."
            if data.get('refund_cap_derived'):
                caps = f"Tope de compra {data['cap_scope']}: Gs. {money(data['purchase_cap'])}. Reintegro máximo calculado al {offer['percent']}%: Gs. {money(offer['refund_cap'])}; no es un cupo adicional independiente."
            benefit = f"{offer['percent']}% de reintegro con {offer['payment']}"
            rows.append({'Comercio':merchant, 'Categoria':data.get('category', 'Combustible' if merchant == 'Copetrol' else 'Tiendas'),
                         'Beneficio':benefit, 'Dia':data['day'],
                         'Vigencia':f"Desde {details.get('starts_on', data['starts_on'])} hasta {data['ends_on']}",
                         'Locales':locations, 'Montos':caps, 'URL detalle':data['source_url'],
                         'Tarjetas verificadas':offer['cards'] + ' · ' + offer['payment'],
                         'Detalle':f"{benefit}. {caps} {data['conditions']} {details.get('exception', '')}".strip(),
                         'Variante':offer['key'], 'Tipo de variante':offer['kind'],
                         'Etiqueta de variante':offer.get('label', 'Black / Premier' if offer['kind']=='premium' else 'Clásica / Oro')})
    return rows


def main():
    data = json.loads((ROOT / 'data/gnb_reviewed_offers.json').read_text(encoding='utf-8'))
    rows = build(data)
    restaurants = json.loads((ROOT / 'data/gnb_restaurants_reviewed.json').read_text(encoding='utf-8'))
    rows.extend(build(restaurants))
    with (ROOT / 'outputs/gnb_beneficios_por_categoria.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / 'outputs/gnb_source_meta.json').write_text(json.dumps({'checked_at':max(data['checked_at'], restaurants['checked_at']),'coverage':'Reviewed Copetrol/Copemarket and Bares y Resto PDFs; full catalog pending','records':len(rows)},indent=2),encoding='utf-8')
    print(f'GNB: {len(rows)} reviewed offers; full catalog still pending.')


if __name__ == '__main__':
    main()
