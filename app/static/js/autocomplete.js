/**
 * Autocomplete functionality using MapTiler Geocoding API
 */

// No longer need map reference since we'll communicate with Shiny
let shinyIframe;

/**
 * Set the Shiny iframe reference for use in autocomplete functions
 * @param {HTMLIFrameElement} iframe - The Shiny iframe element
 */
export function setShinyReference(iframe) {
    shinyIframe = iframe;
}

/**
 * Close all autocomplete lists in the document
 * @param {HTMLElement} currentInput - The currently active input element (optional)
 */
function closeAllLists(currentInput) {
    const items = document.getElementsByClassName("autocomplete-items");
    for (let i = 0; i < items.length; i++) {
        if (currentInput !== items[i] && currentInput !== items[i].previousElementSibling) {
            items[i].innerHTML = "";
        }
    }
}

/**
 * Add active class to the current autocomplete item
 * @param {HTMLCollection} items - Collection of autocomplete items
 */
function addActive(items) {
    if (!items) return false;
    removeActive(items);
    if (currentFocus >= items.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (items.length - 1);
    items[currentFocus].classList.add("autocomplete-active");
}

/**
 * Remove active class from all autocomplete items
 * @param {HTMLCollection} items - Collection of autocomplete items
 */
function removeActive(items) {
    for (let i = 0; i < items.length; i++) {
        items[i].classList.remove("autocomplete-active");
    }
}

/**
 * Fly to a specific location by sending message to Shiny
 * @param {Array} lngLat - [longitude, latitude] coordinates
 * @param {number} zoom - Zoom level (default: 14)
 */
function flyToLocation(lngLat, zoom = 14) {
    if (shinyIframe) {
        shinyIframe.contentWindow.postMessage({
            type: 'fly-to',
            center: lngLat,
            zoom: zoom
        }, '*');
    }
}

/**
 * Setup autocomplete for an input field
 * @param {HTMLElement} inputElement - The input element
 * @param {HTMLElement} resultsElement - The dropdown results container
 * @param {HTMLElement} coordsElement - Hidden input for coordinates
 */
export function setupAutocomplete(inputElement, resultsElement, coordsElement) {
    let currentFocus = -1;
    
    inputElement.addEventListener("input", function(e) {
        const query = this.value;
        if (query.length < 3) {
            closeAllLists();
            return;
        }
        
        fetch(`/api/geocode?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                const features = data.features;
                closeAllLists();
                
                if (!features || !features.length) return;
                
                resultsElement.innerHTML = '';
                features.forEach((feature) => {
                    const item = document.createElement("div");
                    item.innerHTML = `<strong>${feature.place_name}</strong>`;
                    item.addEventListener("click", function() {
                        inputElement.value = feature.place_name;
                        coordsElement.value = `${feature.center[0]},${feature.center[1]}`;
                        closeAllLists();
                        flyToLocation(feature.center);
                    });
                    resultsElement.appendChild(item);
                });
            })
            .catch(error => console.error('Geocoding error:', error));
    });
    
    inputElement.addEventListener("keydown", function(e) {
        const items = resultsElement.getElementsByTagName("div");
        
        if (e.key === "ArrowDown") {
            currentFocus++;
            addActive(items);
        } else if (e.key === "ArrowUp") {
            currentFocus--;
            addActive(items);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (currentFocus > -1 && items.length > 0) {
                items[currentFocus].click();
            }
        }
    });
    
    // Close the dropdown when clicking outside
    document.addEventListener("click", function(e) {
        if (e.target !== inputElement) {
            closeAllLists();
        }
    });
}

/**
 * Reverse geocode coordinates to address
 * @param {Array} lngLat - [longitude, latitude] coordinates
 * @param {string} fieldPrefix - Prefix for field IDs ('origin' or 'destination')
 */
export function reverseGeocode(lngLat, fieldPrefix) {
    fetch(`/api/reverse-geocode?lng=${lngLat[0]}&lat=${lngLat[1]}`)
        .then(response => response.json())
        .then(data => {
            if (data.features && data.features.length > 0) {
                const feature = data.features[0];
                document.getElementById(fieldPrefix).value = feature.place_name;
                document.getElementById(`${fieldPrefix}-coords`).value = `${lngLat[0]},${lngLat[1]}`;
            }
        })
        .catch(error => console.error('Reverse geocoding error:', error));
}