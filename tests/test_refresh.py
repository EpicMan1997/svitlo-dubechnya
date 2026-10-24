import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import normalize,pairs,parse_bez,parse_kolysvitlo,parse_kolybude,choose,change
D=date(2026,10,24)
E=(('08:00','12:00'),('18:30','22:30'))
B='<h1>Вища Дубечня на 24.10.2026</h1><h3>Графік Черга 3.1</h3>00:00 – 08:00 08:00 – 12:00 12:00 – 18:30 18:30 – 22:30 22:30 – 24:00 Зберегти підчергу'
K='Сьогодні, 24 жовтня 2026 р. 3.1 Немає світла: 08:00–12:00, 18:30–22:30 3.2 Немає світла: 08:00–12:00'
KB='Сьогодні, 24 жовтня 2026. Черга 3.1: 08:00–12:00, 18:30–22:30 Черга 3.2: 08:00–12:00'
class Tests(unittest.TestCase):
 def test_bez(self):self.assertIn(E,parse_bez(B,D)['candidates'])
 def test_koly(self):self.assertEqual(parse_kolysvitlo(K,D,D),E)
 def test_bude(self):self.assertEqual(parse_kolybude(KB,D,D),E)
 def test_concensus(self):self.assertEqual(choose(D,parse_bez(B,D),E,None,{})['status'],'normal')
 def test_conflict(self):self.assertEqual(choose(D,{'candidates':[E],'updated':'','unpublished':False},(('15:00','16:00'),),None,{})['status'],'unknown')
 def test_stale(self):self.assertEqual(choose(D,{'candidates':[],'updated':'','unpublished':False},None,None,{'date':D.isoformat(),'status':'normal','outages':[['08:00','12:00']]})['status'],'stale')
 def test_tomorrow(self):self.assertIsNone(parse_kolysvitlo(K,date(2026,10,25),D))
 def test_zero(self):self.assertEqual(parse_kolysvitlo('Сьогодні, 24 жовтня 2026 р. 3.1 Без відключень 3.2',D,D),())
 def test_merge(self):self.assertEqual(normalize([('12:00','13:00'),('13:00','14:00')]),(('12:00','14:00'),))
 def test_unpublished(self):self.assertTrue(parse_bez('На 25.10.2026 ще не опубліковано',date(2026,10,25))['unpublished'])
 def test_no_wrong_date(self):self.assertEqual(parse_bez(B,date(2026,10,25))['candidates'],[])
 def test_no_repeat(self):self.assertIsNone(change({'status':'normal','outages':[['08:00','12:00']]},{'status':'normal','outages':[['08:00','12:00']]}))
