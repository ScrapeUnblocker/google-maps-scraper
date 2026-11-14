"""Unit tests for GoogleMapsScraper - fully mocked, no network access."""

from __future__ import annotations

import pytest
import requests
from conftest import FakeResponse, FakeSession, make_item, page

from google_maps_scraper import GoogleLocalError, GoogleMapsScraper


def _scraper(responses, **kwargs):
    session = FakeSession(responses)
    scraper = GoogleMapsScraper(api_key="test-key", session=session, retry_backoff=0, **kwargs)
    scraper._sleep = lambda _seconds: None  # never actually sleep in tests
    return scraper, session


def test_search_returns_normalized_places():
    scraper, session = _scraper(
        [FakeResponse(200, page([make_item(), make_item(name="Metric Coffee", position=2)]))]
    )
    places = scraper.search("coffee shops in chicago", proxy_country="US")
    assert [p.name for p in places] == ["Sawada Coffee", "Metric Coffee"]
    assert places[0].rating == 4.6
    assert places[0].reviews == 2200
    assert places[0].keyword == "coffee shops in chicago"
    # Key travels in the header, query params carry the search fields.
    call = session.calls[0]
    assert call["headers"]["x-scrapeunblocker-key"] == "test-key"
    assert call["params"]["keyword"] == "coffee shops in chicago"
    assert call["params"]["proxy_country"] == "US"


def test_optional_params_omitted_when_none():
    scraper, session = _scraper([FakeResponse(200, page([]))])
    scraper.search("kw")
    params = session.calls[0]["params"]
    assert params == {"keyword": "kw"}  # gl / hl / proxy_country dropped


def test_include_sponsored_false_filters_ads():
    scraper, _ = _scraper(
        [FakeResponse(200, page([make_item(sponsored=True), make_item(name="Real Place")]))]
    )
    places = scraper.search("kw", include_sponsored=False)
    assert [p.name for p in places] == ["Real Place"]


def test_limit_caps_results():
    scraper, _ = _scraper([FakeResponse(200, page([make_item(name=f"P{i}") for i in range(5)]))])
    places = scraper.search("kw", limit=2)
    assert len(places) == 2


def test_search_many_dedupes_across_queries():
    scraper, session = _scraper(
        [
            FakeResponse(200, page([make_item(name="Shared", address="1 St")])),
            FakeResponse(
                200,
                page(
                    [
                        make_item(name="Shared", address="1 St"),  # duplicate
                        make_item(name="Unique", address="2 Ave"),
                    ]
                ),
            ),
        ]
    )
    places = scraper.search_many(["chicago coffee", "austin coffee"])
    assert [p.name for p in places] == ["Shared", "Unique"]
    assert len(session.calls) == 2


def test_search_many_can_keep_duplicates():
    scraper, _ = _scraper(
        [
            FakeResponse(200, page([make_item(name="Shared", address="1 St")])),
            FakeResponse(200, page([make_item(name="Shared", address="1 St")])),
        ]
    )
    places = scraper.search_many(["a", "b"], dedupe=False)
    assert len(places) == 2


def test_search_many_skips_blank_keywords():
    scraper, session = _scraper([FakeResponse(200, page([make_item()]))])
    places = scraper.search_many(["  ", "coffee"])
    assert len(session.calls) == 1  # blank keyword never hit the network
    assert len(places) == 1


def test_retries_on_server_error_then_succeeds():
    scraper, session = _scraper(
        [FakeResponse(503, text="boom"), FakeResponse(200, page([make_item()]))]
    )
    places = scraper.search("kw")
    assert len(places) == 1
    assert len(session.calls) == 2


def test_retries_on_network_error_then_succeeds():
    scraper, session = _scraper(
        [requests.exceptions.ConnectionError("down"), FakeResponse(200, page([make_item()]))]
    )
    assert len(scraper.search("kw")) == 1
    assert len(session.calls) == 2


def test_4xx_is_not_retried():
    scraper, session = _scraper([FakeResponse(401, text="unauthorized")])
    with pytest.raises(GoogleLocalError) as excinfo:
        scraper.search("kw")
    assert excinfo.value.status == 401
    assert len(session.calls) == 1  # no retry on auth failure


def test_gives_up_after_max_retries():
    responses = [FakeResponse(500, text="err")] * 6
    scraper, session = _scraper(responses, max_retries=2)
    with pytest.raises(GoogleLocalError):
        scraper.search("kw")
    assert len(session.calls) == 3  # initial try + 2 retries


def test_empty_keyword_rejected_before_any_request():
    scraper, session = _scraper([])
    with pytest.raises(GoogleLocalError):
        scraper.search("   ")
    assert session.calls == []


def test_missing_results_key_returns_empty_list():
    scraper, _ = _scraper([FakeResponse(200, {"keyword": "kw", "resultsCollected": 0})])
    assert scraper.search("kw") == []


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("SCRAPEUNBLOCKER_KEY", raising=False)
    with pytest.raises(GoogleLocalError):
        GoogleMapsScraper()
