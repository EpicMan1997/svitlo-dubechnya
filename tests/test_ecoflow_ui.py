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

    def test_disconnected_device_values_are_not_claimed_as_live(self):
        self.assertIn("Не підключено", HTML)
        self.assertIn("Відсотки та потужності поки не надходять", HTML)
        panel = HTML.split('<section class="eco-shell"', 1)[1].split('</section>', 1)[0]
        self.assertTrue(panel)
        self.assertNotRegex(panel + JS, r"(?i)демо|демонстрац|макет|preview")
        self.assertNotRegex(JS, r"\bfetch\s*\(|XMLHttpRequest|WebSocket")
        self.assertIn("disabled", JS)

    def test_admin_toggle_is_ui_only(self):
        self.assertIn('id="ecoAdminToggle"', HTML)
        self.assertIn('role="switch"', HTML)
        self.assertIn('aria-checked="false"', HTML)
        self.assertIn("setAdminMode(false)", JS)
        self.assertIn("toggle.addEventListener('click'", JS)
        self.assertIn("Захищене підключення ще не налаштоване", HTML)
        self.assertIn(".eco-shell.is-admin-mode", CSS)

    def test_capacity_is_proportional_and_powerocean_is_known(self):
        self.assertIn("flex-grow:' + d.capacityWh", JS)
        self.assertIn("capacityWh: 5000, inverterKw: 6, systemPowerKw: 3, twoBatterySystemKw: 6, batteryCount: 1", JS)
        self.assertIn("Інвертор ", JS)
        self.assertIn("d.systemPowerKw", JS)
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

    def test_expansion_batteries_are_one_system_card(self):
        self.assertIn("parentId: 'dp3'", JS)
        self.assertIn("parentId: 'd2'", JS)
        self.assertIn("function renderDeviceGrid(devices)", JS)
        self.assertIn("const addons = new Map(", JS)
        self.assertIn("ids.has(d.parentId)", JS)
        self.assertIn("return addon ? systemView(d, addon) : deviceView(d);", JS)
        self.assertIn('class="eco-system eco-system-paired', JS)
        self.assertIn('class="eco-system-parts"', JS)
        self.assertIn("batteryPart(main, 'Основна')", JS)
        self.assertIn("batteryPart(addon, 'Додаткова')", JS)
        self.assertIn("niceWh(capacityWh)", JS)
        self.assertIn(".eco-system-parts{display:grid", CSS)
        self.assertIn("formatAutonomy(capacityWh, chargePct, outputW)", JS)
        self.assertIn("energyStats(main, capacityWh, weighted)", JS)

    def test_header_alignment_and_tabs_reach_graph_end(self):
        self.assertIn("main > header .location-shell,\nmain > header #clock,\nmain > header .header-time{min-height:58px}", CSS)
        self.assertIn("main > nav.tabs{", CSS)
        self.assertIn("grid-template-columns:minmax(0,1fr) max-content", CSS)
        self.assertIn('main > nav.tabs > button[data-tab="tomorrow"]{justify-self:end;margin:0}', CSS)
        self.assertIn("main > nav.tabs{width:100%;padding-right:0}", CSS)

    def test_power_and_autonomy_are_shared_at_system_level(self):
        self.assertIn("function energyStats(d, capWh, pct)", JS)
        self.assertIn("Math.round(capacityWh * chargePct / 100 * 0.85 / outputW", JS)
        self.assertIn("Автономність", JS)
        self.assertNotIn("Автономність: —", JS)
        self.assertNotIn("Вхід / вихід контролює основна станція", JS)
        self.assertIn("disabled", JS)


    def test_compact_location_and_space_mapping(self):
        self.assertIn('id="eco-selected-location"', HTML)
        self.assertIn('id="eco-space-name"', HTML)
        self.assertIn("name: 'Дім', space: 'Квартира'", JS)
        self.assertIn("$('eco-space-name').textContent = place.space;", JS)
        self.assertIn("eco-context-arrow", HTML)
        self.assertEqual(HTML.count('class="eco-status"'), 1)
        self.assertIn(".eco-context-space strong{color:#a5e4db}", CSS)

    def test_admin_stays_accessible_while_scrolling(self):
        self.assertIn("function syncFloatingAdmin()", JS)
        self.assertIn("window.addEventListener('scroll', syncFloatingAdmin", JS)
        self.assertIn("adminHost.classList.toggle('is-floating'", JS)
        self.assertIn("main > header .header-time.is-floating", CSS)
        self.assertIn("position:fixed", CSS)
        self.assertIn("z-index:150", CSS)



if __name__ == "__main__":
    unittest.main()
