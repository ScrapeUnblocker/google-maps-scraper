# google-maps-scraper

[![CI](https://github.com/ScrapeUnblocker/google-maps-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/ScrapeUnblocker/google-maps-scraper/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Scrape Google Maps / Google Local business listings as clean JSON** — name,
rating, review count, category, address, phone, website, price level, opening
hours and a sponsored flag — for any keyword and market.

Powered by [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
and its **Google Local plugin**, so you never touch anti-bot systems, proxies or
browser rendering yourself — you send a keyword, you get structured data back.

Great for **local lead generation, competitor research, review monitoring and
market analysis** across cities and verticals.

## Features

- 🗺️ Search the Google Maps local pack for any keyword (put the location in the query).
- 🧾 Clean, typed records — no HTML parsing, no brittle CSS selectors.
- 🌐 Country targeting via `--country` (proxy exit) plus Google's `gl` / `hl` codes.
- 🏙️ `search_many` collects one vertical across many cities and **de-dupes** by name + address.
- 🚫 Optional `--no-sponsored` to drop ad listings.
- 🧰 Library **and** CLI, with JSON or CSV output.
- ✅ Fully mocked test suite — the examples are the only thing that spends credit.

## Install

```bash
pip install .
# or, just the runtime dependency:
pip install -r requirements.txt
```

## Configuration

Set your API key (get one from
[scrapeunblocker.com](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)):

```bash
export SCRAPEUNBLOCKER_KEY=your_key_here
```

or copy `.env.example` to `.env`.

## CLI usage

```bash
# Search and print JSON
google-maps-scraper "coffee shops in chicago" --country US

# Service vertical with a CSV of leads, ads excluded
google-maps-scraper "plumbers in austin tx" --country US --no-sponsored -f csv -o leads.csv

# Target a different market
google-maps-scraper "dentists in london" --gl uk --hl en
```

```
usage: google-maps-scraper [-h] [-c PROXY_COUNTRY] [--gl GL] [--hl HL]
                           [--no-sponsored] [-l LIMIT] [-f {json,csv}]
                           [-o OUTPUT] [--api-key API_KEY] [--version]
                           keyword
```

## Library usage

```python
from google_maps_scraper import GoogleMapsScraper

scraper = GoogleMapsScraper()  # reads SCRAPEUNBLOCKER_KEY from the environment

for place in scraper.search("coffee shops in chicago", proxy_country="US"):
    print(place.name, place.rating, place.reviews, place.address)

# Build a de-duplicated lead list across several cities
queries = [f"dentists in {c}" for c in ("chicago", "austin tx", "seattle")]
leads = scraper.search_many(queries, proxy_country="US", include_sponsored=False)
```

### Example output

```json
[
  {
    "position": 1,
    "name": "Sawada Coffee",
    "rating": 4.6,
    "reviews": 2200,
    "price": "$1–10",
    "category": "Coffee shop",
    "address": "112 N Green St",
    "phone": null,
    "website": null,
    "hours": null,
    "review_snippet": "i stop by here about every trip to chicago just for their chai latte!",
    "sponsored": false,
    "keyword": "coffee shops in chicago",
    "extra": {}
  }
]
```

> Field availability depends on the vertical and on what Google renders in the
> local pack for a query: service businesses often expose `phone` and `hours`,
> `website` is rarely surfaced in search results, and `price` only appears where a
> price level is shown. Missing values are returned as `null`, never guessed. The
> pack returns up to ~20 businesses per search — use `search_many` across cities
> or verticals to gather more.

## Project layout

```
src/google_maps_scraper/
  __init__.py      package exports + version
  models.py        Place dataclass, normalization, dedupe, CSV, number parsing
  scraper.py       GoogleMapsScraper client (search, search_many, retries)
  cli.py           argparse command-line interface
examples/          runnable scripts (JSON, CSV, multi-city leads)
tests/             offline unit tests (the HTTP layer is mocked)
```

## Development

```bash
make install   # editable install + dev tools + pre-commit
make lint      # ruff check
make format    # ruff format + autofix
make test      # pytest (no API credit used)
```

## Links

- 🌐 [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)
- 📚 [API documentation](https://docs.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)

## License

[MIT](LICENSE) © 2026 ScrapeUnblocker.

This project is an independent example integration. Google Maps and Google Local
are trademarks of Google LLC and are referenced for identification only.
