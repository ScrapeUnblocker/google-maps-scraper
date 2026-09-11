"""Build a de-duplicated lead list for one vertical across several cities.

Google's local pack has no pagination, so the way to gather more businesses is to
vary the query. ``search_many`` runs each query and collapses duplicates by
name + address, giving you one clean list.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/leads_multi_city.py
"""

from __future__ import annotations

from pathlib import Path

from google_maps_scraper import GoogleMapsScraper, places_to_csv

CITIES = ["chicago", "austin tx", "seattle"]


def main() -> None:
    scraper = GoogleMapsScraper()
    queries = [f"digital marketing agencies in {city}" for city in CITIES]

    places = scraper.search_many(queries, proxy_country="US", include_sponsored=False)

    out = Path("marketing_agency_leads.csv")
    out.write_text(places_to_csv(places), encoding="utf-8")
    print(f"Collected {len(places)} unique businesses across {len(CITIES)} cities -> {out}")


if __name__ == "__main__":
    main()
