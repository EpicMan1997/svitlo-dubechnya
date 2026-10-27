/* EcoFlow dashboard preview. Static demonstration only: NO API, NO secrets and NO commands. */
(function () {
  'use strict';

  // These percentages and watts are EXAMPLES, not measurements.
  // capacityWh contains nominal manufacturer capacity, never inverter output.
  const inventory = Object.freeze({
    dacha: {
      name: 'Дача',
      devices: [
        { name: 'DELTA Pro 3', capacityWh: 4096, pct: 84, inputW: 0, outputW: 620, type: 'station', id: 'dp3' },
        { name: 'Додаткова батарея DELTA Pro 3', capacityWh: 4096, pct: 82, type: 'battery', parent: 'DELTA Pro 3', id: 'dp3eb' },
        { name: 'DELTA 2', capacityWh: 1024, pct: 64, inputW: 0, outputW: 75, type: 'station', id: 'd2' },
        { name: 'DELTA 3 Plus', capacityWh: 1024, pct: 92, inputW: 120, outputW: 38, type: 'station', id: 'd3p' },
        { name: 'RIVER 3 Plus Wireless', capacityWh: 286, pct: 29, inputW: 0, outputW: 12, type: 'station', id: 'r3pw' }
      ]
    },
    home: {
      name: 'Квартира',
      devices: [
        // 5 kW is the inverter's power rating; the installed battery capacity is NOT known.
        { name: 'PowerOcean', capacityWh: null, powerKw: 5, pct: 67, inputW: 300, outputW: 760, type: 'system', id: 'po' }
      ]
    },
    solovky: {
      name: 'Соловки',
      devices: [
        { name: 'DELTA 2', capacityWh: 1024, pct: 54, inputW: 0, outputW: 125, type: 'station', id: 'd2' },
        { name: 'Додаткова батарея DELTA 2', capacityWh: 1024, pct: 49, type: 'battery', parent: 'DELTA 2', id: 'd2eb' },
        { name: 'RIVER 2', capacityWh: 256, pct: 18, inputW: 0, outputW: 26, type: 'station', id: 'r2' }
      ]
    },
    naumenky: {
      name: 'Науменки',
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
  function deviceView(d) {
    const isBattery = d.type === 'battery';
    const size = capClass(d.capacityWh);
    const capacity = d.capacityWh === null ? 'Ємність акумуляторів невідома' : niceWh(d.capacityWh);
    const typeLabel = isBattery ? 'Додаткова батарея' : d.type === 'system' ? 'Домашня система' : 'Зарядна станція';
    const info = d.powerKw ? 'Інвертор ' + d.powerKw + ' кВт · батареї не уточнені' :
      isBattery ? 'Підключена до ' + d.parent : 'Номінальна ємність ' + capacity;
    const charge = level(d.pct);
    const stats = isBattery ?
      '<div class="eco-attached-note">Вхід / вихід контролює основна станція. Потужності окремо не показуємо.</div>' :
      '<div class="eco-device-stats">' +
        '<div class="eco-device-stat"><span>Вхід · демо</span><strong>' + d.inputW + ' Вт</strong></div>' +
        '<div class="eco-device-stat"><span>Вихід · демо</span><strong>' + d.outputW + ' Вт</strong></div>' +
      '</div>';
    return '<article class="eco-device ' + size + ' charge-' + charge + '" aria-label="' + d.name + ', демонстраційний заряд ' + d.pct + ' відсотків">' +
      '<div class="eco-device-head"><div class="eco-device-ident"><strong class="eco-device-name">' + d.name + '</strong>' +
      '<span class="eco-device-model">' + typeLabel + '</span></div><span class="eco-device-badge">Демо</span></div>' +
      '<div class="eco-battery"><span class="eco-battery-percent">' + d.pct + '%</span>' +
      '<span class="eco-battery-art" aria-hidden="true"><i style="width:' + d.pct + '%"></i></span></div>' +
      '<div class="eco-charge-track" role="progressbar" aria-label="Приклад рівня заряду" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + d.pct + '">' +
      '<i style="width:' + d.pct + '%"></i></div>' +
      '<div class="eco-capacity-line">' + (d.capacityWh === null ? '<span>Ємність: уточнюється</span>' : '<strong>' + capacity + '</strong>') +
      '<span class="eco-size-note">Розмір відносно ємності</span></div>' +
      '<p class="eco-device-caption">' + info + '</p>' +
      (d.capacityWh !== null ? '<div class="eco-relative-label">Масштаб ємності відносно 4,096 кВт·год</div><div class="eco-relative-track" aria-label="Паспортна ємність ' + niceWh(d.capacityWh) + '"><i style="width:' + Math.round(d.capacityWh / 4096 * 1000) / 10 + '%"></i></div>' : '') +
      stats +
      '<div class="eco-device-foot"><span>Автономність: не розраховано</span><span>Не підключено</span></div>' +
      '<div class="eco-admin-only eco-device-admin">' +
      '<strong>Керування · майбутній адмінрежим</strong>' +
      '<div class="eco-admin-controls"><label>Ліміт заряджання <input type="range" min="50" max="100" value="90" disabled></label>' +
      '<button type="button" disabled>AC: керування недоступне</button></div>' +
      '<span>Тільки макет. Команди не виконуються, авторизації ще немає.</span>' +
      '</div></article>';
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
    $('eco-count').textContent = String(place.devices.length);
    $('eco-capacity').textContent = allKnown ? niceWh(totalWh) : 'Уточнюється';
    $('eco-capacity-note').textContent = allKnown ? 'Сума паспортних ємностей батарей' : '5 кВт інвертора не означає 5 кВт·год батареї';
    $('eco-demo-total').textContent = weighted === null ? '—' : weighted + '%';
    $('eco-demo-total').dataset.level = weighted === null ? 'unknown' : level(weighted);
    $('eco-demo-note').textContent = weighted === null ? 'Ємність PowerOcean ще невідома' : 'Приклад середньозваженого заряду';
    // Here the segment width, unlike a card's layout size, is mathematically proportional to Wh.
    $('eco-capacity-strip').innerHTML = allKnown
      ? place.devices.map(d =>
          '<span class="eco-cap-segment charge-' + level(d.pct) + '" style="flex-grow:' + d.capacityWh +
          '" title="' + d.name + ': ' + niceWh(d.capacityWh) + ', демо заряд ' + d.pct + '%">' +
          '<i style="width:' + d.pct + '%"></i></span>'
        ).join('')
      : '<span class="eco-cap-unknown">Ємність акумуляторів PowerOcean ще не уточнена (5 кВт - потужність інвертора)</span>';
    $('eco-devices').innerHTML = place.devices.map(deviceView).join('');
    $('eco-scale-note').textContent = allKnown ?
      'Площа карток приблизно відповідає ємності станцій: більше кВт·год = більша картка.' :
      'PowerOcean показано окремо: площу за ємністю визначимо після уточнення кількості батарей.';
  }

  // Front-end preview toggle. This is NOT authentication and does not grant privileges.
  function setAdminPreview(enabled) {
    root.classList.toggle('is-admin-preview', enabled);
    document.body.classList.toggle('eco-admin-visible', enabled);
    toggle.setAttribute('aria-checked', String(enabled));
    toggle.title = enabled ? 'Вимкнути демонстрацію адмінрежиму' : 'Показати майбутні елементи керування (демо)';
    $('eco-admin-mode-hint').hidden = !enabled;
  }
  toggle.addEventListener('click', function () {
    setAdminPreview(toggle.getAttribute('aria-checked') !== 'true');
  });
  setAdminPreview(false);

  const selectedButton = document.querySelector('[data-location].selected');
  const restored = selectedButton?.dataset.location || 'dacha';
  updateLocation(restored);
  window.addEventListener('svitlo:location-change', e => updateLocation(e.detail?.id));
})();
