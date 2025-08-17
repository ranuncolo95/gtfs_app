/**
 * Autocomplete functionality using MapTiler Geocoding API
 */

/**
 * Close all autocomplete lists in the document
 */
function closeAllLists() {
    const items = document.getElementsByClassName("autocomplete-items");
    for (let i = 0; i < items.length; i++) {
        items[i].innerHTML = "";
    }
}

/**
 * Setup autocomplete for an input field
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
    
    document.addEventListener("click", function(e) {
        if (e.target !== inputElement) {
            closeAllLists();
        }
    });
}

/**
 * Reverse geocode coordinates to address
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