import unittest
from scrapers.build_gnb_live_offers import dated_weekday_schedule

class DatedScheduleTests(unittest.TestCase):
    def card(self, lines, end='2026-10-18'):
        return {'startDate':'2026-10-09','endDate':end,'lines':lines}
    def test_two_explicit_weekends_keep_saturday_and_exclude_weekdays(self):
        result=dated_weekday_schedule(self.card(['Del Viernes 09 al Domingo 11 de octubre del 2026.', 'Del Viernes 16 al Domingo 18 de octubre del 2026.']))
        self.assertEqual(result, ('viernes, sábado, domingo', 'Desde 2026-10-09 hasta 2026-10-18'))
    def test_skipped_weekend_cannot_become_recurring(self):
        self.assertIsNone(dated_weekday_schedule(self.card(['Del Viernes 09 al Domingo 11 de octubre del 2026.', 'Del Viernes 23 al Domingo 25 de octubre del 2026.'], '2026-10-25')))
    def test_conflicting_api_dates_are_not_repaired_by_guessing(self):
        self.assertIsNone(dated_weekday_schedule(self.card(['Del Viernes 09 al Domingo 11 de octubre del 2026.'])))

    def test_explicit_range_without_weekday_names(self):
        card={'startDate':'2026-10-20','endDate':'2026-10-21','lines':['Del 20 al 21 de octubre del 2026.']}
        self.assertEqual(dated_weekday_schedule(card),('martes, miércoles','Desde 2026-10-20 hasta 2026-10-21'))
    def test_first_and_third_friday_preserve_both_ordinals(self):
        from scrapers.build_gnb_live_offers import day_text
        from promo_backend.normalize import detect_ordinal_weekdays
        days=day_text('20% de descuento','El beneficio aplica el primer y tercer viernes de cada mes.','20% descuento',False)
        self.assertEqual(detect_ordinal_weekdays(days),[{'ordinal':1,'day':'viernes'},{'ordinal':3,'day':'viernes'}])

    def test_installments_do_not_inherit_discount_fridays(self):
        from scrapers.build_gnb_live_offers import day_text
        self.assertEqual(day_text('20% descuento + 6 cuotas','Descuento el primer y tercer viernes de cada mes.','Hasta 6 cuotas sin intereses todos los días',True),'Todos los días')
