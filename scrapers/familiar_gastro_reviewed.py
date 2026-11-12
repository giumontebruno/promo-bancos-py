"""Expand only explicitly reviewed McDonald's locations, bound to source PDF bytes."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build(record):
    reviews=json.loads((ROOT/'data/familiar_gastro_mcdonalds_reviewed.json').read_text())['reviews']
    review=next((r for r in reviews if r['source_url']==record['source_url']),None)
    if not review:
        return None
    if record.get('pdf_sha256')!=review['pdf_sha256'] or hashlib.sha256(record.get('terms_text','').encode()).hexdigest()!=review['text_sha256']:
        raise ValueError('reviewed_gastro_source_changed')
    rows=[]
    for rate,cards,kind in [(25,'Visa Platinum','premium'),(20,'Visa o Mastercard Oro/Gold, Visa o Mastercard Clásica, Positiva Visa y Positiva Bancardcheck','base')]:
        cap='Límite de compra mensual por tarjeta: Gs. 500.000. '+review['shared_scope']
        detail=f'{rate}% de reintegro con {cards}. {cap} Sólo McDonald’s de {review["location"]}. Lunes a viernes. Pagos únicamente a través de la red Bancard. No participan tarjetas empresariales, Gourmet Cards ni Movil Cards. No asumir un cupo adicional al cambiar entre las campañas Gastro Plaza Norte, Mariano y Mariscal: Plaza Norte y Mariano expresamente comparten el límite entre las tres; Mariscal sólo menciona su campaña.'
        rows.append({'Comercio':"McDonald's - "+review['location'],'Categoria':'Gastronomía','Beneficio':f'{rate}% de reintegro','Dia':'Lunes a viernes','Vigencia':'Desde 2026-04-01 hasta 2026-12-31','Locales':"Sólo McDonald's de "+review['location'],'Montos':cap,'URL detalle':record['source_url'],'Documento fuente URL':record['pdf_url'],'Tarjetas verificadas':cards,'Detalle':detail,'Texto original de la fuente':record['terms_text'],'Variante':'gastro-mcdonalds-'+kind,'Tipo de variante':kind,'Etiqueta de variante':cards,'Fecha verificacion fuente':review['checked_at'],'Estado verificacion':'official_document','Topes revisados por variante':'yes'})
    return rows
