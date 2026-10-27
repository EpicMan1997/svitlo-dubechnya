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
  const MAX_BATTERY_WH = 5000; // Capacity scale: largest installed battery in the current inventory.
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
  function deviceView(d, linked = false) {
    const isBattery = d.type === 'battery';
    const size = capClass(d.capacityWh);
    const capacity = d.capacityWh === null ? 'Ємність акумуляторів невідома' : niceWh(d.capacityWh);
    const typeLabel = isBattery ? 'Додаткова батарея' : d.type === 'system' ? 'Домашня система' : 'Зарядна станція';
    const info = d.type === 'system'
      ? '1 батарея · ' + capacity + ' · інвертор ' + d.inverterKw + ' кВт · потужність системи зараз ' + d.systemPowerKw + ' кВт (із другою батареєю: ' + d.twoBatterySystemKw + ' кВт)'
      : isBattery ? 'Підключена до ' + d.parent : 'Номінальна ємність ' + capacity;
    const charge = level(d.pct);
    const stats = isBattery ?
      '<div class="eco-attached-note">Вхід / вихід контролює основна станція. Потужності окремо не показуємо.</div>' :
      '<div class="eco-device-stats">' +
        '<div class="eco-device-stat"><span>Вхід</span><strong>' + d.inputW + ' Вт</strong></div>' +
        '<div class="eco-device-stat"><span>Вихід</span><strong>' + d.outputW + ' Вт</strong></div>' +
      '</div>';
    return '<article class="eco-device ' + size + ' charge-' + charge + (linked ? (isBattery ? ' eco-linked-extension' : ' eco-linked-main') : '') + '" aria-label="' + d.name + ', заряд ' + d.pct + ' відсотків">' +
      '<div class="eco-device-head"><div class="eco-device-ident">' + (linked ? '<span class="eco-link-role">' + (isBattery ? 'Додаткова батарея' : 'Основна станція') + '</span>' : '') + '<strong class="eco-device-name">' + d.name + '</strong>' +
      '<span class="eco-device-model">' + typeLabel + '</span></div></div>' +
      '<div class="eco-battery"><span class="eco-battery-percent">' + d.pct + '%</span>' +
      '<span class="eco-battery-art" aria-hidden="true"><i style="width:' + d.pct + '%"></i></span></div>' +
      '<div class="eco-charge-track" role="progressbar" aria-label="Рівень заряду" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + d.pct + '">' +
      '<i style="width:' + d.pct + '%"></i></div>' +
      '<div class="eco-capacity-line">' + (d.capacityWh === null ? '<span>Ємність: уточнюється</span>' : '<strong>' + capacity + '</strong>') +
      '<span class="eco-size-note">Розмір відносно ємності</span></div>' +
      '<p class="eco-device-caption">' + info + '</p>' +
      (d.capacityWh !== null ? '<div class="eco-relative-label">Масштаб ємності відносно 5 кВт·год</div><div class="eco-relative-track" aria-label="Паспортна ємність ' + niceWh(d.capacityWh) + '"><i style="width:' + Math.round(d.capacityWh / MAX_BATTERY_WH * 1000) / 10 + '%"></i></div>' : '') +
      stats +
      '<div class="eco-device-foot"><span>Автономність: —</span></div>' +
      '<div class="eco-admin-only eco-device-admin">' +
      '<strong>' + (isBattery ? 'Додаткова батарея' : 'Керування') + '</strong>' +
      (isBattery ? '<p>Параметри цього акумулятора керуються через основну станцію ' + d.parent + '.</p>' :
        '<div class="eco-admin-controls"><label>Ліміт заряджання <input type="range" min="50" max="100" value="90" disabled></label>' +
        '<button type="button" disabled>AC: керування недоступне</button></div>') +
      '<span>Керування заблоковане до підключення та перевірки доступу.</span>' +
      '</div></article>';
  }

  // One visual power system per main station, with its battery linked inside.
  function renderDeviceGrid(devices) {
    const addons = new Map(devices.filter(d => d.type === 'battery' && d.parentId).map(d => [d.parentId, d]));
    const ids = new Set(devices.map(d => d.id));
    return devices.map(d => {
      if (d.type === 'battery' && d.parentId && ids.has(d.parentId)) return '';
      const addon = addons.get(d.id);
      if (!addon) return deviceView(d);
      const total = d.capacityWh + addon.capacityWh;
      const avg = Math.round((d.pct * d.capacityWh + addon.pct * addon.capacityWh) / total);
      return '<section class="eco-pair" aria-label="Система ' + d.name + ' із додатковою батареєю">' +
        '<div class="eco-pair-head"><div class="eco-pair-title"><span class="eco-pair-icon" aria-hidden="true">↔</span>' +
        '<div><strong>' + d.name + ' + додаткова батарея</strong>' +
        '<span class="eco-pair-subtitle">Єдина система · 2 акумулятори</span></div></div>' +
        '<div class="eco-pair-summary"><b>' + niceWh(total) + '</b><span class="eco-pair-average charge-' + level(avg) + '">' + avg + '%</span></div></div>' +
        '<div class="eco-pair-grid">' + deviceView(d, true) + deviceView(addon, true) + '</div>' +
        '<div class="eco-pair-caption"><span class="eco-linked-dot"></span>Додаткова батарея підключена до основної станції. Показники заряду кожного акумулятора окремі.</div>' +
        '</section>';
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
