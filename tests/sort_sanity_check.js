/* sort_sanity_check.js - a tiny standalone check for the client-side sort.

   This mirrors the sortProducts logic in static/script.js and verifies
   Property 4 (sorting never loses or adds rows, and "N/A" goes last) on a
   small fixed array. It is intentionally self-contained so it can run with:

       node tests/sort_sanity_check.js

   Validates: Requirements 12.4, 13.4
*/

"use strict";

// --- Same sort logic as static/script.js (kept in sync) --------------------
function parsePrice(priceText) {
  if (typeof priceText !== "string") {
    return null;
  }
  var match = priceText.match(/[0-9]+(\.[0-9]+)?/);
  return match ? parseFloat(match[0]) : null;
}

function parseRating(rating) {
  if (typeof rating === "number") {
    return rating;
  }
  var n = parseFloat(rating);
  return isNaN(n) ? null : n;
}

function sortProducts(products, field, direction) {
  var getKey = field === "price"
    ? function (p) { return parsePrice(p.price); }
    : function (p) { return parseRating(p.rating); };

  var decorated = products.map(function (p, i) {
    return { product: p, key: getKey(p), index: i };
  });

  decorated.sort(function (a, b) {
    if (a.key === null && b.key === null) { return a.index - b.index; }
    if (a.key === null) { return 1; }
    if (b.key === null) { return -1; }
    if (a.key !== b.key) {
      return direction === "asc" ? a.key - b.key : b.key - a.key;
    }
    return a.index - b.index;
  });

  return decorated.map(function (d) { return d.product; });
}

// --- Tiny assert helper ----------------------------------------------------
var failures = 0;
function assert(condition, message) {
  if (!condition) {
    failures += 1;
    console.error("FAIL: " + message);
  } else {
    console.log("ok: " + message);
  }
}

// --- Fixed sample ----------------------------------------------------------
var sample = [
  { name: "A", price: "£20.00", rating: 4.0 },
  { name: "B", price: "N/A", rating: "N/A" },
  { name: "C", price: "£10.00", rating: 2.0 },
  { name: "D", price: "£10.00", rating: "N/A" }
];

// Property 4a: the set of items is unchanged after sorting.
function sameSet(before, after) {
  if (before.length !== after.length) { return false; }
  var beforeNames = before.map(function (p) { return p.name; }).sort();
  var afterNames = after.map(function (p) { return p.name; }).sort();
  return beforeNames.join(",") === afterNames.join(",");
}

var sortedByPrice = sortProducts(sample.slice(), "price", "asc");
assert(sameSet(sample, sortedByPrice),
  "price sort keeps the same set of items");

// "N/A" price (B) must be last.
assert(sortedByPrice[sortedByPrice.length - 1].name === "B",
  "price sort places N/A price last");

// Ascending order: the two £10 items (C then D, stable) come before A (£20).
assert(sortedByPrice[0].name === "C" && sortedByPrice[1].name === "D" &&
       sortedByPrice[2].name === "A",
  "price ascending orders the £10 items (stable) before £20");

var sortedByRating = sortProducts(sample.slice(), "rating", "desc");
assert(sameSet(sample, sortedByRating),
  "rating sort keeps the same set of items");

// Both N/A ratings (B and D) must be at the end.
var lastTwo = [sortedByRating[2].name, sortedByRating[3].name].sort();
assert(lastTwo.join(",") === "B,D",
  "rating sort places both N/A ratings last");

if (failures === 0) {
  console.log("\nAll sort sanity checks passed.");
} else {
  console.error("\n" + failures + " check(s) failed.");
  process.exit(1);
}
