// Wait for DOM to be fully loaded
import { setShinyReference, setupAutocomplete, reverseGeocode } from './autocomplete.js';

document.addEventListener('DOMContentLoaded', function() {
    const shinyIframe = document.getElementById('shiny-iframe');
    
    // Initialize autocomplete
    function initAutocomplete() {
        // Set the shiny reference for autocomplete functions
        setShinyReference(shinyIframe);
        
        // Setup autocomplete for origin and destination
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
                    flyToLocation(lngLat);
                });
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        });
    }
    
    // Initialize event listeners
    function initEventListeners() {
        // Route form submission
        document.getElementById('route-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const origin = document.getElementById('origin-coords').value;
            const destination = document.getElementById('destination-coords').value;
            
            if (!origin || !destination) {
                alert('Please select both origin and destination');
                return;
            }
            
            sendMessageToShiny({
                type: 'route-request',
                origin: origin.split(',').map(Number),
                destination: destination.split(',').map(Number)
            });
        });
        
        // Listen for messages from Shiny
        window.addEventListener('message', handleMessageFromShiny);
    }
    
    // Helper function to send messages to Shiny
    function sendMessageToShiny(message) {
        shinyIframe.contentWindow.postMessage(message, '*');
    }
    
    // Handle messages from Shiny
    function handleMessageFromShiny(event) {
        if (event.data.type === 'map-move') {
            updateCoordinates(event.data.lat, event.data.lng);
        }
        // Add other message types as needed
    }
    
    // Initialize everything
    initAutocomplete();
    initEventListeners();
});