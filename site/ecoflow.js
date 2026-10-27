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
        { name: 'DELTA 2', capacityWh: 1024, pct: 64, inputW: 0, outputW: 75, type: 'station', id: 'd2' },
        { name: 'DELTA 3 Plus', capacityWh: 1024, pct: 92, inputW: 120, outputW: 38, type: 'station', id: 'd3p' },
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

  function adminControls() {
    return '<div class="eco-admin-only eco-device-admin"><strong>Керування</strong>' +
      '<div class="eco-admin-controls"><label>Ліміт заряджання' +
      '<input type="range" min="50" max="100" value="90" disabled></label>' +
      '<button type="button" disabled>AC-вихід</button></div>' +
      '<span>Доступ після захищеного підключення.</span></div>';
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
      adminControls() +
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
      adminControls() +
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

  function updateLocation(id) {
    if (!Object.prototype.hasOwnProperty.call(inventory, id)) return;
    const place = inventory[id];
    const totalWh = place.devices.reduce((v, d) => v + (d.capacityWh || 0), 0);
    const allKnown = place.devices.every(d => d.capacityWh !== null);
    const weighted = allKnown && totalWh
      ? Math.round(place.devices.reduce((v, d) => v + d.capacityWh * d.pct, 0) / totalWh)
      : null;
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
    $('eco-capacity-strip').innerHTML = allKnown
      ? place.devices.map(d =>
          '<span class="eco-cap-segment charge-' + level(d.pct) + '" style="flex-grow:' + d.capacityWh +
          '" title="' + d.name + ': ' + niceWh(d.capacityWh) + ', заряд ' + d.pct + '%">' +
          '<i style="width:' + d.pct + '%"></i></span>'
        ).join('')
      : '<span class="eco-cap-unknown">Ємність цієї батареї ще не уточнена</span>';
    $('eco-devices').innerHTML = renderDeviceGrid(place.devices);
  }

  // Admin controls stay disabled pending authenticated server access.
  function setAdminMode(enabled) {
    root.classList.toggle('is-admin-mode', enabled);
    document.body.classList.toggle('eco-admin-visible', enabled);
    toggle.setAttribute('aria-checked', String(enabled));
    toggle.title = enabled ? 'Вимкнути Admin' : 'Увімкнути Admin';
    $('eco-admin-mode-hint').hidden = !enabled;
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
