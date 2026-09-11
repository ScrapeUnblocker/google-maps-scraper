"""Core client for the ScrapeUnblocker Google Local plugin.

Wraps the public search endpoint::

    POST /maps/google-local   -> Google Maps / Local business listings for a keyword

All network access goes through ScrapeUnblocker; nothing here talks to Google
directly. The client is deliberately dependency-light (only ``requests``) and
injectable, so the test suite runs fully offline.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

from .models import Place, dedupe_places, normalize_item

DEFAULT_BASE_URL = "https://api.scrapeunblocker.com"
_SEARCH_PATH = "/maps/google-local"

# Product / docs links (UTM-tagged so referrals are attributable).
PRODUCT_URL = (
    "https://scrapeunblocker.com/?utm_source=github"
    "&utm_medium=integration&utm_campaign=example-repos"
)
DOCS_URL = (
    "https://docs.scrapeunblocker.com/?utm_source=github"
    "&utm_medium=integration&utm_campaign=example-repos"
)


class GoogleLocalError(RuntimeError):
    """Raised on a non-2xx API response or an exhausted retry budget."""

    def __init__(self, message: str, *, status: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


class GoogleMapsScraper:
    """Search Google Maps / Local business listings via ScrapeUnblocker.

    Parameters
    ----------
    api_key:
        ScrapeUnblocker API key. If omitted, ``SCRAPEUNBLOCKER_KEY`` is read from
        the environment.
    base_url:
        API base URL (override only for testing / self-hosting).
    timeout:
        Per-request timeout in seconds. Google Maps rendering can be slow, so the
        default is generous.
    max_retries:
        Extra attempts on a transient error (5xx / network / timeout) before
        giving up. ``4xx`` responses are surfaced immediately.
    retry_backoff:
        Base seconds for exponential backoff between retries.
    session:
        A pre-built ``requests.Session`` (mainly for testing). When given,
        ``api_key`` is still used for the auth header.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 90.0,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("SCRAPEUNBLOCKER_KEY", "")
        if not self.api_key:
            raise GoogleLocalError(
                "Missing API key. Set SCRAPEUNBLOCKER_KEY or pass api_key=...",
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session = session or requests.Session()
        self._sleep = time.sleep

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        """POST the search endpoint with ``params``, retrying transient failures.

        The plugin expects its arguments in the query string (an empty request
        body), so ``params`` travels via ``requests``' ``params=`` argument.
        """
        url = self.base_url + _SEARCH_PATH
        headers = {"x-scrapeunblocker-key": self.api_key}
        clean = {k: v for k, v in params.items() if v is not None}

        attempt = 0
        while True:
            try:
                response = self.session.post(
                    url, params=clean, headers=headers, timeout=self.timeout
                )
                if response.status_code >= 500:
                    raise GoogleLocalError(
                        f"Server error {response.status_code}",
                        status=response.status_code,
                        body=response.text[:500],
                    )
                if response.status_code >= 400:
                    # 4xx (auth, bad request, ...) are not retryable.
                    raise GoogleLocalError(
                        f"Request failed with status {response.status_code}",
                        status=response.status_code,
                        body=response.text[:500],
                    )
                return response.json()
            except (GoogleLocalError, requests.RequestException) as exc:
                retryable = isinstance(exc, requests.RequestException) or (
                    isinstance(exc, GoogleLocalError)
                    and exc.status is not None
                    and exc.status >= 500
                )
                attempt += 1
                if not retryable or attempt > self.max_retries:
                    if isinstance(exc, GoogleLocalError):
                        raise
                    raise GoogleLocalError(f"Network error: {exc}") from exc
                self._sleep(self.retry_backoff * (2 ** (attempt - 1)))

    def search(
        self,
        keyword: str,
        *,
        proxy_country: str | None = None,
        gl: str | None = None,
        hl: str | None = None,
        include_sponsored: bool = True,
        limit: int | None = None,
    ) -> list[Place]:
        """Fetch the Google Local pack for ``keyword`` and return typed places.

        Parameters
        ----------
        keyword:
            The search, e.g. ``"coffee shops in chicago"``. Including a location
            in the query is what scopes the results to that area.
        proxy_country:
            Two-letter country for the request's exit location (e.g. ``"US"``).
        gl:
            Google country code (e.g. ``"us"``, ``"uk"``) — biases which market's
            results Google returns.
        hl:
            Interface / results language (e.g. ``"en"``).
        include_sponsored:
            When ``False``, ad / sponsored listings are dropped from the result.
        limit:
            Optionally cap the number of places returned (the plugin returns up to
            roughly 20 per search).
        """
        if not keyword or not keyword.strip():
            raise GoogleLocalError("`keyword` is required.")
        payload = self._request(
            {
                "keyword": keyword.strip(),
                "proxy_country": proxy_country,
                "gl": gl,
                "hl": hl,
            }
        )
        source_keyword = payload.get("keyword") or keyword.strip()
        results = payload.get("results")
        if not isinstance(results, list):
            return []
        places = [
            normalize_item(item, keyword=source_keyword)
            for item in results
            if isinstance(item, dict)
        ]
        if not include_sponsored:
            places = [p for p in places if not p.sponsored]
        if limit is not None:
            places = places[: max(limit, 0)]
        return places

    def search_many(
        self,
        keywords: list[str],
        *,
        proxy_country: str | None = None,
        gl: str | None = None,
        hl: str | None = None,
        include_sponsored: bool = True,
        dedupe: bool = True,
    ) -> list[Place]:
        """Run several searches (e.g. one per city / vertical) and combine them.

        Google's local pack has no pagination, so the way to gather more than one
        pack is to vary the query. This is ideal for lead lists: search the same
        vertical across several cities, or several verticals in one city.

        With ``dedupe=True`` (the default) places that repeat across queries -
        matched on name + address - are collapsed to a single record.
        """
        collected: list[Place] = []
        for keyword in keywords:
            if not keyword or not keyword.strip():
                continue
            collected.extend(
                self.search(
                    keyword,
                    proxy_country=proxy_country,
                    gl=gl,
                    hl=hl,
                    include_sponsored=include_sponsored,
                )
            )
        return dedupe_places(collected) if dedupe else collected
