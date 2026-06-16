# Product Data Scraper

A simple educational web app that scrapes product information (name, price, and
rating) from a single product listing page, shows the results in a table, and
lets you download them as a CSV file. Built as SkillCraft Technology Software
Development Task 4.

## Live Demo

https://your-app.onrender.com

## Features

- Scrape product **name**, **price**, and **rating** from a listing page
- Results shown in a clean, responsive table with a total count and a scrape timestamp
- **Search** by product name (live, as you type)
- **Sort** by price or rating (ascending/descending, with `N/A` values last)
- **Export to CSV** using Pandas
- **Dark mode** toggle that persists across reloads
- Friendly status messages for empty/invalid URLs, network errors, and timeouts

## Screenshots

### Light Mode

[](image.png)

### Dark Mode

[](image1.png)


## Tech Stack

- **Python** + **Flask** — web server and routes (`app.py`)
- **Requests** — download the webpage (`scraper.py`)
- **BeautifulSoup** (bs4) — parse the HTML (`scraper.py`)
- **Pandas** — build the CSV export (`app.py`)
- **HTML / CSS / JavaScript** — the frontend page, styling, and client-side search, sort, and dark mode

## How to Run

```bash
# 1. (optional) create and activate a virtual environment
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
python app.py

# 4. open the app in a browser
#    http://127.0.0.1:5000
```

## How to Use

1. Open `http://127.0.0.1:5000` in your browser.
2. Paste a product listing URL from **Books to Scrape**:
   `https://books.toscrape.com/`
3. Click **Scrape**. The table fills with the products, plus a count and timestamp.
4. Use the **search** box to filter by name, or the **sort** control to order by
   price or rating.
5. Click **Export CSV** to download the results.
6. Use the **🌙 Dark / ☀️ Light** toggle in the header to switch themes.

## Educational Note

This project is for **learning web scraping concepts** using only the Requests
library and BeautifulSoup to fetch and parse publicly available HTML. It is
demonstrated against [Books to Scrape](https://books.toscrape.com/), a site made
for scraping practice — **not** against large commercial sites such as Amazon,
Flipkart, or Myntra. It uses no proxies, no CAPTCHA solving, and no browser
automation.

## Project Structure

```
SCT_SD_4/
├── app.py              # Flask web server: routes, URL validation, CSV export with Pandas
├── scraper.py          # Fetch the page (Requests) and parse products (BeautifulSoup)
├── requirements.txt    # Python dependencies (Flask, requests, beautifulsoup4, pandas)
├── README.md           # This file
├── LICENSE             # MIT license
├── .gitignore          # Ignore venv, __pycache__, exported CSVs, etc.
├── templates/
│   └── index.html      # The single page: URL form, controls, results table
├── static/
│   ├── style.css       # Styling, CSS variables for light/dark themes, responsive layout
│   └── script.js       # Client-side: scrape request, search, sort, dark mode, CSV trigger
└── tests/
    ├── sample_books.html      # A saved snippet of a Books to Scrape page for testing
    ├── test_scraper.py        # Unit tests for the parsing/cleaning functions (pytest)
    ├── test_app.py            # Unit tests for URL validation and CSV export (pytest)
    └── sort_sanity_check.js   # A small Node check for the client-side sort
```

## Running the Tests

```bash
# Python tests (from the SCT_SD_4 folder)
pip install pytest
pytest

# Optional client-side sort sanity check
node tests/sort_sanity_check.js
```

## License

Released under the [MIT License](LICENSE).

## Internship Information

Organization: SkillCraft Technology

Track: Software Development Internship

Task: SCT_SD_4 – Product Data Scraper

