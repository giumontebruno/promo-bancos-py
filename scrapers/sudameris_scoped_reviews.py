"""Apply exact, document-hash-bound Sudameris reviews without guessing renewals."""
import hashlib
import json
from pathlib import Path
try:
    from .sudameris_document_links import fetch_pdf
except ImportError:
    from sudameris_document_links import fetch_pdf


def fingerprint(row, fields):
    values = {key: row.get(key, '') for key in fields}
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def selector(row):
    return tuple(row.get(key, '') for key in ('URL', 'Comercio/Promoción', 'Variante'))


def apply_scoped_reviews(rows, review, fetch=fetch_pdf):
    # Validate every document and every identity before mutating any row.
    for url, expected in review['documents'].items():
        if hashlib.sha256(fetch(url)).hexdigest() != expected:
            raise ValueError('Reviewed Sudameris document changed: ' + url)
    result = [dict(row) for row in rows]
    index = {}
    for row in result:
        key = selector(row)
        if key in index:
            raise ValueError('Duplicate Sudameris scoped identity: ' + str(key))
        index[key] = row
    for item in review['mutations']:
        key = selector(item['selector'])
        if key not in index:
            raise ValueError('Missing reviewed Sudameris identity: ' + str(key))
        row = index[key]
        if fingerprint(row, review['fingerprint_fields']) not in item['accepted_sha256']:
            raise ValueError('Reviewed Sudameris row changed: ' + str(key))
        row.update(item['patch'])
    for item in review['additions']:
        row = item['row']
        key = selector(row)
        if key in index:
            if fingerprint(index[key], review['fingerprint_fields']) != fingerprint(row, review['fingerprint_fields']):
                raise ValueError('Scoped Sudameris merchant changed: ' + str(key))
            index[key].update(row)
        else:
            index[key] = dict(row)
            result.append(index[key])
    return result


def apply_saved_reviews(rows, path=Path('data/sudameris_scoped_reviews.json')):
    if not path.exists():
        return rows
    return apply_scoped_reviews(rows, json.loads(path.read_text(encoding='utf-8')))
