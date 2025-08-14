import { setupAutocomplete, reverseGeocode } from './autocomplete.js';

document.addEventListener('DOMContentLoaded', function() {
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
    
    // Current location button
    document.getElementById('locate-me').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                const lngLat = [position.coords.longitude, position.coords.latitude];
                document.getElementById('origin-coords').value = lngLat.join(',');
                reverseGeocode(lngLat, 'origin');
            });
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    });
    
    // Form submission handler
    document.getElementById('route-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const origin = document.getElementById('origin-coords').value;
        const destination = document.getElementById('destination-coords').value;
        
        if (!origin || !destination) {
            alert('Please select both origin and destination');
            return;
        }
        
        console.log('Route submitted:', {
            origin: origin.split(',').map(Number),
            destination: destination.split(',').map(Number)
        });
    });
});