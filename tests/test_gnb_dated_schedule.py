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
