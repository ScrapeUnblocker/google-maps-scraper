"""Unit tests for the CLI argument parser and dispatch (no network)."""

from __future__ import annotations

import json

import pytest
from conftest import make_item

from google_maps_scraper import cli
from google_maps_scraper.models import normalize_item


def test_parser_defaults():
    args = cli.build_parser().parse_args(["coffee in chicago"])
    assert args.keyword == "coffee in chicago"
    assert args.proxy_country is None
    assert args.gl is None
    assert args.hl is None
    assert args.no_sponsored is False
    assert args.limit is None
    assert args.format == "json"
    assert args.output is None


def test_parser_accepts_all_options():
    args = cli.build_parser().parse_args(
        [
            "dentists in london",
            "-c",
            "GB",
            "--gl",
            "uk",
            "--hl",
            "en",
            "--no-sponsored",
            "-l",
            "10",
            "-f",
            "csv",
            "-o",
            "leads.csv",
        ]
    )
    assert args.proxy_country == "GB"
    assert args.gl == "uk"
    assert args.hl == "en"
    assert args.no_sponsored is True
    assert args.limit == 10
    assert args.format == "csv"
    assert args.output == "leads.csv"


def test_parser_rejects_unknown_format():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["kw", "-f", "xml"])


def test_main_prints_json(monkeypatch, capsysbinary):
    sample = [normalize_item(make_item())]
    monkeypatch.setattr(cli.GoogleMapsScraper, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(cli.GoogleMapsScraper, "search", lambda self, *a, **k: sample)

    exit_code = cli.main(["coffee in chicago"])
    assert exit_code == 0
    out = capsysbinary.readouterr().out.decode("utf-8")
    data = json.loads(out)
    assert data[0]["name"] == "Sawada Coffee"


def test_main_writes_output_file(monkeypatch, tmp_path):
    sample = [normalize_item(make_item())]
    monkeypatch.setattr(cli.GoogleMapsScraper, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(cli.GoogleMapsScraper, "search", lambda self, *a, **k: sample)

    target = tmp_path / "out.csv"
    exit_code = cli.main(["coffee", "-f", "csv", "-o", str(target)])
    assert exit_code == 0
    assert target.read_text(encoding="utf-8").startswith("keyword,position,name")


def test_main_rejects_bad_limit():
    assert cli.main(["kw", "-l", "0"]) == 2
