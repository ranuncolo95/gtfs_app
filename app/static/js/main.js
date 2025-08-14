// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const shinyIframe = document.getElementById('shiny-iframe');
    
    // Initialize event listeners
    function initEventListeners() {
        // Map style change
        document.getElementById('map-style').addEventListener('change', (e) => {
            sendMessageToShiny({
                type: 'map-style-change',
                value: e.target.value
            });
        });
        
        // Opacity change
        document.getElementById('opacity').addEventListener('input', (e) => {
            sendMessageToShiny({
                type: 'opacity-change',
                value: parseFloat(e.target.value)
            });
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            sendMessageToShiny({
                type: 'refresh-data'
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
    }
    
    // Update coordinate display
    function updateCoordinates(lat, lng) {
        document.getElementById('lat').textContent = lat.toFixed(4);
        document.getElementById('lng').textContent = lng.toFixed(4);
    }
    
    // Initialize everything
    initEventListeners();
});