"""Unit tests for app.py helpers and CSV export.

These tests cover the URL validation helper and the Pandas CSV builder.
They run offline and never start the Flask server.

Run from the SCT_SD_4 folder with:
    pytest
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import validate_url, build_csv  # noqa: E402


# --- validate_url -----------------------------------------------------------
def test_validate_url_accepts_good_url():
    ok, value = validate_url("  https://books.toscrape.com/  ")
    assert ok is True
    # The cleaned URL is returned trimmed.
    assert value == "https://books.toscrape.com/"


def test_validate_url_rejects_empty():
    ok, message = validate_url("   ")
    assert ok is False
    assert "enter a URL" in message


def test_validate_url_rejects_bad_scheme():
    ok, message = validate_url("ftp://example.com")
    assert ok is False
    assert "http://" in message


def test_validate_url_accepts_scheme_case_insensitively():
    ok, value = validate_url("HTTPS://EXAMPLE.COM")
    assert ok is True
    assert value == "HTTPS://EXAMPLE.COM"


def test_validate_url_rejects_too_long():
    long_url = "https://example.com/" + ("a" * 2100)
    ok, message = validate_url(long_url)
    assert ok is False
    assert "too long" in message


# --- Property 5: CSV row count is consistent --------------------------------
def test_property_csv_row_count_is_consistent():
    """The CSV has one header row plus one data row per product, and every
    data row carries the same timestamp.

    Validates: Requirements 10.2, 17.3
    """
    sample_results = [
        {"name": "Book A", "price": "£10.00", "rating": 3.0},
        {"name": "Book B", "price": "£20.00", "rating": "N/A"},
        {"name": "Book C", "price": "N/A", "rating": 5.0},
    ]
    timestamp = "2025-01-15 14:30"

    csv_text = build_csv(sample_results, timestamp)

    # Split into non-empty lines (the file ends with a trailing newline).
    lines = [line for line in csv_text.splitlines() if line != ""]

    # 1 header row + one row per product.
    assert len(lines) == 1 + len(sample_results)

    # The header lists the four expected columns in order.
    assert lines[0] == "Product Name,Product Price,Product Rating,Scrape Timestamp"

    # Every data row ends with the same timestamp value.
    for data_line in lines[1:]:
        assert data_line.endswith(timestamp)


def test_csv_writes_empty_cells_for_na():
    """Missing price/rating ('N/A') become empty cells, not the text N/A."""
    sample_results = [{"name": "Book B", "price": "N/A", "rating": "N/A"}]
    csv_text = build_csv(sample_results, "2025-01-15 14:30")
    lines = [line for line in csv_text.splitlines() if line != ""]
    # Data row: name, empty price, empty rating, timestamp.
    assert lines[1] == "Book B,,,2025-01-15 14:30"
