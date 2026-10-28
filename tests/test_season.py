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

    def test_change_events_use_schedule_date_not_detection_date(self):
        from season import archive_changes
        iso='2026-10-27'
        state={'days':{iso:day(iso,[['09:00','11:00']])}, 'logs':[
          {'date':iso,'at':'2026-10-26T22:10+02:00','kind':'published','message':'Опубліковано графік'},
          {'date':iso,'at':'2026-10-27T10:00+02:00','kind':'changed','before':[['09:00','12:00']],
           'after':[['09:00','11:00']],'message':'Змінено графік'},
          {'date':iso,'at':'2026-10-27T11:00+02:00','kind':'changed','before':[['09:00','11:00']],
           'after':[['09:00','12:00']],'message':'Змінено графік'},
        ]}
        archive={'seasons':{}}
        from season import archive_completed
        archive_completed(archive,state,date(2026,10,28))
        archive_completed(archive,state,date(2026,10,28))
        entry=season_payload(archive,date(2026,10,28))['locations']['dacha']
        self.assertEqual(entry['total_detected_changes'],2)
        self.assertEqual(entry['average_changes_per_tracked_day'],2)
        self.assertEqual(entry['max_changes'],{'date':iso,'count':2})
        self.assertEqual(entry['days_with_changes'],1)
        self.assertEqual(entry['days'][iso]['detected_changes'],2)
        self.assertEqual(len(archive['seasons']['2026/27']['change_history']['dacha'][iso]['events']),2)

    def test_unmonitored_and_missing_days_do_not_become_zero_change_days(self):
        old={'days':{
           '2026-10-26':day('2026-10-26',[['08:00','10:00']]),
           '2026-10-27':day('2026-10-27',[]),
        }, 'logs':[{'date':'2026-10-27','at':'2026-10-27T00:01+02:00',
                    'kind':'published','message':'Опубліковано графік'}]}
        archive=archive_completed({'seasons':{}},old,date(2026,10,28))
        result=season_payload(archive,date(2026,10,28))['locations']['dacha']
        self.assertEqual(result['outage_days'],1)
        self.assertEqual(result['zero_outage_days'],1)
        self.assertEqual(result['recorded_days'],2)
        self.assertEqual(result['tracked_change_days'],1)
        self.assertEqual(result['total_detected_changes'],0)
        self.assertEqual(result['average_changes_per_tracked_day'],0)
        self.assertIsNone(result['days']['2026-10-26']['detected_changes'])
        self.assertEqual(result['days']['2026-10-27']['detected_changes'],0)
        self.assertEqual(result['first_recorded_outage'],'2026-10-26')
        self.assertEqual(result['days_since_first_recorded_outage'],2)
        self.assertEqual(result['scheduled_intervals'],1)
        self.assertEqual(result['average_interval_minutes'],120)
        self.assertEqual(result['coverage_days'],2)
        self.assertEqual(result['elapsed_days'],27)

    def test_historic_october_backfill_has_earlier_verified_dacha_days(self):
        import json
        source=json.loads(Path(__file__).resolve().parents[1].joinpath(
            'state/season_backfill.json').read_text(encoding='utf-8'))
        dates=('2026-10-07','2026-10-11','2026-10-12','2026-10-13','2026-10-14',
               '2026-10-16','2026-10-17','2026-10-18','2026-10-19','2026-10-20','2026-10-21')
        for d in dates:
            entry=source[d]['dacha']
            self.assertEqual(len(set(entry['sources'])),2)
            self.assertIn('bezsvitla.com.ua',entry['sources'][0])
            self.assertTrue(entry['outages'])
        self.assertEqual(source['2026-10-17']['dacha']['outages'],
                         [['00:00','02:00'],['08:30','12:00'],['18:30','19:00']])
        self.assertEqual(source['2026-10-20']['dacha']['outages'],
                         [['10:00','13:00'],['20:00','22:00']])

    def test_historic_backfill_does_not_override_automatically_observed_days(self):
        from season import archive_external, archive_completed
        iso='2026-10-24'
        first={'days':{iso:day(iso,[['08:00','12:00']])}}
        archive=archive_completed({'seasons':{}},first,date(2026,10,28))
        archive_external(archive,{iso:{'dacha':{
          'outages':[['09:00','12:00']],
          'sources':['https://example.org/a','https://example.com/b']}}},date(2026,10,28))
        stats=season_payload(archive,date(2026,10,28))['locations']['dacha']
        self.assertEqual(stats['total_minutes'],240)
        self.assertEqual(stats['historical_days'],0)
        other={'2026-10-23':{'dacha':{'outages':[['10:00','12:00']],
                                     'sources':['https://example.org/a','https://example.com/b']}}}
        archive_external(archive,other,date(2026,10,28))
        stats=season_payload(archive,date(2026,10,28))['locations']['dacha']
        self.assertEqual(stats['historical_days'],1)
        self.assertEqual(stats['total_minutes'],360)
        self.assertIsNone(stats['average_changes_per_tracked_day'])
        archive_completed(archive,first,date(2026,10,28))
        self.assertEqual(season_payload(archive,date(2026,10,28))['locations']['dacha']['recorded_days'],2)

    def test_event_only_days_wait_for_confirmed_completed_schedule(self):
        from season import archive_changes
        archive={'seasons':{}}
        event={'date':'2026-10-27','at':'2026-10-27T12:00+02:00','kind':'changed',
               'message':'Змінено графік'}
        archive_changes(archive,{'logs':[event]},date(2026,10,27))
        result=season_payload(archive,date(2026,10,28))['locations']['dacha']
        self.assertIsNone(result['average_changes_per_tracked_day'])
        self.assertEqual(result['tracked_change_days'],0)

    def test_latest_confirmed_revision_replaces_prior_snapshot(self):
        iso='2026-10-26'
        state={'days':{iso:day(iso,[['08:00','12:00']])}}
        archive=archive_completed({'seasons':{}},state,date(2026,10,28))
        state['days'][iso]=day(iso,[['08:00','13:00']])
        archive_completed(archive,state,date(2026,10,28))
        self.assertEqual(season_payload(archive,date(2026,10,28))['locations']['dacha']['total_minutes'],300)

if __name__=='__main__':
    unittest.main()
