"""Evidence-bound October Shell campaign; keep stable card variant identities."""
import hashlib


def apply_review(promotions, review):
    for promo in promotions:
        if promo.get('bank') != 'Itaú' or promo.get('source_url') != review['source_url']:
            continue
        fingerprint = hashlib.sha256(promo.get('raw_detail', '').encode()).hexdigest()
        if fingerprint != review['offers'].get(promo['id']):
            promo['source_verification'] = 'unconfirmed'
            promo['source_warning'] = 'La fuente Shell cambió; revisar la campaña antes de reactivarla.'
            continue
        promo['original_source_text'] = promo['raw_detail']
        promo['validity'] = f"Desde {promo['terms']['starts_on']} hasta {review['ends_on']}"
        promo['terms']['ends_on'] = review['ends_on']
        promo['raw_detail'] = promo['raw_detail'].replace('2026-12-31', review['ends_on'])
        promo['source_page_url'] = review['document_url']
        promo['source_document_url'] = review['document_url']
        promo['source_reviewed_at'] = review['reviewed_on']
        promo['source_verification'] = 'official_document'
        promo['source_warning'] = 'Campaña y estaciones adheridas verificadas para octubre, hasta el 26/10/2026.'
    return promotions
