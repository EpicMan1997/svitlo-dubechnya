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
        self.assertNotIn('id="eco-admin-mode-hint"', HTML)
        self.assertNotIn("eco-admin-mode-hint", JS)
        self.assertIn(".eco-shell.is-admin-mode", CSS)

    def test_capacity_is_proportional_and_powerocean_is_known(self):
        self.assertIn("flex-grow:' + system.wh", JS)
        self.assertIn("capacityWh: 5000, inverterKw: 6, systemPowerKw: 3, twoBatterySystemKw: 6, batteryCount: 1", JS)
        self.assertIn("function powerOceanView(d)", JS)
        self.assertIn("powerOceanAdmin(d)", JS)
        self.assertIn('id="eco-capacity-strip"', HTML)

    def test_location_changer_and_pwa_integration(self):
        self.assertIn("svitlo:location-change", JS)
        self.assertIn("new CustomEvent('svitlo:location-change'", HTML)
        self.assertNotIn('href="#ecoflow"', HTML)
        self.assertIn('<section class="eco-shell"', HTML)
        self.assertIn('"./ecoflow.css?v=21"', SW)
        self.assertIn('"./ecoflow.js?v=21"', SW)


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
        self.assertIn("return addon ? systemView(d, addon) : d.type === 'system' ? powerOceanView(d) : deviceView(d);", JS)
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



    def test_dacha_delta_three_plus_before_delta_two(self):
        dacha = JS.split("dacha: {", 1)[1].split("home: {", 1)[0]
        self.assertLess(dacha.index("name: 'DELTA 3 Plus'"), dacha.index("name: 'DELTA 2'"))

    def test_full_width_chart_with_inline_change_history(self):
        self.assertIn('class="card schedule-card"', HTML)
        self.assertIn('class="history history-inline"', HTML)
        self.assertIn('id="scheduleDetailsHost"', HTML)
        self.assertLess(HTML.index('id="display"'), HTML.index('class="history history-inline"'))
        self.assertLess(HTML.index('class="history history-inline"'), HTML.index('id="scheduleDetailsHost"'))
        self.assertIn("const detailsAt=html.indexOf", HTML)
        self.assertIn("$('scheduleDetailsHost').innerHTML=html.slice(detailsAt)", HTML)
        self.assertIn("document.querySelector('#scheduleDetailsHost .schedule-details')", HTML)
        self.assertIn("main > .layout{display:block;grid-template-columns:none", CSS)
        self.assertIn(".history-inline .change-comparison", CSS)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", CSS)

    def test_speed_presets_show_per_model_watts_and_allow_overrides(self):
        self.assertIn("const chargingProfiles = {", JS)
        self.assertIn("d2: { quiet: 200, balanced: 500, fast: 1200 }", JS)
        self.assertIn("d3p: { quiet: 200, balanced: 500, fast: 1500 }", JS)
        self.assertIn("dp3: { quiet: 500, balanced: 1000, fast: 2900 }", JS)
        self.assertIn("Тиха", JS)
        self.assertIn("Оптимальна", JS)
        self.assertIn("Швидка", JS)
        self.assertIn("data-eco-preset", JS)
        self.assertIn("data-eco-speed", JS)
        self.assertIn("adminDraft.speeds.set(key, value)", JS)
        self.assertNotIn("['25', '50', '75', '100']", JS)
        self.assertIn(".eco-speed-preset{", CSS)

    def test_capacity_strip_groups_extra_battery_with_parent(self):
        self.assertIn("const batteries = new Map(", JS)
        self.assertIn("const systems = place.devices.flatMap(", JS)
        self.assertIn("linked.capacityWh", JS)
        self.assertIn("linked.pct", JS)
        self.assertIn("flex-grow:' + system.wh", JS)

    def test_admin_shared_actions_and_independent_targets(self):
        self.assertIn('id="eco-admin-bulk"', HTML)
        self.assertIn('id="eco-bulk-content"', HTML)
        self.assertIn("'eco-admin-bulk').hidden = !enabled", JS)
        for group in ("reserve", "ac", "speed"):
            self.assertIn("targetRows('" + group + "'", JS)
        for action in ("Застосувати резерв", "Увімкнути AC", "Вимкнути AC", "Застосувати швидкості"):
            self.assertIn(action, JS)
        self.assertIn("data-eco-target", JS)
        self.assertIn("data-eco-speed", JS)
        self.assertIn("data-eco-select", JS)
        self.assertIn("value=\"all\"", JS)
        self.assertIn("function renderBulkPanel()", JS)
        self.assertIn("new Set()", JS)
        self.assertIn("Object.keys(adminDraft.selected).forEach(group => adminDraft.selected[group].clear())", JS)
        self.assertIn(".eco-bulk-actions{display:grid", CSS)

    def test_no_unsecured_admin_commands_and_powerocean_is_separate(self):
        self.assertIn("PowerOcean requires separate verified commands", JS)
        self.assertIn(".filter(d => d.type === 'station')", JS)
        self.assertNotRegex(JS, r"\bfetch\s*\(|XMLHttpRequest|WebSocket")
        self.assertIn("type=\"button\" disabled>Увімкнути AC", JS)
        self.assertIn("type=\"button\" disabled>Вимкнути AC", JS)
        self.assertIn("type=\"button\" disabled>Застосувати швидкості", JS)
        self.assertNotIn("Доступ після захищеного підключення.", JS)



    def test_previous_changes_counter_and_yesterday_label(self):
        self.assertIn('Минулі зміни сьогодні <span class="past-change-count">', HTML)
        self.assertIn("previousEdits.length", HTML)
        self.assertNotIn("<summary>Ще '+previousEdits.length", HTML)
        self.assertIn("$('previousTitle').textContent='Зміни і графік вчора'", HTML)
        self.assertNotIn("$('previousTitle').textContent='Зміни і графік '+yDate", HTML)
        self.assertIn(".past-change-count{", CSS)

    def test_tomorrow_aligned_to_full_width_chart(self):
        self.assertIn("main > nav.tabs{width:100%;padding-left:0;padding-right:20px}", CSS)
        self.assertIn("@media(max-width:650px){main > nav.tabs{padding-right:14px}}", CSS)
        self.assertIn('main > nav.tabs > button[data-tab="tomorrow"]{justify-self:end;margin:0}', CSS)

    def test_capacity_details_centered_without_floating(self):
        self.assertIn('id="eco-capacity-tooltip"', HTML)
        self.assertIn('role="status" aria-live="polite"', HTML)
        self.assertIn('data-active="false"', HTML)
        self.assertIn('data-eco-tooltip=', JS)
        self.assertIn("system.name + ' · ' + system.pct", JS)
        self.assertIn("const pct = Math.round((d.capacityWh * d.pct + linked.capacityWh * linked.pct) / wh)", JS)
        for event_name in ("pointerover", "pointerout", "focusin", "focusout", "click"):
            self.assertIn("capacityStrip.addEventListener('" + event_name + "'", JS)
        self.assertIn("capacityTooltip.dataset.active = 'true'", JS)
        self.assertIn("capacityTooltip.dataset.active = 'false'", JS)
        self.assertIn("height:46px", CSS)
        self.assertIn("position:static", CSS)
        self.assertNotIn("const middle = position.left", JS)

    def test_charge_arrows_and_resized_three_station_row(self):
        self.assertIn("charging: { label: 'Заряджається', sign: '↑' }", JS)
        self.assertIn("discharging: { label: 'Розряджається', sign: '↓' }", JS)
        self.assertIn('@media(min-width:951px)', CSS)
        self.assertIn('.eco-shell[data-location="dacha"] .eco-devices', CSS)
        self.assertIn("grid-template-columns:repeat(24,minmax(0,1fr))", CSS)
        self.assertIn(".eco-device.size-medium", CSS)
        self.assertIn("grid-column:span 9", CSS)
        self.assertIn(".eco-device.size-small", CSS)
        self.assertIn("grid-column:span 6", CSS)

    def test_every_battery_has_explicit_operation_state(self):
        self.assertEqual(JS.count("operation: 'discharging'"), 8)
        self.assertEqual(JS.count("operation: 'charging'"), 1)
        self.assertEqual(JS.count("operation: 'holding'"), 1)
        self.assertIn("charging: { label: 'Заряджається'", JS)
        self.assertIn("discharging: { label: 'Розряджається'", JS)
        self.assertIn("holding: { label: 'Підтримує заряд'", JS)
        self.assertIn("unknown: { label: 'Статус невідомий'", JS)
        self.assertIn("function operationBadge(device)", JS)
        self.assertIn("operationBadge(d)", JS)
        for classname in ("charging", "discharging", "holding", "unknown"):
            self.assertIn(".eco-operation-" + classname, CSS)
        self.assertIn(".eco-system-part .eco-operation", CSS)

    def test_reserve_presets_replaced_charge_limit(self):
        self.assertIn("const reservePresets = [0, 5, 20, 50, 80, 100]", JS)
        self.assertIn("const individualReserves = new Map()", JS)
        self.assertIn("function adminControls(device)", JS)
        self.assertIn("adminControls(d)", JS)
        self.assertIn("adminControls(main)", JS)
        self.assertIn("data-eco-reserve", JS)
        self.assertIn("individualReserves.set(key, value)", JS)
        self.assertNotIn("Ліміт заряджання", JS)
        self.assertIn("Резерв заряду", JS)
        self.assertIn(".eco-reserve-presets", CSS)
        self.assertIn(".eco-reserve-option.is-active", CSS)

    def test_powerocean_wide_with_separate_energy_flow_and_controls(self):
        self.assertIn("function powerOceanView(d)", JS)
        self.assertIn('class="eco-powerocean charge-', JS)
        self.assertIn("eco-ocean-body", JS)
        self.assertIn("eco-ocean-energy", JS)
        self.assertIn("powerOceanAdmin(d)", JS)
        self.assertIn("powerOceanDraft = { reserve: 0, selfPowered: true, allDay: true", JS)
        self.assertIn("chargeW: 3000", JS)
        self.assertIn("data-eco-ocean-watts", JS)
        self.assertIn('min="100" max="3000" step="100"', JS)
        self.assertIn("data-eco-ocean-allday", JS)
        self.assertIn("data-eco-ocean-self-powered", JS)
        self.assertIn("data-eco-ocean-time", JS)
        self.assertIn(".eco-powerocean{", CSS)
        self.assertIn('grid-column:1/-1!important', CSS)
        self.assertIn(".eco-ocean-controls{", CSS)
        self.assertNotIn("Інвертор ' + d.inverterKw", JS)

    def test_river_three_plus_quiet_is_eighty_watts(self):
        self.assertIn("r3pw: { quiet: 80, balanced: 200, fast: 380 }", JS)
        self.assertIn("mode.key === 'quiet' ? 'до 80 Вт'", JS)
        self.assertIn("'</select>'", JS)


    def test_matching_archive_arrows_and_prominent_daily_counter(self):
        self.assertIn('class="past-change-label"', HTML)
        self.assertIn("Минулі зміни сьогодні", HTML)
        self.assertIn('class="archive-arrow" aria-hidden="true"', HTML)
        self.assertEqual(HTML.count('class="archive-arrow"'), 2)
        self.assertIn('class="yesterday-summary-label"', HTML)
        self.assertIn(".history-inline .archive-arrow::before", CSS)
        self.assertIn(".history-inline details[open]>summary>.archive-arrow::before", CSS)
        self.assertIn(".past-change-count{", CSS)
        self.assertIn("border:2px solid #fb7185", CSS)
        self.assertIn(".history-inline .earlier-changes>summary::after{content:none!important}", CSS)

    def test_tomorrow_flush_with_schedule_card_edge(self):
        self.assertIn("main > nav.tabs{", CSS)
        self.assertIn("box-sizing:border-box", CSS)
        self.assertIn("margin-inline:0", CSS)
        self.assertIn("padding:0", CSS)
        self.assertIn('main > nav.tabs > button[data-tab="tomorrow"]{justify-self:end;margin-right:0;margin-left:0}', CSS)
        self.assertIn("main > nav.tabs{padding:0}", CSS)


    def test_ecoflow_branding_and_fresh_pwa_assets(self):
        self.assertIn('eco-title-monogram', HTML)
        self.assertIn('stroke="#67E8F9"', HTML)
        self.assertIn('href="./ecoflow.css?v=21"', HTML)
        self.assertIn('src="./ecoflow.js?v=21"', HTML)
        self.assertIn("updateViaCache:'none'", HTML)
        self.assertIn('nashe-svitlo-static-v21', SW)
        self.assertIn('url.pathname.endsWith("/ecoflow.css")', SW)
        self.assertIn('url.pathname.endsWith("/ecoflow.js")', SW)
        self.assertIn('fetch(request, {cache: "no-store"})', SW)
        self.assertIn('caches.match(request)', SW)
        self.assertIn(".eco-title-monogram{", CSS)



    def test_capacity_detail_is_only_short_name_and_percentage(self):
        self.assertIn("d.name + ' + батарея'", JS)
        self.assertIn("data-eco-tooltip=", JS)
        self.assertIn("system.name + ' · ' + system.pct", JS)
        self.assertNotIn("system.pct + '% · ' + niceWh(system.wh)", JS)

    def test_mobile_eco_cards_full_width_and_admin_switch_within_track(self):
        self.assertIn('.eco-shell[data-location="dacha"] .eco-devices > .eco-device,', CSS)
        self.assertIn("grid-template-columns:minmax(0,1fr)", CSS)
        self.assertIn("grid-column:1/-1!important", CSS)
        self.assertIn('main > header .eco-admin-toggle .eco-switch-track{', CSS)
        self.assertIn("overflow:hidden", CSS)
        self.assertIn("transform:translateX(18px)", CSS)
        self.assertIn("transform:translateX(16px)", CSS)
        self.assertIn("max-width:calc(100vw - 16px)", CSS)

    def test_long_outages_have_responsive_duration_labels(self):
        self.assertIn("function outageDurationText(minutes)", HTML)
        self.assertIn("function outageDurationCompact(minutes)", HTML)
        self.assertIn("length>120?", HTML)
        self.assertIn('class="outage-duration"', HTML)
        self.assertIn('duration-full', HTML)
        self.assertIn('duration-short', HTML)
        self.assertIn(".outage-duration .duration-short{display:none}", CSS)
        self.assertIn("@media(max-width:700px)", CSS)


    def test_zero_reserve_only_on_powerocean(self):
        self.assertIn("reservePresets.filter(percent => powerOcean || percent >= 5)", JS)
        self.assertIn("if (!device || (device.type !== 'system' && value < 5)) return;", JS)
        self.assertIn("powerOceanDraft = { reserve: 0", JS)
        self.assertIn("reserveOptions(device, key, powerOceanDraft.reserve, true)", JS)
        self.assertIn("    reserve: 5,", JS)
        self.assertIn('id="eco-bulk-reserve" min="5" max="100" step="5"', JS)
        self.assertIn("Math.max(5, Math.min(100", JS)

    def test_reserve_buttons_fit_small_river_card(self):
        self.assertIn(".eco-admin-controls .eco-reserve-presets > button.eco-reserve-option{", CSS)
        self.assertIn("min-width:0", CSS)
        self.assertIn("box-sizing:border-box", CSS)
        self.assertIn(".eco-device.size-small .eco-admin-controls{", CSS)
        self.assertIn("flex-direction:column", CSS)
        self.assertIn(".eco-device.size-small .eco-admin-controls > button[disabled]{", CSS)



if __name__ == "__main__":
    unittest.main()
