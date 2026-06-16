/* script.js - client-side behavior for the Product Data Scraper.

   Responsibilities:
     - Send the scrape request and render the results table (Req 6, 7, 8, 9).
     - Search by name and sort by price/rating in the browser (Req 11, 12, 13).
     - Trigger the CSV download (Req 10).
     - Toggle and persist dark mode (Req 14).

   Search, sort, and dark mode all work on data already in the browser, so
   they feel instant and never contact the server again. */

(function () {
  "use strict";

  // --- In-memory state -----------------------------------------------------
  // allProducts holds the full scraped list; the table is always rendered
  // from a filtered + sorted view of this array.
  var allProducts = [];

  var PLACEHOLDER = "N/A";

  // --- Element references --------------------------------------------------
  var urlInput = document.getElementById("urlInput");
  var scrapeButton = document.getElementById("scrapeButton");
  var statusMessage = document.getElementById("statusMessage");
  var countDisplay = document.getElementById("countDisplay");
  var timestampDisplay = document.getElementById("timestampDisplay");
  var searchInput = document.getElementById("searchInput");
  var sortSelect = document.getElementById("sortSelect");
  var resultsTable = document.getElementById("resultsTable");
  var resultsBody = document.getElementById("resultsBody");
  var exportButton = document.getElementById("exportButton");
  var darkModeToggle = document.getElementById("darkModeToggle");

  // --- Status helper -------------------------------------------------------
  // Shows exactly one status message at a time (Requirement 8.5).
  function setStatus(text) {
    statusMessage.textContent = text;
  }

  // --- Price parsing -------------------------------------------------------
  // Pull the first number out of a price string like "£51.77". Returns null
  // when there is no readable number (used to push N/A prices last).
  function parsePrice(priceText) {
    if (typeof priceText !== "string") {
      return null;
    }
    var match = priceText.match(/[0-9]+(\.[0-9]+)?/);
    if (!match) {
      return null;
    }
    return parseFloat(match[0]);
  }

  // Numeric value of a rating, or null when it is "N/A"/not a number.
  function parseRating(rating) {
    if (typeof rating === "number") {
      return rating;
    }
    var n = parseFloat(rating);
    return isNaN(n) ? null : n;
  }

  // --- Sorting (Req 12, 13) ------------------------------------------------
  // Stable sort by a numeric key. Items whose key is null (N/A) always go
  // last, in both ascending and descending order. Equal values keep their
  // original relative order (we decorate with the original index for
  // stability across all browsers).
  function sortProducts(products, field, direction) {
    var getKey = field === "price"
      ? function (p) { return parsePrice(p.price); }
      : function (p) { return parseRating(p.rating); };

    var decorated = products.map(function (p, i) {
      return { product: p, key: getKey(p), index: i };
    });

    decorated.sort(function (a, b) {
      // N/A (null) always sorts after real numbers.
      if (a.key === null && b.key === null) {
        return a.index - b.index;
      }
      if (a.key === null) {
        return 1;
      }
      if (b.key === null) {
        return -1;
      }
      if (a.key !== b.key) {
        return direction === "asc" ? a.key - b.key : b.key - a.key;
      }
      // Equal keys: keep original order (stable) (Req 12.5, 13.5).
      return a.index - b.index;
    });

    return decorated.map(function (d) { return d.product; });
  }

  // --- Build the view (filter -> sort) and render --------------------------
  function getVisibleProducts() {
    var query = searchInput.value.trim().toLowerCase();

    // Filter by name (trimmed, case-insensitive) (Req 11.2).
    var filtered = allProducts.filter(function (p) {
      var name = (p.name || "").toLowerCase();
      return name.indexOf(query) !== -1;
    });

    // Sort if a sort option is selected (Req 12, 13).
    var sortValue = sortSelect.value;
    if (sortValue) {
      var parts = sortValue.split("-"); // e.g. "price-asc"
      filtered = sortProducts(filtered, parts[0], parts[1]);
    }

    return filtered;
  }

  function renderTable() {
    var visible = getVisibleProducts();

    // Clear current rows.
    resultsBody.innerHTML = "";

    if (allProducts.length === 0) {
      // Nothing scraped yet (or last scrape found nothing): hide table.
      resultsTable.classList.add("hidden");
      return;
    }

    if (visible.length === 0) {
      // A search filtered everything out (Req 11.4).
      resultsTable.classList.add("hidden");
      setStatus("No matching products were found.");
      updateCount(0);
      return;
    }

    // Build one row per visible product (Req 6.1, 6.2).
    visible.forEach(function (p) {
      var tr = document.createElement("tr");
      tr.appendChild(makeCell(p.name));
      tr.appendChild(makeCell(p.price));
      tr.appendChild(makeCell(formatRating(p.rating)));
      resultsBody.appendChild(tr);
    });

    resultsTable.classList.remove("hidden");
    updateCount(visible.length);

    // Clear a stale "no matching" message once results are visible again.
    if (statusMessage.textContent === "No matching products were found.") {
      setStatus("Scraping succeeded.");
    }
  }

  // A table cell, showing placeholder text for missing values (Req 6.3).
  function makeCell(value) {
    var td = document.createElement("td");
    if (value === undefined || value === null || value === "" ||
        value === PLACEHOLDER) {
      td.textContent = PLACEHOLDER;
    } else {
      td.textContent = value;
    }
    return td;
  }

  // Ratings are numbers; show one decimal place, or N/A.
  function formatRating(rating) {
    if (typeof rating === "number") {
      return rating.toFixed(1);
    }
    return PLACEHOLDER;
  }

  // Update the visible-vs-total count display (Req 7.1, 7.3).
  function updateCount(visibleCount) {
    var total = allProducts.length;
    if (visibleCount === total) {
      countDisplay.textContent = "Total products: " + total;
    } else {
      countDisplay.textContent =
        "Showing " + visibleCount + " of " + total;
    }
    countDisplay.classList.remove("hidden");
  }

  // --- Enable / disable the controls based on whether we have data ---------
  function setControlsEnabled(enabled) {
    searchInput.disabled = !enabled;
    sortSelect.disabled = !enabled;
    exportButton.disabled = !enabled;
    if (!enabled) {
      searchInput.value = "";
      sortSelect.value = "";
    }
  }

  // --- Scrape request (Req 1, 6, 7, 8, 9) ----------------------------------
  function doScrape() {
    var url = urlInput.value.trim();

    // Quick client-side empty check (server validates again) (Req 1.3).
    if (url === "") {
      setStatus("Please enter a URL.");
      return;
    }

    // Show in-progress status immediately (Req 8.1).
    setStatus("Scraping... please wait.");

    fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url })
    })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data.status !== "ok") {
          // Failure: show the message, keep the old timestamp (Req 8.4, 9.4).
          setStatus(data.message || "Scraping failed.");
          return;
        }

        // Store the products in memory for search/sort (Req 6).
        allProducts = data.products || [];

        if (data.count === 0) {
          // Scrape succeeded but found nothing (Req 6.4, 7.2).
          setStatus("No products were found on that page.");
          resultsTable.classList.add("hidden");
          setControlsEnabled(false);
          updateCount(0);
        } else {
          setStatus("Scraping succeeded.");
          setControlsEnabled(true);
          renderTable();
        }

        // Update the timestamp from the successful response (Req 9.1).
        if (data.timestamp) {
          timestampDisplay.textContent = "Scraped at: " + data.timestamp;
          timestampDisplay.classList.remove("hidden");
        }
      })
      .catch(function () {
        setStatus("Could not reach the server. Please try again.");
      });
  }

  // --- CSV export (Req 10) -------------------------------------------------
  function doExport() {
    if (allProducts.length === 0) {
      setStatus("There is no data to export yet.");
      return;
    }
    // Navigate to the download route; the server returns the file.
    window.location.href = "/download-csv";
    setStatus("Export started - check your downloads.");
  }

  // --- Dark mode (Req 14) --------------------------------------------------
  var STORAGE_KEY = "pds-theme";

  function applyTheme(theme) {
    if (theme === "dark") {
      document.body.classList.add("dark");
      darkModeToggle.textContent = "☀️ Light";
    } else {
      document.body.classList.remove("dark");
      darkModeToggle.textContent = "🌙 Dark";
    }
  }

  function toggleTheme() {
    var isDark = document.body.classList.contains("dark");
    var next = isDark ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {
      // localStorage may be unavailable; the toggle still works for now.
    }
  }

  function loadTheme() {
    var saved = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      saved = null;
    }
    // Apply saved theme, otherwise default to light (Req 14.2, 14.6).
    applyTheme(saved === "dark" ? "dark" : "light");
  }

  // --- Wire up events ------------------------------------------------------
  scrapeButton.addEventListener("click", doScrape);
  urlInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      doScrape();
    }
  });
  searchInput.addEventListener("input", function () {
    // Re-render on each keystroke (Req 11.2). renderTable handles the
    // "no matching products" message and count update.
    if (searchInput.value.trim() === "") {
      setStatus("Scraping succeeded.");
    }
    renderTable();
  });
  sortSelect.addEventListener("change", renderTable);
  exportButton.addEventListener("click", doExport);
  darkModeToggle.addEventListener("click", toggleTheme);

  // --- On page load --------------------------------------------------------
  loadTheme();
  setControlsEnabled(false);

  // Expose the sort helper for the optional sanity check (task 8.4).
  window.__pds = { sortProducts: sortProducts };
})();
