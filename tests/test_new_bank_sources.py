import unittest
import json
from pathlib import Path
from scrapers.extract_familiar import parse_cards, terms_pdf
from scrapers.build_familiar_table import convert, date_range
from scrapers.build_gnb_reviewed import build, build_additional, build_page_campaigns
from scrapers.build_gnb_live_offers import build_rows as build_gnb_live_rows
from promo_backend.normalize import normalize_row, detect_month_days


class FamiliarTests(unittest.TestCase):
    def test_preserves_payment_qualifiers_and_pagination(self):
        rows, next_url = parse_cards('''<div class="promotions-collection-item"><p fs-list-field="name">Comercio</p><p fs-list-field="description">Lunes</p><div class="text-s">30% con Platinum</div><div class="text-s">20% con Oro</div><a href="/pdfs/test">Bases</a></div><a class="w-pagination-next" href="?236ef13f_page=2">Siguiente</a>''')
        self.assertEqual(rows[0]['benefit_summary'], '30% con Platinum; 20% con Oro')
        self.assertEqual(rows[0]['review_status'], 'pending_terms_review')
        self.assertTrue(next_url.endswith('?236ef13f_page=2'))

    def test_terms_only_accept_official_cdn_pdf(self):
        self.assertEqual(terms_pdf('<iframe src="https://drive.google.com/viewer?url=https%3A%2F%2Fcdn.prod.website-files.com%2Fx.pdf"></iframe>'), 'https://cdn.prod.website-files.com/x.pdf')
        self.assertIsNone(terms_pdf('<iframe src="https://drive.google.com/viewer?url=http%3A%2F%2Flocalhost%2Fx.pdf"></iframe>'))

    def test_pdf_date_range_does_not_use_listing_expiry(self):
        self.assertEqual(date_range('desde el 16 de septiembre al 30 de diciembre del 2026'), ('2026-09-16','2026-12-30'))
        with self.assertRaises(ValueError):
            date_range('desde el 1 de diciembre hasta el 2 de enero de 2026')

    def test_representative_official_terms(self):
        source = json.loads((Path(__file__).resolve().parents[1] / 'outputs/familiar_extraction_review.json').read_text(encoding='utf-8'))
        records = {r['merchant_name']:r for r in source['records']}
        cycles = convert(records['CYCLES SHOP'])
        self.assertEqual(cycles['Vigencia'], 'Desde 2026-09-16 hasta 2026-12-30')
        self.assertIn('12 cuotas sin intereses con tarjetas clásicas', cycles['Beneficio'])
        self.assertIn('24 cuotas sin intereses con tarjetas oro', cycles['Beneficio'])
        sun = convert(records['SUN HOTEL'])
        self.assertIn('12 cuotas', sun['Beneficio'])
        self.assertIn('24 cuotas', sun['Beneficio'])
        plaza = convert(records['CEROGRADO-PLAZA NORTE'])
        self.assertIn('primer martes de cada mes', plaza['Dia'])
        self.assertIn('5% adicional pagando con QR', plaza['Beneficio'])
        self.assertNotIn('diciembre', plaza['Dia'])
        with self.assertRaisesRegex(ValueError, 'merchant_not_in_terms'):
            convert(records['MOPAR'])

    def test_gnb_card_payment_variants_have_unique_ids_and_correct_caps(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'data/gnb_reviewed_offers.json').read_text(encoding='utf-8'))
        rows = build(data)
        self.assertEqual(len(rows), 8)
        normalized = [normalize_row('GNB', row) for row in rows]
        self.assertEqual(len({row['id'] for row in normalized}), 8)
        self.assertIn('150.000', rows[0]['Montos'])
        self.assertIn('300.000', rows[3]['Montos'])
        self.assertEqual(normalized[3]['offer_kind'], 'premium')
        self.assertNotIn('Clásica', normalized[3]['verified_cards'])
        self.assertEqual(normalized[0]['promotion_days'], ['lunes'])

    def test_gnb_restaurants_preserve_days_shared_cap_and_exceptions(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'data/gnb_restaurants_reviewed.json').read_text(encoding='utf-8'))
        rows = build(data)
        normalized = [normalize_row('GNB', row) for row in rows]
        self.assertEqual(len(rows), 28)
        self.assertEqual(len({row['id'] for row in normalized}), 28)
        self.assertEqual(len({row['Comercio'] for row in rows}), 14)
        for row in normalized:
            self.assertEqual(row['promotion_days'], ['miércoles', 'jueves', 'viernes', 'sábado', 'domingo'])
            self.assertEqual(row['offer_kind'], 'base')
        self.assertIn('1.500.000', rows[0]['Montos'])
        self.assertIn('compartido', rows[0]['Montos'])
        self.assertIn('calculado al 25%', rows[1]['Montos'])
        ola = next(row for row in rows if row['Comercio'] == 'OLA POKE')
        self.assertIn('2026-06-30', ola['Vigencia'])
        self.assertIn('también aplica a pagos vía web', ola['Detalle'])
        emeterio = next(row for row in rows if row['Comercio'] == 'Emeterio')
        self.assertIn('2026-02-06', emeterio['Vigencia'])
        hon = next(row for row in rows if row['Comercio'] == 'Honorio Bar')
        self.assertIn('Encarnación', hon['Locales'])

    def test_gnb_financing_merchants_and_municipalities_are_distinct(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'data/gnb_additional_reviewed.json').read_text(encoding='utf-8'))
        rows = build_additional(data)
        self.assertEqual(len(rows), 19)
        self.assertEqual(len({row['Comercio'] for row in rows}), 15)
        self.assertTrue(all('cuotas sin intereses' in row['Beneficio'] for row in rows if row['Comercio'] != 'Farmacenter'))
        normalized = [normalize_row('GNB', row) for row in rows]
        self.assertEqual(len({row['id'] for row in normalized}), 19)
        self.assertTrue(all(len(row['promotion_days']) == 7 for row in normalized if row['merchant_name'] != 'Farmacenter'))
        pharmacy = [row for row in normalized if row['merchant_name'] == 'Farmacenter']
        self.assertEqual(len(pharmacy), 5)
        self.assertEqual([row.get('effective_percent') for row in pharmacy], [32, 28, 27.75, 23.5, None])
        self.assertTrue(all(row['promotion_days'] == ['lunes'] for row in pharmacy[:4]))
        self.assertEqual(len(pharmacy[4]['promotion_days']), 7)

    def test_gnb_indexed_cards_keep_premium_separate_and_link_source_page(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'data/gnb_page_reviewed.json').read_text(encoding='utf-8'))
        rows = build_page_campaigns(data)
        self.assertEqual(len(rows), 5)
        self.assertEqual([row['Beneficio'] for row in rows[:2]], ['20% de reintegro', '25% de reintegro'])
        self.assertEqual(rows[1]['Tipo de variante'], 'premium')
        self.assertNotIn('Black', rows[0]['Tarjetas verificadas'])
        self.assertIn('/categorias/260', rows[0]['URL detalle'])
        self.assertNotIn('.pdf', rows[0]['URL detalle'])
        self.assertEqual(rows[2]['Beneficio'], 'Hasta 6 cuotas sin intereses')
        self.assertIn('según oferta', rows[3]['Beneficio'])
        self.assertEqual(len({normalize_row('GNB', row)['id'] for row in rows}), 5)

    def test_gnb_live_card_pdf_crosscheck_and_schedule(self):
        root = Path(__file__).resolve().parents[1]
        cards = json.loads((root / 'data/gnb_live_cards_2026-09-22.json').read_text(encoding='utf-8'))
        documents = json.loads((root / 'data/gnb_pdf_text_2026-09-22.json').read_text(encoding='utf-8'))
        self.assertEqual(cards['total'], len(cards['cards']))
        self.assertEqual(cards['total'], 238)
        self.assertEqual(len(documents['documents']), 217)
        self.assertFalse(any(doc['error'] for doc in documents['documents'].values()))

        rows, issues = build_gnb_live_rows()
        self.assertEqual(issues, [])
        by_card = {}
        for row in rows:
            card_id = int(row['URL detalle'].rsplit('/', 1)[-1])
            by_card.setdefault(card_id, []).append(normalize_row('GNB', row))
            self.assertNotIn('.pdf', row['URL detalle'])
        self.assertEqual(len(by_card), 227)
        self.assertTrue({20, 157, 297}.isdisjoint(by_card))
        self.assertEqual(by_card[275][0]['promotion_days'], ['miércoles'])
        self.assertEqual(by_card[392][0]['offer_kind'], 'premium')
        self.assertEqual(by_card[392][1]['offer_kind'], 'base')
        self.assertEqual(len(by_card[145][0]['promotion_days']), 7)
        self.assertEqual(by_card[9][0]['validity'], 'Desde 2026-10-14 hasta 2026-10-14')
        self.assertEqual(by_card[638][0]['month_days'], [17, 18, 19, 20])
        self.assertEqual(by_card[638][0]['last_days_of_month'], 3)
        self.assertEqual(len(by_card[638][1]['promotion_days']), 7)
        self.assertEqual({(rule['ordinal'], rule['day']) for rule in by_card[631][0]['ordinal_weekdays']},
                         {(3, 'jueves'), (3, 'viernes')})
        self.assertIn('29 de diciembre', by_card[660][0]['validity'])
        self.assertEqual([x['benefit_summary'] for x in by_card[639]][:2],
                         ['25% de reintegro con QR', '20% de reintegro con tarjeta física'])
        self.assertEqual(detect_month_days('del 1 al 10 de cada mes'), list(range(1, 11)))
