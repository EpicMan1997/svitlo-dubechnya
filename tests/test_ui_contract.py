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

    def test_yesterday_archive_and_comparison(self):
        refresh = ROOT.joinpath("scripts/refresh.py").read_text(encoding="utf-8")
        self.assertIn("'days':visible_days", refresh)
        self.assertIn("'days':visible_days,'logs':logs,'operator':", refresh)
        self.assertIn("if k>=(today-timedelta(days=2)).isoformat()", refresh)
        self.assertIn("function changeComparison(parts){", HTML)
        self.assertIn("hoursAndMinutes(yMinutes)+' без світла'", HTML)
        self.assertIn("yesterday-count.zero", HTML)
        self.assertIn("yesterday-count.few", HTML)
        self.assertIn("yesterday-count.many", HTML)
        self.assertIn("item.date===yesterday&&eventKind(item)==='changed'", HTML)

    def test_yesterday_compact_and_unknown_archive(self):
        self.assertIn("'Зміни і графік '+yDate", HTML)
        self.assertIn("hoursAndMinutes(yMinutes)+' без світла'", HTML)
        self.assertIn(".yesterday-count.zero{color:#94a3b8}", HTML)
        self.assertIn("['normal','stale','suspended'].includes(saved.status)", HTML)
        self.assertNotIn("Графік за цей день не збережений", HTML)
        self.assertNotIn("Зміни графіка: '+count", HTML)

    def test_open_tomorrow_tab_marks_every_new_version_as_seen(self):
        self.assertIn("if(tab==='tomorrow'&&tomorrowFingerprint()){markTomorrowSeen();updateTomorrowTab()}", HTML)
        self.assertIn("setInterval(reload,30000)", HTML)

    def test_historic_event_does_not_claim_unverified_first_signal(self):
        self.assertIn("Одне з джерел, що підтвердили зміну:", HTML)
        self.assertIn("const name=first||confirmed;", HTML)
        self.assertIn("item.sources_confirmed.find(x=>sourcePalette[x])", HTML)
        self.assertIn("info.first?'Перший сигнал':'Підтвердив'", HTML)
        self.assertIn("change-source-name", HTML)


if __name__ == '__main__':
    unittest.main()
