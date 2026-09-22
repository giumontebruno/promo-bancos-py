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


def build_additional(data):
    rows = []
    for campaign in data['campaigns']:
        locations = campaign.get('municipalities') or [(campaign['merchant'], campaign['location'])]
        for merchant, location in locations:
            for offer in campaign.get('offers', [campaign]):
                financing = 'cuotas' in offer['benefit'].lower()
                rows.append({
                    'Comercio': merchant,
                    'Categoria': campaign['category'],
                    'Beneficio': offer['benefit'],
                    'Dia': offer.get('day', 'Todos los días'),
                    'Vigencia': f"Desde {campaign['starts_on']} hasta {campaign['ends_on']}",
                    'Locales': location,
                    'Montos': 'Sin tope monetario indicado en las bases.' if financing else 'Tope de compra mensual por cuenta, compartido entre todas las sucursales: Gs. 1.000.000. Incluye titular y adicionales.',
                    'URL detalle': campaign['source_url'],
                    'Tarjetas verificadas': offer['cards'],
                    'Detalle': f"{offer['benefit']}. {campaign['conditions']} {offer.get('conditions', '')}".strip(),
                    'Variante': offer.get('variant', 'financing'),
                    'Tipo de variante': offer.get('kind', 'base'),
                    'Etiqueta de variante': offer.get('label', 'Cuotas'),
                    'Porcentaje efectivo': offer.get('effective_percent', ''),
                })
    return rows


def build_page_campaigns(data):
    rows = []
    money = lambda value: f'{value:,}'.replace(',', '.')
    for campaign in data['campaigns']:
        cap = f"Tope de compra mensual compartido por cuenta en los locales adheridos: Gs. {money(campaign['purchase_cap'])}. No es un tope de reintegro." if campaign.get('purchase_cap') else ''
        for offer in campaign['offers']:
            benefit = offer.get('benefit') or f"{offer['percent']}% de reintegro"
            rows.append({
                'Comercio': campaign['merchant'],
                'Categoria': campaign['category'],
                'Beneficio': benefit,
                'Dia': campaign['day'],
                'Vigencia': f"Desde {campaign['starts_on']} hasta {campaign['ends_on']}",
                'Locales': campaign['locations'],
                'Montos': cap,
                'URL detalle': campaign['source_url'],
                'Tarjetas verificadas': offer['cards'],
                'Detalle': f"{benefit} con {offer['cards']}. {cap} {campaign['conditions']} Consultá la ficha original para confirmar las condiciones vigentes.",
                'Variante': offer['key'],
                'Tipo de variante': offer['kind'],
                'Etiqueta de variante': offer['label'],
            })
    return rows


def main():
    data = json.loads((ROOT / 'data/gnb_reviewed_offers.json').read_text(encoding='utf-8'))
    rows = build(data)
    restaurants = json.loads((ROOT / 'data/gnb_restaurants_reviewed.json').read_text(encoding='utf-8'))
    rows.extend(build(restaurants))
    additional = json.loads((ROOT / 'data/gnb_additional_reviewed.json').read_text(encoding='utf-8'))
    rows.extend(build_additional(additional))
    page_campaigns = json.loads((ROOT / 'data/gnb_page_reviewed.json').read_text(encoding='utf-8'))
    rows.extend(build_page_campaigns(page_campaigns))
    with (ROOT / 'outputs/gnb_beneficios_por_categoria.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / 'outputs/gnb_source_meta.json').write_text(json.dumps({'checked_at':page_campaigns['checked_at'],'coverage':'Reviewed PDFs and indexed GNB benefit cards; full catalog pending','records':len(rows)},indent=2),encoding='utf-8')
    print(f'GNB: {len(rows)} reviewed offers; full catalog still pending.')


if __name__ == '__main__':
    main()
