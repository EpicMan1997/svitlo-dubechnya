"""Seasonal schedule archive: confirmed, finished days only."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from season import confirmed_record, archive_completed, season_payload, season_for


def day(iso, outages, sources=('Карта світла', 'Alerts Energy'), status='normal'):
    return {'date': iso, 'status': status, 'sources': list(sources), 'outages': outages}


class SeasonTests(unittest.TestCase):
    def test_season_bounds(self):
        self.assertEqual(season_for(date(2026, 10, 28))[0], '2026/27')
        self.assertEqual(season_for(date(2027, 2, 15))[0], '2026/27')
        self.assertEqual(season_for(date(2027, 10, 1))[0], '2027/28')

    def test_requires_two_sources_and_valid_ranges(self):
        iso='2026-10-27'
        self.assertIsNone(confirmed_record(iso, day(iso, [['09:00','11:00']], sources=('Карта світла',))))
        self.assertIsNone(confirmed_record(iso, day(iso, [], status='stale')))
        self.assertIsNone(confirmed_record(iso, day(iso, [['09:00','12:00'],['11:00','13:00']])))
        self.assertIsNone(confirmed_record(iso, day(iso, [['12:00','09:00']])))
        self.assertIsNone(confirmed_record(iso, day(iso, [['09:00','11:00']], sources=())))
        self.assertEqual(confirmed_record(iso, day(iso, []))['total_minutes'], 0)

    def test_archive_completed_days_only_and_idempotent(self):
        old={'days':{
            '2026-10-26':day('2026-10-26',[['08:00','12:00'],['18:00','21:00']]),
            '2026-10-27':day('2026-10-27',[],status='unknown'),
            '2026-10-28':day('2026-10-28',[['07:00','09:00']]),
            '2026-10-29':day('2026-10-29',[['07:00','09:00']])
          },
          'locations':{'home':{'days':{'2026-10-27':day('2026-10-27',[])}}}}
        archive_completed_data=archive_completed({'seasons':{}},old,date(2026,10,28))
        same=archive_completed(archive_completed_data,old,date(2026,10,28))
        self.assertEqual(archive_completed_data,same)
        stats=season_payload(same,date(2026,10,28))['locations']
        self.assertEqual(stats['dacha']['recorded_days'],1)
        self.assertEqual(stats['dacha']['total_minutes'],420)
        self.assertEqual(stats['dacha']['longest']['minutes'],240)
        self.assertEqual(stats['home']['recorded_days'],1)
        self.assertEqual(stats['home']['average_minutes'],0)
        self.assertIsNone(stats['solovky']['average_minutes'])
        self.assertNotIn('2026-10-28',stats['dacha']['days'])

    def test_latest_confirmed_revision_replaces_prior_snapshot(self):
        iso='2026-10-26'
        state={'days':{iso:day(iso,[['08:00','12:00']])}}
        archive=archive_completed({'seasons':{}},state,date(2026,10,28))
        state['days'][iso]=day(iso,[['08:00','13:00']])
        archive_completed(archive,state,date(2026,10,28))
        self.assertEqual(season_payload(archive,date(2026,10,28))['locations']['dacha']['total_minutes'],300)

if __name__=='__main__':
    unittest.main()
