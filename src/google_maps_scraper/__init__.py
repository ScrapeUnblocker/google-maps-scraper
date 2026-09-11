"""google-maps-scraper: scrape Google Maps / Local business listings as clean JSON.

A small, typed Python client for the `ScrapeUnblocker <https://scrapeunblocker.com>`_
Google Local plugin. Search any keyword + market and get back normalized business
records - name, rating, review count, category, address, phone, website, price
level, hours and a sponsored flag - with country targeting, multi-query lead
collection and CSV export.

Basic usage::

    from google_maps_scraper import GoogleMapsScraper

    scraper = GoogleMapsScraper()  # reads SCRAPEUNBLOCKER_KEY from the environment
    for place in scraper.search("coffee shops in chicago", proxy_country="US"):
        print(place.name, place.rating, place.reviews, place.address)
"""

from __future__ import annotations

from .models import (
    Place,
    dedupe_places,
    normalize_item,
    parse_float,
    parse_int,
    places_to_csv,
)
from .scraper import GoogleLocalError, GoogleMapsScraper

__all__ = [
    "GoogleMapsScraper",
    "GoogleLocalError",
    "Place",
    "normalize_item",
    "dedupe_places",
    "places_to_csv",
    "parse_float",
    "parse_int",
]

__version__ = "0.1.0"
