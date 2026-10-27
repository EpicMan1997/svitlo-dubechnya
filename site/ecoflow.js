/* EcoFlow static data model until cloud telemetry is connected; no remote commands. */
(function () {
  'use strict';

  // Placeholder percentages and watt values until real telemetry is connected.
  // capacityWh contains nominal manufacturer capacity, never inverter output.
  const inventory = Object.freeze({
    dacha: {
      name: 'Дача', space: 'Дача',
      devices: [
        { name: 'DELTA Pro 3', capacityWh: 4096, pct: 84, inputW: 0, outputW: 620, type: 'station', id: 'dp3' },
        { name: 'Додаткова батарея DELTA Pro 3', capacityWh: 4096, pct: 82, type: 'battery', parent: 'DELTA Pro 3', parentId: 'dp3', id: 'dp3eb' },
        { name: 'DELTA 3 Plus', capacityWh: 1024, pct: 92, inputW: 120, outputW: 38, type: 'station', id: 'd3p' },
        { name: 'DELTA 2', capacityWh: 1024, pct: 64, inputW: 0, outputW: 75, type: 'station', id: 'd2' },
        { name: 'RIVER 3 Plus Wireless', capacityWh: 286, pct: 29, inputW: 0, outputW: 12, type: 'station', id: 'r3pw' }
      ]
    },
    home: {
      name: 'Дім', space: 'Квартира',
      devices: [
        // PowerOcean: 6 kW inverter, currently one 5 kWh battery; system delivers 3 kW now, 6 kW with two batteries.
        { name: 'PowerOcean', capacityWh: 5000, inverterKw: 6, systemPowerKw: 3, twoBatterySystemKw: 6, batteryCount: 1, pct: 67, inputW: 300, outputW: 760, type: 'system', id: 'po' }
      ]
    },
    solovky: {
      name: 'Соловки', space: 'Соловки',
      devices: [
        { name: 'DELTA 2', capacityWh: 1024, pct: 54, inputW: 0, outputW: 125, type: 'station', id: 'd2' },
        { name: 'Додаткова батарея DELTA 2', capacityWh: 1024, pct: 49, type: 'battery', parent: 'DELTA 2', parentId: 'd2', id: 'd2eb' },
        { name: 'RIVER 2', capacityWh: 256, pct: 18, inputW: 0, outputW: 26, type: 'station', id: 'r2' }
      ]
    },
    naumenky: {
      name: 'Науменки', space: 'Науменки',
      devices: [
        { name: 'DELTA 2', capacityWh: 1024, pct: 71, inputW: 0, outputW: 93, type: 'station', id: 'd2' }
      ]
    }
  });

  const root = document.getElementById('ecoflow');
  const toggle = document.getElementById('ecoAdminToggle');
  if (!root || !toggle) return;

  const $ = id => document.getElementById(id);
  const uk = new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 1 });
  function niceWh(wh) {
    return wh >= 1000 ? uk.format(wh / 1000) + ' кВт·год' : uk.format(wh) + ' Вт·год';
  }
  function capClass(wh) {
    if (wh === null) return 'size-unknown';
    if (wh >= 3500) return 'size-large';
    if (wh >= 800) return 'size-medium';
    return 'size-small';
  }
  function level(pct) {
    if (pct >= 80) return 'high';
    if (pct >= 55) return 'good';
    if (pct >= 35) return 'medium';
    if (pct >= 20) return 'low';
    return 'critical';
  }

  function formatAutonomy(capacityWh, chargePct, outputW) {
    if (!Number.isFinite(outputW) || outputW <= 0) return '—';
    // Approximation using an 85% available energy factor.
    const estimatedMinutes = Math.round(capacityWh * chargePct / 100 * 0.85 / outputW * 60 / 5) * 5;
    const hours = Math.floor(estimatedMinutes / 60);
    const mins = estimatedMinutes % 60;
    return (hours ? hours + ' год' : '') + (mins ? (hours ? ' ' : '') + mins + ' хв' : '');
  }

  function chargeTrack(pct, name) {
    return '<div class="eco-charge-track" role="progressbar" aria-label="Заряд ' + name +
      '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '">' +
      '<i style="width:' + pct + '%"></i></div>';
  }

  function energyStats(d, capWh, pct) {
    const output = Number.isFinite(d.outputW) ? d.outputW : 0;
    const autonomy = formatAutonomy(capWh, pct, output);
    return '<div class="eco-device-stats eco-common-stats">' +
      '<div class="eco-device-stat"><span>Вхід</span><strong>' + d.inputW + ' Вт</strong></div>' +
      '<div class="eco-device-stat"><span>Вихід</span><strong>' + output + ' Вт</strong></div>' +
      '<div class="eco-device-stat eco-autonomy"><span>Автономність</span><strong>' + autonomy + '</strong></div>' +
      '</div>';
  }

  const individualLimitPresets = [100, 80, 50, 5];
  // UI-only drafts: a separate selection per physical station and location.
  const individualChargeLimits = new Map();

  function adminControls(device) {
    const key = activeEcoLocation + ':' + device.id;
    const selected = individualChargeLimits.get(key) ?? 80;
    const controls = individualLimitPresets.map(percent =>
      '<button type="button" class="eco-limit-preset' + (selected === percent ? ' is-active' : '') +
      '" data-eco-individual-limit="' + percent + '" data-eco-device="' + key +
      '" aria-pressed="' + String(selected === percent) + '">' + percent + '%</button>'
    ).join('');
    return '<div class="eco-admin-only eco-device-admin"><strong>Керування</strong>' +
      '<div class="eco-admin-controls"><div class="eco-individual-limit">' +
      '<span class="eco-individual-label">Ліміт заряджання</span>' +
      '<div class="eco-limit-presets" role="group" aria-label="Ліміт заряджання ' + device.name + '">' +
      controls + '</div></div>' +
      '<button type="button" disabled>AC-вихід</button></div>' +
      '</div>';
  }

  function deviceView(d) {
    const size = capClass(d.capacityWh);
    const charge = level(d.pct);
    const capacity = niceWh(d.capacityWh);
    const titleNote = d.type === 'system'
      ? 'Інвертор ' + d.inverterKw + ' кВт · система ' + d.systemPowerKw +
        ' кВт (із другою батареєю ' + d.twoBatterySystemKw + ' кВт)'
      : 'Зарядна станція';
    return '<article class="eco-device eco-standalone ' + size + ' charge-' + charge +
      '" aria-label="' + d.name + ', заряд ' + d.pct + '%">' +
      '<div class="eco-device-head"><div class="eco-device-ident">' +
      '<strong class="eco-device-name">' + d.name + '</strong>' +
      '<span class="eco-device-model">' + titleNote + '</span></div></div>' +
      '<div class="eco-battery"><span class="eco-battery-percent">' + d.pct +
      '%</span><span class="eco-battery-art" aria-hidden="true"><i style="width:' +
      d.pct + '%"></i></span></div>' +
      chargeTrack(d.pct, d.name) +
      '<div class="eco-capacity-line"><strong>' + capacity + '</strong></div>' +
      energyStats(d, d.capacityWh, d.pct) +
      adminControls(d) +
      '</article>';
  }

  function systemView(main, addon) {
    const capacityWh = main.capacityWh + addon.capacityWh;
    const weighted = Math.round((main.capacityWh * main.pct + addon.capacityWh * addon.pct) / capacityWh);
    const batteryPart = (d, role) => {
      const name = role === 'Основна' ? 'основної станції' : 'додаткової батареї';
      return '<div class="eco-system-part charge-' + level(d.pct) + '">' +
        '<div class="eco-system-part-top"><span class="eco-system-part-label">' + role + '</span>' +
        '<strong class="eco-system-percent">' + d.pct + '%</strong></div>' +
        chargeTrack(d.pct, name) +
        '<span class="eco-system-part-cap">' + niceWh(d.capacityWh) + '</span>' +
        '</div>';
    };
    return '<article class="eco-system eco-system-paired charge-' + level(weighted) +
      '" aria-label="' + main.name + ' із додатковою батареєю, загалом ' + niceWh(capacityWh) + '">' +
      '<div class="eco-system-head"><div class="eco-system-title"><strong>' + main.name +
      '</strong><span class="eco-system-tag">+ додаткова батарея</span></div>' +
      '<div class="eco-system-total"><strong>' + niceWh(capacityWh) + '</strong>' +
      '<span>' + weighted + '% загалом</span></div></div>' +
      '<div class="eco-system-parts">' + batteryPart(main, 'Основна') + batteryPart(addon, 'Додаткова') + '</div>' +
      energyStats(main, capacityWh, weighted) +
      adminControls(main) +
      '</article>';
  }

  // Each primary station and its expansion battery form ONE visual system.
  function renderDeviceGrid(devices) {
    const addons = new Map(devices.filter(d => d.type === 'battery' && d.parentId).map(d => [d.parentId, d]));
    const ids = new Set(devices.map(d => d.id));
    return devices.map(d => {
      if (d.type === 'battery' && d.parentId && ids.has(d.parentId)) return '';
      const addon = addons.get(d.id);
      return addon ? systemView(d, addon) : deviceView(d);
    }).join('');
  }

  // Drafts are session-local UI state. No device commands or authentication exist yet.
  const adminDraft = {
    scope: 'current',
    chargeLimit: 90,
    selected: { limit: new Set(), ac: new Set(), speed: new Set() },
    speeds: new Map(),
    speedPreset: 'balanced'
  };
  let activeEcoLocation = 'dacha';

  function selectableStations() {
    const locIds = adminDraft.scope === 'all'
      ? Object.keys(inventory) : [activeEcoLocation];
    // Expansion batteries belong to the primary; PowerOcean requires separate verified commands.
    return locIds.flatMap(loc => inventory[loc].devices
      .filter(d => d.type === 'station')
      .map(d => ({ key: loc + ':' + d.id, name: d.name, id: d.id, loc, place: inventory[loc].name })));
  }

  // Per-model AC input power targets in W. Values are illustrative until device API capabilities are verified.
  // DELTA 2 200/500/1200 W follows EcoFlow's documented quiet/optimized/max settings.
  const chargingProfiles = {
    dp3: { quiet: 500, balanced: 1000, fast: 2900 },
    d3p: { quiet: 200, balanced: 500, fast: 1500 },
    d2: { quiet: 200, balanced: 500, fast: 1200 },
    r3pw: { quiet: 80, balanced: 200, fast: 380 },
    r2: { quiet: 100, balanced: 200, fast: 360 }
  };
  const speedModes = [
    { key: 'quiet', label: 'Тиха' },
    { key: 'balanced', label: 'Оптимальна' },
    { key: 'fast', label: 'Швидка' }
  ];
  function speedOptions(station) {
    const profile = chargingProfiles[station.id];
    const selected = adminDraft.speeds.get(station.key) || adminDraft.speedPreset;
    return '<select class="eco-speed-select" data-eco-speed="' + station.key +
      '" aria-label="Режим заряджання ' + station.name + '">' +
      speedModes.map(mode => '<option value="' + mode.key + '"' +
        (selected === mode.key ? ' selected' : '') + '>' + mode.label +
        ' · ' + (station.id === 'r3pw' && mode.key === 'quiet' ? 'до 80 Вт' : profile[mode.key] + ' Вт') + '</option>').join('') + '</select';
  }

  function targetRows(group, withSpeed) {
    const stations = selectableStations();
    const set = adminDraft.selected[group];
    const rows = stations.map(station => {
      const checked = set.has(station.key);
      const speedSelect = withSpeed ? speedOptions(station) : '';
      return '<div class="eco-target-row"><label class="eco-target-label">' +
        '<input type="checkbox" data-eco-group="' + group + '" data-eco-target="' +
        station.key + '"' + (checked ? ' checked' : '') + '>' +
        '<span>' + station.name + (adminDraft.scope === 'all' ?
          '<small>' + station.place + '</small>' : '') + '</span></label>' +
        speedSelect + '</div>';
    }).join('');
    return '<div class="eco-target-top"><span>Станції: ' +
      set.size + ' / ' + stations.length + '</span><span class="eco-target-actions">' +
      '<button type="button" data-eco-select="all" data-eco-group="' + group + '">Усі</button>' +
      '<button type="button" data-eco-select="none" data-eco-group="' + group + '">Жодної</button>' +
      '</span></div><div class="eco-target-list">' +
      (rows || '<p class="eco-target-empty">Немає сумісних переносних станцій у цій локації.</p>') +
      '</div>';
  }

  function renderBulkPanel() {
    const container = $('eco-bulk-content');
    if (!container) return;
    const selected = adminDraft.scope === 'all' ? 'Усі локації' : inventory[activeEcoLocation].name;
    const scopePicker = '<label class="eco-bulk-scope">Локації <select id="eco-admin-scope">' +
      '<option value="current"' + (adminDraft.scope === 'current' ? ' selected' : '') + '>Поточна: ' +
        inventory[activeEcoLocation].name + '</option>' +
      '<option value="all"' + (adminDraft.scope === 'all' ? ' selected' : '') + '>Усі локації</option></select></label>';
    container.innerHTML =
      '<div class="eco-bulk-toolbar">' + scopePicker +
      '<span class="eco-bulk-scope-note">' + selected + '</span></div>' +
      '<div class="eco-bulk-actions">' +
      '<section class="eco-bulk-card"><h4>Ліміт заряджання</h4>' +
      '<div class="eco-bulk-range"><input type="range" id="eco-bulk-limit" min="50" max="100" step="5" value="' +
        adminDraft.chargeLimit + '" aria-label="Спільний ліміт заряджання">' +
      '<output id="eco-bulk-limit-value" for="eco-bulk-limit">' + adminDraft.chargeLimit + '%</output></div>' +
      targetRows('limit', false) +
      '<button class="eco-bulk-apply" type="button" disabled>Застосувати ліміт</button></section>' +
      '<section class="eco-bulk-card"><h4>AC-виходи</h4>' +
      targetRows('ac', false) +
      '<div class="eco-bulk-buttons"><button class="eco-bulk-apply" type="button" disabled>Увімкнути AC</button>' +
      '<button class="eco-bulk-apply eco-bulk-danger" type="button" disabled>Вимкнути AC</button></div>' +
      '</section>' +
      '<section class="eco-bulk-card"><h4>Швидкість заряджання</h4>' +
      '<div class="eco-speed-preset" role="group" aria-label="Режим заряджання для вибраних станцій">' +
      speedModes.map(mode => '<button type="button" data-eco-preset="' + mode.key +
        '" class="eco-speed-preset-button' + (adminDraft.speedPreset === mode.key ? ' active' : '') + '">' +
        mode.label + '</button>').join('') + '</div>' +
      '<p class="eco-bulk-subtitle">Потужність у ватах залежить від моделі. Можна змінити режим кожної станції окремо.</p>' +
      targetRows('speed', true) +
      '<button class="eco-bulk-apply" type="button" disabled>Застосувати швидкості</button></section></div>';
  }

  const bulkContent = $('eco-bulk-content');
  if (bulkContent) {
    bulkContent.addEventListener('click', event => {
      const presetButton = event.target.closest('button[data-eco-preset]');
      if (presetButton) {
        const mode = presetButton.dataset.ecoPreset;
        if (!speedModes.some(item => item.key === mode)) return;
        adminDraft.speedPreset = mode;
        const available = new Set(selectableStations().map(st => st.key));
        adminDraft.selected.speed.forEach(key => {
          if (available.has(key)) adminDraft.speeds.set(key, mode);
        });
        renderBulkPanel();
        return;
      }
      const button = event.target.closest('button[data-eco-select]');
      if (!button) return;
      const group = button.dataset.ecoGroup;
      if (!Object.prototype.hasOwnProperty.call(adminDraft.selected, group)) return;
      adminDraft.selected[group] = button.dataset.ecoSelect === 'all'
        ? new Set(selectableStations().map(x => x.key))
        : new Set();
      renderBulkPanel();
    });
    bulkContent.addEventListener('input', event => {
      const target = event.target;
      if (target.id === 'eco-bulk-limit') {
        $('eco-bulk-limit-value').textContent = target.value + '%';
      }
    });
    bulkContent.addEventListener('change', event => {
      const target = event.target;
      if (target.id === 'eco-admin-scope') {
        adminDraft.scope = target.value === 'all' ? 'all' : 'current';
        Object.keys(adminDraft.selected).forEach(group => adminDraft.selected[group].clear());
      } else if (target.id === 'eco-bulk-limit') {
        adminDraft.chargeLimit = Math.max(50, Math.min(100, Number(target.value) || 90));
      } else if (target.dataset.ecoTarget) {
        const group = target.dataset.ecoGroup;
        const key = target.dataset.ecoTarget;
        if (!adminDraft.selected[group] || !selectableStations().some(st => st.key === key)) return;
        if (target.checked) adminDraft.selected[group].add(key);
        else adminDraft.selected[group].delete(key);
      } else if (target.dataset.ecoSpeed) {
        const key = target.dataset.ecoSpeed;
        if (!selectableStations().some(st => st.key === key)) return;
        const value = speedModes.some(item => item.key === target.value) ? target.value : 'balanced';
        adminDraft.speeds.set(key, value);
        adminDraft.selected.speed.add(key);
      } else return;
      renderBulkPanel();
    });
  }

  function updateLocation(id) {
    if (!Object.prototype.hasOwnProperty.call(inventory, id)) return;
    const place = inventory[id];
    const totalWh = place.devices.reduce((v, d) => v + (d.capacityWh || 0), 0);
    const allKnown = place.devices.every(d => d.capacityWh !== null);
    const weighted = allKnown && totalWh
      ? Math.round(place.devices.reduce((v, d) => v + d.capacityWh * d.pct, 0) / totalWh)
      : null;
    if (adminDraft.scope === 'current' && activeEcoLocation !== id) {
      Object.keys(adminDraft.selected).forEach(group => adminDraft.selected[group].clear());
    }
    activeEcoLocation = id;
    root.dataset.location = id;
    $('eco-selected-location').textContent = place.name;
    $('eco-space-name').textContent = place.space;
    $('eco-count').textContent = String(place.devices.length);
    $('eco-capacity').textContent = allKnown ? niceWh(totalWh) : 'Уточнюється';
    $('eco-capacity-note').textContent = allKnown ? 'Сума номінальних ємностей батарей' : 'Ємність системи ще не уточнена';
    $('eco-demo-total').textContent = weighted === null ? '—' : weighted + '%';
    $('eco-demo-total').dataset.level = weighted === null ? 'unknown' : level(weighted);
    $('eco-demo-note').textContent = weighted === null ? 'Ємність батарей ще невідома' : 'Зважений за ємністю';
    // Here the segment width, unlike a card's layout size, is mathematically proportional to Wh.
    const batteries = new Map(place.devices.filter(d => d.type === 'battery' && d.parentId).map(d => [d.parentId, d]));
    const mainIds = new Set(place.devices.map(d => d.id));
    const systems = place.devices.flatMap(d => {
      if (d.type === 'battery' && d.parentId && mainIds.has(d.parentId)) return [];
      const linked = batteries.get(d.id);
      if (!linked) return [{ name: d.name, wh: d.capacityWh, pct: d.pct }];
      const wh = d.capacityWh + linked.capacityWh;
      const pct = Math.round((d.capacityWh * d.pct + linked.capacityWh * linked.pct) / wh);
      return [{ name: d.name + ' + додаткова батарея', wh, pct }];
    });
    $('eco-capacity-strip').innerHTML = allKnown
      ? systems.map(system =>
          '<span class="eco-cap-segment charge-' + level(system.pct) + '" style="flex-grow:' + system.wh +
          '" tabindex="0" role="img" aria-label="' + system.name + ', заряд ' + system.pct + ' відсотків"' +
          ' data-eco-tooltip="' + system.name + ' · ' + system.pct + '% · ' + niceWh(system.wh) + '">' +
          '<i style="width:' + system.pct + '%"></i></span>'
        ).join('')
      : '<span class="eco-cap-unknown">Ємність цієї батареї ще не уточнена</span>';
    hideCapacityTooltip();
    $('eco-devices').innerHTML = renderDeviceGrid(place.devices);
    renderBulkPanel();
  }

  // Individual limit presets affect only the displayed draft, never the EcoFlow devices.
  root.addEventListener('click', event => {
    const button = event.target.closest('button[data-eco-individual-limit]');
    if (!button || !root.contains(button)) return;
    const value = Number(button.dataset.ecoIndividualLimit);
    const key = button.dataset.ecoDevice;
    if (!individualLimitPresets.includes(value)) return;
    if (!key.startsWith(activeEcoLocation + ':')) return;
    const allowed = inventory[activeEcoLocation].devices.some(d =>
      d.type !== 'battery' && (activeEcoLocation + ':' + d.id) === key);
    if (!allowed) return;
    individualChargeLimits.set(key, value);
    const group = button.closest('.eco-limit-presets');
    if (!group) return;
    group.querySelectorAll('button[data-eco-individual-limit]').forEach(option => {
      const active = Number(option.dataset.ecoIndividualLimit) === value;
      option.classList.toggle('is-active', active);
      option.setAttribute('aria-pressed', String(active));
    });
  });

  // Read-only capacity detail: hover, keyboard focus or touch/click.
  const capacityStrip = $('eco-capacity-strip');
  const capacityTooltip = $('eco-capacity-tooltip');
  function hideCapacityTooltip() {
    if (capacityTooltip) capacityTooltip.hidden = true;
  }
  function showCapacityTooltip(segment) {
    if (!segment || !capacityTooltip || !segment.dataset.ecoTooltip) return;
    capacityTooltip.textContent = segment.dataset.ecoTooltip;
    capacityTooltip.hidden = false;
    const position = segment.getBoundingClientRect();
    const tooltipSize = capacityTooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const middle = position.left + position.width / 2 - tooltipSize.width / 2;
    capacityTooltip.style.left = Math.max(8, Math.min(middle, viewportWidth - tooltipSize.width - 8)) + 'px';
    const above = position.top - tooltipSize.height - 9;
    capacityTooltip.style.top = (above >= 8 ? above : position.bottom + 9) + 'px';
  }
  if (capacityStrip && capacityTooltip) {
    capacityStrip.addEventListener('pointerover', event => {
      const segment = event.target.closest('.eco-cap-segment');
      if (segment) showCapacityTooltip(segment);
    });
    capacityStrip.addEventListener('pointerout', event => {
      const next = event.relatedTarget?.closest?.('.eco-cap-segment');
      if (!next) hideCapacityTooltip();
    });
    capacityStrip.addEventListener('focusin', event => {
      const segment = event.target.closest('.eco-cap-segment');
      if (segment) showCapacityTooltip(segment);
    });
    capacityStrip.addEventListener('focusout', event => {
      if (!event.relatedTarget?.closest?.('.eco-cap-segment')) hideCapacityTooltip();
    });
    capacityStrip.addEventListener('click', event => {
      const segment = event.target.closest('.eco-cap-segment');
      if (segment) showCapacityTooltip(segment);
    });
    document.addEventListener('pointerdown', event => {
      if (!event.target.closest('.eco-capacity-strip')) hideCapacityTooltip();
    });
    window.addEventListener('scroll', hideCapacityTooltip, { passive: true });
    window.addEventListener('resize', hideCapacityTooltip);
  }

  // Admin controls stay disabled pending authenticated server access.
  function setAdminMode(enabled) {
    root.classList.toggle('is-admin-mode', enabled);
    document.body.classList.toggle('eco-admin-visible', enabled);
    toggle.setAttribute('aria-checked', String(enabled));
    toggle.title = enabled ? 'Вимкнути Admin' : 'Увімкнути Admin';
    $('eco-admin-bulk').hidden = !enabled;
  }
  toggle.addEventListener('click', function () {
    setAdminMode(toggle.getAttribute('aria-checked') !== 'true');
  });
  setAdminMode(false);

  // Keep Admin reachable after the header scrolls out of view.
  const adminHost = toggle.closest('.header-time');
  const siteHeader = document.querySelector('main > header');
  function syncFloatingAdmin() {
    if (!adminHost || !siteHeader) return;
    const threshold = siteHeader.offsetTop + siteHeader.offsetHeight + 12;
    adminHost.classList.toggle('is-floating', window.scrollY > threshold);
  }
  window.addEventListener('scroll', syncFloatingAdmin, { passive: true });
  window.addEventListener('resize', syncFloatingAdmin);
  syncFloatingAdmin();

  const selectedButton = document.querySelector('[data-location].selected');
  const restored = selectedButton?.dataset.location || 'dacha';
  updateLocation(restored);
  window.addEventListener('svitlo:location-change', e => updateLocation(e.detail?.id));
})();
