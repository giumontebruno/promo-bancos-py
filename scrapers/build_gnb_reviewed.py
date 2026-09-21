"""Build explicitly reviewed GNB offers; never infer coverage from inaccessible pages."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(data):
    rows = []
    money = lambda value: f'{value:,}'.replace(',', '.')
    branches = '; '.join(f'{name}: {address}, {city}' for name, address, city, _ in data['branches'])
    for merchant in data['merchants']:
        for offer in data['offers']:
            caps = f"Tope de compra mensual por cuenta: Gs. {money(data['purchase_cap'])}. Tope de reintegro mensual por cuenta: Gs. {money(offer['refund_cap'])}."
            benefit = f"{offer['percent']}% de reintegro con {offer['payment']}"
            rows.append({'Comercio':merchant, 'Categoria':'Combustible' if merchant == 'Copetrol' else 'Tiendas',
                         'Beneficio':benefit, 'Dia':data['day'],
                         'Vigencia':f"Desde {data['starts_on']} hasta {data['ends_on']}",
                         'Locales':branches, 'Montos':caps, 'URL detalle':data['source_url'],
                         'Tarjetas verificadas':offer['cards'] + ' · ' + offer['payment'],
                         'Detalle':f"{benefit}. {caps} {data['conditions']}",
                         'Variante':offer['key'], 'Tipo de variante':offer['kind'],
                         'Etiqueta de variante':'Black / Premier' if offer['kind']=='premium' else 'Clásica / Oro'})
    return rows


def main():
    data = json.loads((ROOT / 'data/gnb_reviewed_offers.json').read_text(encoding='utf-8'))
    rows = build(data)
    with (ROOT / 'outputs/gnb_beneficios_por_categoria.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / 'outputs/gnb_source_meta.json').write_text(json.dumps({'checked_at':data['checked_at'],'coverage':'Reviewed Copetrol/Copemarket PDF only','records':len(rows)},indent=2),encoding='utf-8')
    print(f'GNB: {len(rows)} reviewed offers; full catalog still pending.')


if __name__ == '__main__':
    main()
