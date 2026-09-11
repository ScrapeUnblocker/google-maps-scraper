"""Search Google Maps for a keyword and print the places as JSON.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/search_to_json.py
"""

from __future__ import annotations

import json

from google_maps_scraper import GoogleMapsScraper


def main() -> None:
    scraper = GoogleMapsScraper()
    places = scraper.search("coffee shops in chicago", proxy_country="US")

    print(json.dumps([p.as_dict() for p in places], indent=2, ensure_ascii=False))
    print(f"\n{len(places)} places found.")


if __name__ == "__main__":
    main()
