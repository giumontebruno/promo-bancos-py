"""Exact-source reviews of card/cap scopes; changed evidence is withheld for review."""
import hashlib
import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / 'data/itau_reviewed_scopes.json'
SOURCE_FIELDS = ('Detalle', 'Bases y condiciones', 'Cantidad de descuento / beneficio', 'Vigencia', 'Medios de pago')


def source_hash(row):
    source = {key: row.get(key, '') for key in SOURCE_FIELDS}
    return hashlib.sha256(json.dumps(source, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def reviewed_scopes(row, reviews=None):
    reviews = reviews if reviews is not None else json.loads(MANIFEST.read_text(encoding='utf-8'))
    review = reviews.get(row['URL detalle'])
    if review is None:
        return [row]
    original = ' '.join(f'{key}: {row.get(key, "")}' for key in SOURCE_FIELDS)
    evidence = {'Texto original de la fuente': original, 'Vigencia de identidad campaña': row['Vigencia']}
    if source_hash(row) != review['sha256']:
        return [{**row, **evidence, 'Estado verificacion': 'unconfirmed',
                 'Revisión de variantes': 'La fuente cambió desde la revisión por tarjeta; requiere nueva verificación.'}]
    if review.get('pending'):
        return [{**row, **evidence, 'Estado verificacion': 'unconfirmed', 'Revisión de variantes': review['pending']}]
    return [{**row, **evidence, **variant, 'Estado verificacion': 'official_document'} for variant in review['variants']]
