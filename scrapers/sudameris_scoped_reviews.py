"""Apply exact, document-hash-bound Sudameris reviews without guessing renewals."""
import hashlib
import json
import requests
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


def apply_scoped_reviews(rows, review, fetch=fetch_pdf, failures=None):
    # Validate every document and every identity before mutating any row.
    invalid = {}
    for url, expected in review['documents'].items():
        try:
            if hashlib.sha256(fetch(url)).hexdigest() != expected:
                raise ValueError('Reviewed Sudameris document changed: ' + url)
        except (requests.RequestException, ValueError) as error:
            if failures is None:
                raise
            invalid[url] = str(error)
            failures.append({'campaign': 'scoped_review', 'url': url, 'reason': str(error)})

    def blocked(item):
        # Legacy manifests without per-item dependencies depend on every document.
        return [url for url in item.get('documents', review['documents']) if url in invalid]

    def quarantine(row, urls):
        row['Estado verificacion'] = 'unconfirmed'
        row['Advertencia de fuente'] = '; '.join(invalid[url] for url in urls)

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
            message = 'Missing reviewed Sudameris identity: ' + str(key)
            if failures is None:
                raise ValueError(message)
            failures.append({'campaign': key[1], 'url': key[0], 'reason': message})
            continue
        row = index[key]
        if blocked(item):
            quarantine(row, blocked(item))
            continue
        if fingerprint(row, review['fingerprint_fields']) not in item['accepted_sha256']:
            message = 'Reviewed Sudameris row changed: ' + str(key)
            if failures is None:
                raise ValueError(message)
            row['Estado verificacion'] = 'unconfirmed'
            row['Advertencia de fuente'] = message
            failures.append({'campaign': key[1], 'url': key[0], 'reason': message})
            continue
        row.update(item['patch'])
    for item in review['additions']:
        row = item['row']
        key = selector(row)
        if blocked(item):
            if key in index:
                quarantine(index[key], blocked(item))
            continue
        if key in index:
            existing_hash = fingerprint(index[key], review['fingerprint_fields'])
            if existing_hash != fingerprint(row, review['fingerprint_fields']) and existing_hash not in item.get('accepted_sha256', []):
                message = 'Scoped Sudameris merchant changed: ' + str(key)
                if failures is None:
                    raise ValueError(message)
                index[key]['Estado verificacion'] = 'unconfirmed'
                index[key]['Advertencia de fuente'] = message
                failures.append({'campaign': key[1], 'url': key[0], 'reason': message})
                continue
            index[key].update(row)
        else:
            index[key] = dict(row)
            result.append(index[key])
    return result


def apply_saved_reviews(rows, path=Path('data/sudameris_scoped_reviews.json'), failures=None):
    if not path.exists():
        return rows
    return apply_scoped_reviews(rows, json.loads(path.read_text(encoding='utf-8')), failures=failures)
