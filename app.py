"""app.py - the Flask web server for the Product Data Scraper.

This file does three jobs:
  1. Serve the single page (GET /).
  2. Validate a URL and run the scraper (POST /scrape).
  3. Build a CSV download from the last results using Pandas (GET /download-csv).

Scraped results are kept in two simple module-level variables while the
server runs. There is no database - this is a single-user educational demo.
"""

from datetime import datetime
from io import StringIO

import pandas as pd
from flask import Flask, jsonify, render_template, request, Response

import scraper

app = Flask(__name__)

# In-memory storage for the most recent successful scrape.
# last_results holds the list of product dicts; last_timestamp holds the
# date/time string of the last successful scrape (Requirement 9).
last_results = []
last_timestamp = None

# The longest URL we accept (Requirement 1.5).
MAX_URL_LENGTH = 2048


def validate_url(url):
    """Check a submitted URL before doing any network work.

    Returns a (is_valid, value) tuple:
      - on success: (True, cleaned_url)
      - on failure: (False, error_message)

    Checks, in order (Requirements 1.3, 1.4, 1.5):
      1. Not empty after stripping whitespace.
      2. Starts with http:// or https:// (case-insensitive).
      3. No longer than 2048 characters.
    """
    # Treat a missing value the same as an empty string.
    if url is None:
        url = ""

    cleaned = url.strip()

    # 1. Empty after stripping (Requirement 1.3).
    if cleaned == "":
        return (False, "Please enter a URL.")

    # 2. Must start with http:// or https:// (case-insensitive) (Req 1.4).
    lowered = cleaned.lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        return (
            False,
            "Please enter a valid URL starting with http:// or https://.",
        )

    # 3. Too long (Requirement 1.5).
    if len(cleaned) > MAX_URL_LENGTH:
        return (False, "That URL is too long.")

    return (True, cleaned)


@app.route("/")
def index():
    """Serve the single page with the form, controls, and table (Req 1.1)."""
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    """Validate the URL, run the scraper, and return JSON results.

    On invalid input or a fetch/parse failure we return a JSON error and
    leave the previous results and timestamp untouched, so the screen keeps
    showing the last successful scrape's timestamp (Requirement 9.4).
    """
    global last_results, last_timestamp

    # The URL may arrive as JSON or as a normal form field.
    if request.is_json:
        data = request.get_json(silent=True) or {}
        url = data.get("url", "")
    else:
        url = request.form.get("url", "")

    # Validate before any network call.
    is_valid, value = validate_url(url)
    if not is_valid:
        # value holds the friendly error message here.
        return jsonify({"status": "error", "message": value})

    # value holds the cleaned URL here.
    try:
        products = scraper.scrape_products(value)
    except scraper.ScrapeError as err:
        # A friendly fetch/parse error - show it, keep old results/timestamp.
        return jsonify({"status": "error", "message": str(err)})
    except Exception:
        # Any unexpected error - never leak a traceback to the user.
        return jsonify(
            {
                "status": "error",
                "message": "Something went wrong while scraping that page.",
            }
        )

    # Success: store the results and the time this scrape completed.
    last_results = products
    last_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    return jsonify(
        {
            "status": "ok",
            "products": products,
            "count": len(products),
            "timestamp": last_timestamp,
        }
    )


def build_csv(results, timestamp):
    """Build the CSV text from a results list and a timestamp using Pandas.

    Columns are ordered Product Name, Product Price, Product Rating, Scrape
    Timestamp (Requirements 17.1, 17.4). The same timestamp is written on
    every row (Requirement 17.3). Missing price/rating values are written as
    empty cells (Requirement 10.4).
    """
    df = pd.DataFrame(results, columns=["name", "price", "rating"])

    # Add the timestamp as the same value on every row (Requirement 17.3).
    df["timestamp"] = timestamp

    # Write empty cells for missing price/rating values (Requirement 10.4).
    # Scoped to price/rating only so a missing name still reads "N/A".
    df["price"] = df["price"].replace("N/A", "")
    df["rating"] = df["rating"].replace("N/A", "")

    # Rename to clear, spreadsheet-friendly headers (Requirement 17.2).
    df = df.rename(
        columns={
            "name": "Product Name",
            "price": "Product Price",
            "rating": "Product Rating",
            "timestamp": "Scrape Timestamp",
        }
    )

    # Lock the column order (Requirement 17.4).
    df = df[
        ["Product Name", "Product Price", "Product Rating", "Scrape Timestamp"]
    ]

    # Header row included, no index column (Requirement 10.5).
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


@app.route("/download-csv")
def download_csv():
    """Return the last results as a downloadable CSV file.

    If there is nothing scraped yet, return a friendly message and do not
    generate a file (Requirement 10.8).
    """
    if not last_results:
        return jsonify(
            {"status": "error", "message": "There is no data to export yet."}
        )

    csv_text = build_csv(last_results, last_timestamp)

    return Response(
        csv_text,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=products.csv",
        },
    )


if __name__ == "__main__":
    # Run the local development server (Requirement: run locally).
    app.run(debug=True)
