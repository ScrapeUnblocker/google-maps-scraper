"""Shared offline test doubles - no network, no API credit is ever spent."""

from __future__ import annotations

import json as _json
from typing import Any

import requests


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code: int = 200, payload: Any = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or (_json.dumps(payload) if payload is not None else "")

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    """Records POSTs and replays a scripted sequence of responses/exceptions.

    Each entry in ``responses`` is either a :class:`FakeResponse` or an
    ``Exception`` instance (which is raised to simulate a network failure).
    """

    def __init__(self, responses: list[Any]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, *, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        if not self._responses:
            raise AssertionError("FakeSession ran out of scripted responses")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_item(**overrides: Any) -> dict[str, Any]:
    """A representative raw plugin item, overridable per test."""
    base = {
        "position": 1,
        "name": "Sawada Coffee",
        "rating": 4.6,
        "reviews": 2200,
        "price": "$1–10",
        "category": "Coffee shop",
        "address": "112 N Green St",
        "phone": None,
        "website": None,
        "hours": None,
        "review_snippet": "great chai latte",
        "sponsored": False,
    }
    base.update(overrides)
    return base


def page(results: list[dict[str, Any]], **envelope: Any) -> dict[str, Any]:
    """Wrap items in the plugin's response envelope."""
    payload = {"keyword": "coffee shops in chicago", "proxyCountry": "US"}
    payload.update(envelope)
    payload["results"] = results
    payload["resultsCollected"] = len(results)
    return payload


# Re-export so tests can reference requests exception types if needed.
Timeout = requests.exceptions.Timeout
ConnectionError_ = requests.exceptions.ConnectionError
