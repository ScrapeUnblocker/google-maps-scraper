"""Search Google Maps and write the places to a CSV file.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/export_csv.py
"""

from __future__ import annotations

from pathlib import Path

from google_maps_scraper import GoogleMapsScraper, places_to_csv


def main() -> None:
    scraper = GoogleMapsScraper()
    places = scraper.search("plumbers in austin tx", proxy_country="US")

    out = Path("austin_plumbers.csv")
    out.write_text(places_to_csv(places), encoding="utf-8")
    print(f"Wrote {len(places)} places to {out}")


if __name__ == "__main__":
    main()
