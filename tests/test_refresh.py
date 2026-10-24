import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import normalize,pairs,parse_bez,parse_kolysvitlo,parse_kolybude,parse_kyivshchyna,parse_svitlolive,source_reports,choose,change,parse_city_bez,parse_city_koly,parse_city_bude,city_sources,CITY_LOCATIONS
D=date(2026,10,24)
E=(('08:00','12:00'),('18:30','22:30'))
B='<h1>Вища Дубечня на 24.10.2026</h1><h3>Графік Черга 3.1</h3>00:00 – 08:00 08:00 – 12:00 12:00 – 18:30 18:30 – 22:30 22:30 – 24:00 Зберегти підчергу'
K='Сьогодні, 24 жовтня 2026 р. 3.1 Немає світла: 08:00–12:00, 18:30–22:30 3.2 Немає світла: 08:00–12:00'
KB='Сьогодні, 24 жовтня 2026. Черга 3.1: 08:00–12:00, 18:30–22:30 Черга 3.2: 08:00–12:00'
class Tests(unittest.TestCase):
 def test_bez(self):self.assertIn(E,parse_bez(B,D)['candidates'])
 def test_koly(self):self.assertEqual(parse_kolysvitlo(K,D,D),E)
 def test_koly_real_navigation(self):
  site='Графік відключень Київська область Сьогодні, 24 жовтня 2026 р. Моя черга Оберіть свою чергу Усі черги Сьогодні Завтра 0 6 12 18 24 1.1 6–8:30 Немає світла: 06:00–08:30 2.2 15–19 Немає світла: 15:00–19:00 3.1 8–12 18:30–22:30 Немає світла: 08:00–12:00, 18:30–22:30 3.2 8–12 Немає світла: 08:00–12:00 Графік на завтра ще не опубліковано'
  self.assertEqual(parse_kolysvitlo(site,D,D),E)
 def test_koly_tomorrow_if_date_published(self):
  site='Сьогодні, 24 жовтня 2026 р. 3.1 Немає світла: 08:00–12:00 3.2 Завтра, 25 жовтня 2026 р. 3.1 Немає світла: 09:30–11:00 3.2'
  self.assertEqual(parse_kolysvitlo(site,date(2026,10,25),D),(('09:30','11:00'),))
 def test_bude(self):self.assertEqual(parse_kolybude(KB,D,D),E)
 def test_concensus(self):self.assertEqual(choose(D,parse_bez(B,D),E,None,{})['status'],'normal')
 def test_conflict(self):self.assertEqual(choose(D,{'candidates':[E],'updated':'','unpublished':False},(('15:00','16:00'),),None,{})['status'],'unknown')
 def test_stale(self):self.assertEqual(choose(D,{'candidates':[],'updated':'','unpublished':False},None,None,{'date':D.isoformat(),'status':'normal','outages':[['08:00','12:00']]})['status'],'stale')
 def test_tomorrow(self):self.assertIsNone(parse_kolysvitlo(K,date(2026,10,25),D))
 def test_zero(self):self.assertEqual(parse_kolysvitlo('Сьогодні, 24 жовтня 2026 р. 3.1 Без відключень 3.2',D,D),())
 def test_merge(self):self.assertEqual(normalize([('12:00','13:00'),('13:00','14:00')]),(('12:00','14:00'),))
 def test_unpublished(self):self.assertTrue(parse_bez('На 25.10.2026 ще не опубліковано',date(2026,10,25))['unpublished'])
 def test_no_wrong_date(self):self.assertEqual(parse_bez(B,date(2026,10,25))['candidates'],[])
 def test_region_dated(self):
  page='Графік сьогодні 24.10.2026 Черга 3.1 8 год без світла без світла: 08:00–12:00 18:30–22:30 Черга 3.2'
  self.assertEqual(parse_kyivshchyna(page,D,D),E)
 def test_region_refuse_tomorrow(self):
  page='24.10.2026 Черга 3.1 без світла: 08:00–12:00 Черга 3.2'
  self.assertIsNone(parse_kyivshchyna(page,date(2026,10,25),D))
 def test_svitlolive_partial_not_exact(self):
  cells=['●']*24
  for i in range(8,12):cells[i]='✕'
  cells[18]='%'
  for i in range(19,22):cells[i]='✕'
  page='Графік на сьогодні - черга 3.1 24.10.2026 Черга 3.1 '+' '.join(cells)+' Графік на завтра - черга 3.1'
  report=parse_svitlolive(page,D,D)
  self.assertEqual(report['outages'],(('08:00','12:00'),('19:00','22:00')))
  self.assertEqual(report['partial'],['18:00–19:00'])
 def test_source_reports_not_faked(self):
  consensus={'date':D.isoformat(),'status':'normal','outages':[list(x) for x in E],'url':'https://example.com'}
  result=source_reports(consensus,{'candidates':[E],'updated':'','unpublished':False},E,E,(('08:00','12:00'),('18:30','22:00')),None,{})
  self.assertEqual(len(result),4)
  self.assertEqual(result['КолиСвітло']['status'],'match')
  self.assertEqual(result['Київщина.info']['status'],'diff')
  self.assertNotIn('Svitlo.live',result)

 def test_kyiv_address_groups(self):
  self.assertEqual(CITY_LOCATIONS['obolonskyi54']['group'],'4.1')
  self.assertEqual(CITY_LOCATIONS['ivasiuka43']['group'],'4.1')
  self.assertEqual(CITY_LOCATIONS['azov28b']['group'],'10.1')
 def test_kyiv_bez_queue(self):
  page='<h1>Графік у Києві на 24.10.2026</h1>Графік Черга 4.1 00:00 – 07:30 07:30 – 11:00 11:00 – 16:30 16:30 – 20:00 20:00 – 24:00 Зберегти підчергу'
  result=parse_city_bez(page,D,'4.1')
  self.assertIn((('07:30','11:00'),('16:30','20:00')),result['candidates'])
 def test_kyiv_colysvitlo(self):
  page='Графік Київ Сьогодні, 24 жовтня 2026 р. Усі групи Сьогодні Завтра 0 6 12 18 24 3.1 Немає світла: 06:00–07:00 4.1 7:30–11 16:30–20 Немає світла: 07:30–11:00, 16:30–20:00 4.2 Без відключень 10.1 0–3:30 12–15:30 Немає світла: 00:00–03:30, 12:00–15:30 11.1 Без відключень'
  self.assertEqual(parse_city_koly(page,D,D,'4.1'),(('07:30','11:00'),('16:30','20:00')))
  self.assertEqual(parse_city_koly(page,D,D,'10.1'),(('00:00','03:30'),('12:00','15:30')))
 def test_kyiv_kolybude_reject_old_day(self):
  page='Графік відключень світла у Києві на сьогодні, 17 жовтня, Черга 4.1: 22:00–24:00'
  self.assertIsNone(parse_city_bude(page,D,D,'4.1'))
 def test_city_source_dtek_not_faked(self):
  expected={'date':D.isoformat(),'status':'normal','outages':[['07:30','11:00']],'sources':['КолиСвітло','КолиБуде']}
  result=city_sources(expected,{'candidates':[]},(('07:30','11:00'),),(('07:30','11:00'),),'https://example.com',{})
  self.assertEqual(result['ДТЕК']['status'],'unavailable')
  self.assertEqual(result['КолиСвітло']['status'],'match')
 def test_no_repeat(self):self.assertIsNone(change({'status':'normal','outages':[['08:00','12:00']]},{'status':'normal','outages':[['08:00','12:00']]}))
