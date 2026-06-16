"""Unit tests for scraper.py parsing and cleaning functions.

These tests run fully offline using a saved snippet of a Books to Scrape
page (tests/sample_books.html), so they never depend on the live site.

Run from the SCT_SD_4 folder with:
    pytest
"""

import os
import sys

# Make sure we can import scraper.py from the project root (the folder
# above this tests/ directory), no matter where pytest is launched from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scraper import (  # noqa: E402  (import after sys.path tweak)
    parse_products,
    clean_name,
    clean_price,
    clean_rating,
)

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_books.html")


def load_sample():
    """Read the saved Books to Scrape snippet as text."""
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        return f.read()


def test_parse_products_returns_expected_count():
    """The sample has exactly 4 product blocks."""
    products = parse_products(load_sample())
    assert len(products) == 4


def test_known_product_fields():
    """The first product has the expected name, price, and rating."""
    products = parse_products(load_sample())
    first = products[0]
    assert first["name"] == "A Light in the Attic"
    assert first["price"] == "£51.77"
    assert first["rating"] == 3.0


def test_missing_rating_is_na():
    """The fourth product has no star-rating element, so rating is 'N/A'."""
    products = parse_products(load_sample())
    no_rating = products[3]
    assert no_rating["name"] == "A Book With No Rating"
    assert no_rating["rating"] == "N/A"


def test_clean_name_empty_returns_na():
    assert clean_name("") == "N/A"
    assert clean_name("   ") == "N/A"
    assert clean_name(None) == "N/A"
    assert clean_name("  Hello  ") == "Hello"


def test_clean_price_empty_returns_na():
    assert clean_price("") == "N/A"
    assert clean_price("   ") == "N/A"
    assert clean_price(None) == "N/A"
    assert clean_price("  £9.99 ") == "£9.99"


def test_clean_price_truncates_to_100_chars():
    long_text = "x" * 250
    assert len(clean_price(long_text)) == 100


def test_clean_rating_star_words():
    assert clean_rating("Three") == 3.0
    assert clean_rating("five") == 5.0


def test_clean_rating_missing_or_unreadable_returns_na():
    assert clean_rating(None) == "N/A"
    assert clean_rating("") == "N/A"
    assert clean_rating("banana") == "N/A"
    assert clean_rating(9.0) == "N/A"  # out of 0.0-5.0 range


# --- Property 1: Every product has all three fields -------------------------
def test_property_every_product_has_three_fields():
    """Every returned dict always has name, price, and rating keys.

    Validates: Requirements 3.3, 4.2, 5.1
    """
    products = parse_products(load_sample())
    assert products  # not empty
    for product in products:
        assert "name" in product
        assert "price" in product
        assert "rating" in product


# --- Property 2: Rating is always valid -------------------------------------
def test_property_rating_is_always_valid():
    """Each rating is a float in 0.0-5.0 or the string 'N/A'.

    Validates: Requirements 5.1, 5.2, 5.3
    """
    products = parse_products(load_sample())
    for product in products:
        rating = product["rating"]
        if rating != "N/A":
            assert isinstance(rating, float)
            assert 0.0 <= rating <= 5.0
