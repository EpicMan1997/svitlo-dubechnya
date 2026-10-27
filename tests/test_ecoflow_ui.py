"""Contract checks for the unauthenticated, read-only EcoFlow prototype."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "site/index.html").read_text(encoding="utf-8")
JS = (ROOT / "site/ecoflow.js").read_text(encoding="utf-8")
CSS = (ROOT / "site/ecoflow.css").read_text(encoding="utf-8")
SW = (ROOT / "site/sw.js").read_text(encoding="utf-8")


class EcoFlowPreviewContract(unittest.TestCase):
    def test_all_four_locations_are_listed(self):
        for key in ("dacha:", "home:", "solovky:", "naumenky:"):
            self.assertIn(key, JS)
        for name in ("DELTA Pro 3", "DELTA 3 Plus", "RIVER 3 Plus Wireless",
                     "PowerOcean", "RIVER 2", "Додаткова батарея DELTA 2"):
            self.assertIn(name, JS)
        self.assertEqual(JS.count("capacityWh: 4096"), 2)
        self.assertEqual(JS.count("capacityWh: 1024"), 5)
        self.assertEqual(JS.count("capacityWh: 286"), 1)
        self.assertEqual(JS.count("capacityWh: 256"), 1)
        self.assertEqual(JS.count("capacityWh: 5000"), 1)

    def test_demo_not_presented_as_live_telemetry(self):
        self.assertIn("API не підключено", HTML)
        self.assertIn("відсотки та вати вигадані для макета", HTML)
        self.assertIn("Демо", JS)
        self.assertIn("Не підключено", JS)
        self.assertNotRegex(JS, r"\bfetch\s*\(|XMLHttpRequest|WebSocket")
        self.assertIn("disabled", JS)

    def test_admin_toggle_is_ui_only(self):
        self.assertIn('id="ecoAdminToggle"', HTML)
        self.assertIn('role="switch"', HTML)
        self.assertIn('aria-checked="false"', HTML)
        self.assertIn("setAdminPreview(false)", JS)
        self.assertIn("toggle.addEventListener('click'", JS)
        self.assertIn("не виконує автентифікацію", HTML)
        self.assertIn(".eco-shell.is-admin-preview", CSS)

    def test_capacity_is_proportional_and_powerocean_is_known(self):
        self.assertIn("d.capacityWh / MAX_BATTERY_WH", JS)
        self.assertIn("MAX_BATTERY_WH = 5000", JS)
        self.assertIn("flex-grow:' + d.capacityWh", JS)
        self.assertIn("capacityWh: 5000, inverterKw: 6, systemPowerKw: 3, twoBatterySystemKw: 6, batteryCount: 1", JS)
        self.assertIn("інвертор ", JS)
        self.assertIn("потужність системи зараз ", JS)
        self.assertIn('id="eco-capacity-strip"', HTML)

    def test_location_changer_and_pwa_integration(self):
        self.assertIn("svitlo:location-change", JS)
        self.assertIn("new CustomEvent('svitlo:location-change'", HTML)
        self.assertNotIn('href="#ecoflow"', HTML)
        self.assertIn('<section class="eco-shell"', HTML)
        self.assertIn('"./ecoflow.css"', SW)
        self.assertIn('"./ecoflow.js"', SW)


    def test_device_section_first_and_header_rearranged(self):
        self.assertLess(HTML.index(">Станції та акумулятори<"),
                        HTML.index(">Огляд батарей<"))
        self.assertIn('class="site-clock" id="clock"', HTML)
        self.assertIn('</small></button></div></div><div class="site-clock" id="clock"', HTML)
        self.assertLess(HTML.index('id="locationMenu"'), HTML.index('id="clock"'))
        self.assertLess(HTML.index('id="clock"'), HTML.index('id="ecoAdminToggle"'))
        self.assertEqual(HTML.count('id="clock"'), 1)
        self.assertIn('<span class="eco-admin-toggle-label">Admin</span>', HTML)
        self.assertIn('class="eco-admin-shield"', HTML)
        self.assertNotIn('Admin <small>Preview</small>', HTML)
        self.assertIn('main > header #clock', CSS)
        self.assertIn('grid-template-columns:minmax(0,1fr) max-content minmax(0,1fr)', CSS)
        self.assertIn('main > .tabs .tomorrow-tab{margin-left:auto}', CSS)
        self.assertIn('width:calc(100% - 284px)', CSS)
        self.assertIn('main > .tabs{width:100%;padding-right:14px}', CSS)
        self.assertIn(".eco-admin-toggle[aria-checked=\"true\"]", CSS)

    def test_expansion_batteries_share_an_explicit_pair(self):
        self.assertIn("parentId: 'dp3'", JS)
        self.assertIn("parentId: 'd2'", JS)
        self.assertIn("function renderDeviceGrid(devices)", JS)
        self.assertIn("const addons = new Map(", JS)
        self.assertIn("ids.has(d.parentId)", JS)
        self.assertIn("deviceView(d, true) + deviceView(addon, true)", JS)
        self.assertIn("niceWh(total)", JS)
        self.assertIn('class="eco-pair-grid"', JS)
        self.assertIn(".eco-pair-grid", CSS)
        self.assertIn("@media(max-width:760px)", CSS)
        self.assertIn("Параметри цього акумулятора керуються через основну станцію", JS)



if __name__ == "__main__":
    unittest.main()
