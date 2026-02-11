import { setupAutocomplete } from './autocomplete.js';

// This listener should be OUTSIDE DOMContentLoaded - it needs to be set up immediately
window.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'route_response') {
    console.log('Route response received:', event.data.payload);

    // Send the route data to the Shiny app iframe
    const shinyIframe = document.getElementById('shiny-iframe');
    if (shinyIframe && event.data.payload && event.data.payload.route) {
      shinyIframe.contentWindow.postMessage(
        {
          type: 'route_update',
          payload: event.data.payload.route,
        },
        '*'
      );
    }
  }
});

document.addEventListener('DOMContentLoaded', function () {
  // Initialize autocomplete
  setupAutocomplete(
    document.getElementById('origin'),
    document.getElementById('origin-autocomplete'),
    document.getElementById('origin-coords')
  );

  setupAutocomplete(
    document.getElementById('destination'),
    document.getElementById('destination-autocomplete'),
    document.getElementById('destination-coords')
  );

  // Current location button (no reverse geocoding; we just set coords and a label)
  const locateMeBtn = document.getElementById('locate-me');
  if (locateMeBtn) {
    locateMeBtn.addEventListener('click', function () {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by this browser.');
        return;
      }

      navigator.geolocation.getCurrentPosition(
        function (position) {
          const lngLat = [position.coords.longitude, position.coords.latitude];
          const originCoordsEl = document.getElementById('origin-coords');
          const originInputEl = document.getElementById('origin');

          if (originCoordsEl) originCoordsEl.value = lngLat.join(',');
          if (originInputEl) originInputEl.value = 'Posizione corrente';
        },
        function (err) {
          console.error('Geolocation error:', err);
          alert('Impossibile ottenere la posizione corrente.');
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  }
});
