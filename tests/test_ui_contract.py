from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT.joinpath("site/index.html").read_text(encoding="utf-8")


class VisualStatusContract(unittest.TestCase):
    """Source agreement and time since GitHub checked are distinct concepts."""

    def test_recent_source_consensus_does_not_require_fresh_github_job(self):
        self.assertIn("function currentStatus(e){return e?.status||'unknown'}", HTML)
        self.assertNotIn("if(s==='normal'&&(age>35||age< -5))s='delayed'", HTML)

    def test_four_matching_sources_are_still_verified(self):
        self.assertIn("const healthy=status==='normal'&&allMatch>=2", HTML)
        self.assertIn("healthy?'Графік підтверджено'", HTML)

    def test_old_source_is_independently_reported(self):
        self.assertIn("old:'Не оновлено'", HTML)
        self.assertIn("e.source_reports||{}", HTML)

    def test_age_only_colours_freshness_ring(self):
        self.assertIn("function updateRefreshRing(){", HTML)
        self.assertIn("ageLimit=10*60", HTML)
        self.assertNotIn("status==='delayed'", HTML)
        self.assertIn("age>=15*60", HTML)

    def test_github_status_does_not_confuse_development_push_with_scheduled_refresh(self):
        self.assertIn("event=workflow_dispatch", HTML)
        self.assertIn("function events(){", HTML)
        self.assertIn("changeDailyCount", HTML)

    def test_source_palette_is_shared(self):
        self.assertIn("const palette=sourcePalette", HTML)
        self.assertIn("colors=sourcePalette", HTML)
        self.assertIn("const sourcePalette={", HTML)

    def test_five_current_source_colors_are_distinct(self):
        import re
        palette = re.search(r"const sourcePalette=\{(.*?)\};", HTML, re.S)
        self.assertIsNotNone(palette)
        colors = dict(re.findall(r"'([^']+)':'(#[0-9a-fA-F]{6})'", palette.group(1)))
        names = ['Карта світла', 'КолиСвітло', 'КолиБуде', 'Київщина.info', 'Alerts Energy']
        self.assertEqual(len(set(colors[name] for name in names)), 5)
        self.assertEqual(colors['ДТЕК'], colors['Київщина.info'])

    def test_historic_event_does_not_claim_unverified_first_signal(self):
        self.assertIn("Одне з джерел, що підтвердили зміну:", HTML)
        self.assertIn("const name=first||confirmed;", HTML)
        self.assertIn("item.sources_confirmed.find(x=>sourcePalette[x])", HTML)
        self.assertIn("info.first?'Перший сигнал':'Підтвердив'", HTML)
        self.assertIn("change-source-name", HTML)


if __name__ == '__main__':
    unittest.main()
