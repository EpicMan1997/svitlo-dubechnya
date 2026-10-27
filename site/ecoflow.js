/* EcoFlow UI preview. Deliberately no API calls, credentials, device IDs or commands. */
(function () {
  'use strict';
  const names = { dacha: 'Дача', home: 'Дім', solovky: 'Соловки', naumenky: 'Науменки' };
  const root = document.getElementById('ecoflow');
  if (!root) return;

  function updateLocation(id) {
    if (!Object.prototype.hasOwnProperty.call(names, id)) return;
    const selected = document.getElementById('locationLabel');
    const label = selected?.textContent?.trim() || names[id];
    const target = document.getElementById('eco-selected-location');
    if (target) target.textContent = label;
    root.dataset.location = id;
  }

  const selectedButton = document.querySelector('[data-location].selected');
  updateLocation(selectedButton?.dataset.location || 'dacha');
  window.addEventListener('svitlo:location-change', function (event) {
    updateLocation(event.detail?.id);
  });
})();
