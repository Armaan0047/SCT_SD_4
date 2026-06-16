"""scraper.py - fetch a webpage and parse product data from it.

This module holds the scraping logic for the Product Data Scraper.
It uses the Requests library to download a page and BeautifulSoup to
read the HTML. Functions are kept small and simple.
"""

import requests
from bs4 import BeautifulSoup


class ScrapeError(Exception):
    """A simple, friendly error we can show to the user.

    We raise this instead of letting raw requests errors bubble up, so
    app.py can just read the message and put it on the screen.
    """
    pass


def fetch_page(url):
    """Download the HTML at the given URL and return it as text.

    Sends an HTTP GET request with a 10 second timeout. If anything goes
    wrong (timeout, network problem, or a bad HTTP status code) we raise
    a ScrapeError with a clear, friendly message.
    """
    try:
        # Send the GET request with a 10 second timeout (Requirement 2.1).
        response = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        # The request took too long (Requirement 2.3).
        raise ScrapeError("The request timed out. Please try again.")
    except requests.exceptions.RequestException:
        # ConnectionError and any other network problem (Requirement 2.2).
        raise ScrapeError(
            "Could not reach that page. Check the URL or your connection."
        )

    # If the server answered with an error status code (Requirement 2.4).
    if response.status_code >= 400:
        raise ScrapeError(
            "The page could not be retrieved (status {}).".format(
                response.status_code
            )
        )

    # Status code is 200-399, so return the page text (Requirement 2.5).
    return response.text


# Maps the Books to Scrape star-rating words to their numbers.
# The page shows ratings as a CSS class word like "Three", so we turn
# that word into a number. Keys are lowercase so the lookup is
# case-insensitive.
_RATING_WORDS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
}


def clean_name(text):
    """Tidy up a product name.

    Removes leading/trailing whitespace. If nothing is left after
    stripping (or the input was missing), we record the name as "N/A"
    (Requirements 3.2, 3.3).
    """
    # Guard against None or other missing input.
    if text is None:
        return "N/A"

    cleaned = text.strip()
    if cleaned == "":
        return "N/A"
    return cleaned


def clean_price(text):
    """Tidy up a product price, keeping the raw text exactly.

    Strips surrounding whitespace but keeps the currency symbol and the
    price text as displayed. Returns "N/A" if the price is missing or
    only whitespace (Requirement 4.2). If the text is longer than 100
    characters, we keep only the first 100 (Requirement 4.3).
    """
    # Guard against None or other missing input.
    if text is None:
        return "N/A"

    cleaned = text.strip()
    if cleaned == "":
        return "N/A"

    # Keep only the first 100 characters if it is very long.
    return cleaned[:100]


def clean_rating(value):
    """Turn a rating into a float between 0.0 and 5.0 inclusive.

    Accepts either a Books to Scrape star word ("One".."Five",
    case-insensitive) or a numeric value. Returns "N/A" when the rating
    is missing, unknown, or outside the 0.0-5.0 range
    (Requirements 5.1, 5.2, 5.3).
    """
    # Missing rating -> "N/A" (Requirement 5.2).
    if value is None:
        return "N/A"

    # If it is text, first try the star-word mapping (e.g. "Three").
    if isinstance(value, str):
        word = value.strip().lower()
        if word == "":
            return "N/A"
        if word in _RATING_WORDS:
            return _RATING_WORDS[word]
        # Not a known word, so try reading it as a number like "3" or "4.5".
        try:
            number = float(word)
        except ValueError:
            # Unknown / unreadable rating -> "N/A" (Requirement 5.3).
            return "N/A"
    else:
        # Already a number (int or float) -> use it directly.
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "N/A"

    # Only accept numbers within the valid 0.0-5.0 range (Requirement 5.1).
    if 0.0 <= number <= 5.0:
        return number

    # Out of range -> "N/A" (Requirement 5.3).
    return "N/A"


def parse_products(html):
    """Parse the page HTML into a list of product dictionaries.

    Uses BeautifulSoup to find each product block and pull out the name,
    price, and rating. Every dictionary returned always has all three
    keys ("name", "price", "rating"); a missing or broken value becomes
    "N/A" via the cleaning helpers (Requirements 3.1, 4.1, 5.1, 6.1).

    On the Books to Scrape demo site each product is an
    <article class="product_pod"> containing:
      - the title in  <h3><a title="...">  (the link text is a fallback)
      - the price in   <p class="price_color">
      - the rating in  <p class="star-rating Three">  where the second
        class word ("Three") is the rating

    If extracting one product raises an error, we record the affected
    field as "N/A" and keep going so a single bad product never breaks
    the whole parse (Requirement 4.4).
    """
    # Parse the HTML using Python's built-in parser (no extra install).
    soup = BeautifulSoup(html, "html.parser")

    products = []

    # Each product on Books to Scrape is an <article class="product_pod">.
    for pod in soup.select("article.product_pod"):
        # Start every product as "N/A" so the dict always has all keys,
        # even if any single field below fails to read.
        name = "N/A"
        price = "N/A"
        rating = "N/A"

        # --- Name: from <h3><a title="..."> (fall back to the link text) ---
        try:
            link = pod.select_one("h3 a")
            if link is not None:
                # Prefer the full title attribute; some names are truncated
                # in the visible link text but complete in title=.
                title = link.get("title")
                if title is None:
                    title = link.get_text()
                name = clean_name(title)
        except Exception:
            # Any unexpected problem with this field -> leave it as "N/A".
            name = "N/A"

        # --- Price: from the element with class "price_color" ---
        try:
            price_el = pod.select_one(".price_color")
            if price_el is not None:
                price = clean_price(price_el.get_text())
        except Exception:
            price = "N/A"

        # --- Rating: the second word of the "star-rating" CSS class ---
        try:
            rating_el = pod.select_one(".star-rating")
            if rating_el is not None:
                # The class looks like ["star-rating", "Three"]; we want
                # the word that is not "star-rating".
                classes = rating_el.get("class", [])
                rating_word = None
                for css_class in classes:
                    if css_class != "star-rating":
                        rating_word = css_class
                        break
                rating = clean_rating(rating_word)
        except Exception:
            rating = "N/A"

        products.append({"name": name, "price": price, "rating": rating})

    # Return the list (empty if no product blocks were found).
    return products


def scrape_products(url):
    """Fetch a page and parse its products in one call.

    This is the simple orchestrator app.py calls. It first downloads the
    HTML with fetch_page, then turns it into a list of product dicts with
    parse_products, and returns that list (Requirements 2.5, 6.1).

    Any fetch problem raises a ScrapeError from fetch_page. We let that
    bubble up unchanged so app.py can read its friendly message and show
    it to the user as a status message.
    """
    html = fetch_page(url)
    return parse_products(html)
