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
    document.getElementById('route-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Add loading state
        const form = e.target;
        const submitButton = form.querySelector('button[type="submit"]');
        form.classList.add('loading');
        submitButton.disabled = true;

        const origin = document.getElementById('origin-coords').value;
        const destination = document.getElementById('destination-coords').value;
        
        if (!origin || !destination) {
            alert('Please select both origin and destination');
            form.classList.remove('loading');
            submitButton.disabled = false;
            return;
        }
        
        try {
            const response = await fetch('/api/calculate-route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    origin: origin.split(',').map(Number),
                    destination: destination.split(',').map(Number)
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            console.log('Route calculation result:', data);
            
            // Here you can handle the response data
            alert(`Route calculated! Distance: ${data.route.distance}m, Duration: ${data.route.duration}min`);
            
        } catch (error) {
            console.error('Error calculating route:', error);
            alert('Error calculating route. Please try again.');
        } finally {
            // Remove loading state whether successful or not
            form.classList.remove('loading');
            submitButton.disabled = false;
        }
    });
});