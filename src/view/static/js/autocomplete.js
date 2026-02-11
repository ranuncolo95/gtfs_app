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

function removeActive(items) {
  if (!items) return;
  for (let i = 0; i < items.length; i++) {
    items[i].classList.remove("autocomplete-active");
  }
}

function addActive(items, currentFocus) {
  if (!items || !items.length) return -1;
  removeActive(items);

  if (currentFocus >= items.length) currentFocus = 0;
  if (currentFocus < 0) currentFocus = items.length - 1;

  items[currentFocus].classList.add("autocomplete-active");
  // Keep the active item visible if the list scrolls
  try {
    items[currentFocus].scrollIntoView({ block: "nearest" });
  } catch {
    // ignore scrollIntoView issues in older browsers
  }
  return currentFocus;
}

/**
 * Setup autocomplete for an input field
 */
export function setupAutocomplete(inputElement, resultsElement, coordsElement) {
  let currentFocus = -1;

  inputElement.addEventListener("input", function () {
    const query = this.value;

    // Any manual edit invalidates previously selected coordinates
    if (coordsElement) coordsElement.value = "";

    if (query.length < 3) {
      closeAllLists();
      return;
    }

    fetch(`/api/geocode?q=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((data) => {
        const features = data.features;
        closeAllLists();
        currentFocus = -1;

        if (!features || !features.length) return;

        resultsElement.innerHTML = "";
        features.forEach((feature) => {
          const item = document.createElement("div");
          item.innerHTML = `<strong>${feature.place_name}</strong>`;

          item.addEventListener("click", function () {
            inputElement.value = feature.place_name;
            if (coordsElement) {
              coordsElement.value = `${feature.center[0]},${feature.center[1]}`;
            }
            closeAllLists();
          });

          resultsElement.appendChild(item);
        });
      })
      .catch((error) => console.error("Geocoding error:", error));
  });

  inputElement.addEventListener("keydown", function (e) {
    const items = resultsElement.getElementsByTagName("div");

    if (e.key === "ArrowDown") {
      if (items.length === 0) return;
      e.preventDefault();
      currentFocus++;
      currentFocus = addActive(items, currentFocus);
    } else if (e.key === "ArrowUp") {
      if (items.length === 0) return;
      e.preventDefault();
      currentFocus--;
      currentFocus = addActive(items, currentFocus);
    } else if (e.key === "Enter") {
      // If suggestions are open, Enter selects; otherwise keep default (form submit)
      if (items.length > 0 && currentFocus > -1) {
        e.preventDefault();
        items[currentFocus].click();
      }
    } else if (e.key === "Escape") {
      closeAllLists();
      currentFocus = -1;
    }
  });

  document.addEventListener("click", function (e) {
    // Close if click is outside the input and outside the results container
    if (e.target !== inputElement && !resultsElement.contains(e.target)) {
      closeAllLists();
      currentFocus = -1;
    }
  });
}
