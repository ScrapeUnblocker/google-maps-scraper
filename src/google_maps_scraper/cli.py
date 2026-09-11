"""Command-line interface for google-maps-scraper.

Examples
--------
    google-maps-scraper "coffee shops in chicago"
    google-maps-scraper "plumbers in austin tx" --country US --format csv -o leads.csv
    google-maps-scraper "dentists in london" --gl uk --hl en --no-sponsored
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import __version__
from .models import places_to_csv
from .scraper import GoogleLocalError, GoogleMapsScraper


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser (kept separate so it is unit-testable)."""
    parser = argparse.ArgumentParser(
        prog="google-maps-scraper",
        description=(
            "Scrape Google Maps / Local business listings as clean JSON via the "
            "ScrapeUnblocker Google Local plugin."
        ),
    )
    parser.add_argument(
        "keyword",
        help="Search term, e.g. 'coffee shops in chicago' (put the location in the query).",
    )
    parser.add_argument(
        "-c",
        "--country",
        dest="proxy_country",
        default=None,
        help="Two-letter proxy exit country, e.g. US, GB.",
    )
    parser.add_argument(
        "--gl",
        default=None,
        help="Google country code, e.g. us, uk.",
    )
    parser.add_argument(
        "--hl",
        default=None,
        help="Results/interface language, e.g. en.",
    )
    parser.add_argument(
        "--no-sponsored",
        action="store_true",
        help="Drop ad / sponsored listings from the results.",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Cap the number of places returned.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (defaults to the SCRAPEUNBLOCKER_KEY environment variable).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _render(places: list, fmt: str) -> str:
    if fmt == "csv":
        return places_to_csv(places)
    return json.dumps([place.as_dict() for place in places], indent=2, ensure_ascii=False)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    if args.limit is not None and args.limit < 1:
        print("error: --limit must be >= 1", file=sys.stderr)
        return 2

    try:
        scraper = GoogleMapsScraper(api_key=args.api_key)
        places = scraper.search(
            args.keyword,
            proxy_country=args.proxy_country,
            gl=args.gl,
            hl=args.hl,
            include_sponsored=not args.no_sponsored,
            limit=args.limit,
        )
    except GoogleLocalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = _render(places, args.format)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(output)
        print(f"Wrote {len(places)} places to {args.output}", file=sys.stderr)
    else:
        # Encode explicitly so non-ASCII names survive a legacy code page (e.g. cp1252).
        sys.stdout.buffer.write((output + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
