"""Unit tests for the normalization / serialization helpers."""

from __future__ import annotations

from conftest import make_item

from google_maps_scraper import (
    dedupe_places,
    normalize_item,
    parse_float,
    parse_int,
    places_to_csv,
)


def test_normalize_maps_all_known_fields():
    place = normalize_item(make_item(), keyword="coffee shops in chicago")
    assert place.position == 1
    assert place.name == "Sawada Coffee"
    assert place.rating == 4.6
    assert place.reviews == 2200
    assert place.category == "Coffee shop"
    assert place.address == "112 N Green St"
    assert place.sponsored is False
    assert place.keyword == "coffee shops in chicago"


def test_normalize_tolerates_missing_and_null_fields():
    place = normalize_item({"name": "Thing", "rating": None, "reviews": None})
    assert place.name == "Thing"
    assert place.rating is None
    assert place.reviews is None
    assert place.phone is None
    assert place.sponsored is False  # defaults to False when absent


def test_normalize_preserves_unknown_fields_in_extra():
    place = normalize_item(make_item(place_id="abc123", thumbnail="x.jpg"))
    assert place.extra == {"place_id": "abc123", "thumbnail": "x.jpg"}


def test_parse_float_handles_numbers_strings_and_junk():
    assert parse_float(4) == 4.0
    assert parse_float(4.6) == 4.6
    assert parse_float("4,6") == 4.6
    assert parse_float(None) is None
    assert parse_float("") is None
    assert parse_float(True) is None  # bools are not ratings


def test_parse_int_handles_separators_and_multipliers():
    assert parse_int(2200) == 2200
    assert parse_int("2,200") == 2200
    assert parse_int("1.2K") == 1200
    assert parse_int("3M") == 3_000_000
    assert parse_int("") is None
    assert parse_int(None) is None
    assert parse_int(True) is None


def test_dedupe_collapses_same_name_and_address():
    places = [
        normalize_item(make_item(name="A", address="1 St")),
        normalize_item(make_item(name="A", address="1 St")),
        normalize_item(make_item(name="A", address="2 Ave")),  # different address kept
    ]
    unique = dedupe_places(places)
    assert len(unique) == 2


def test_csv_has_header_and_one_row_per_place():
    places = [normalize_item(make_item()), normalize_item(make_item(name="Metric"))]
    csv_text = places_to_csv(places)
    lines = [line for line in csv_text.splitlines() if line]
    assert lines[0].startswith("keyword,position,name,rating,reviews")
    assert len(lines) == 3  # header + 2 rows
