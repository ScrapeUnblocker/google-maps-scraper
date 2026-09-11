"""Data model and (de)serialization helpers for google-maps-scraper.

The Google Local plugin returns one JSON object per business. :func:`normalize_item`
maps that raw object onto a flat, typed :class:`Place`; :func:`places_to_csv`
renders a stable column subset. Nothing here touches the network.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Place:
    """A single Google Maps / Local business, normalized to flat, typed fields.

    Field availability varies by vertical and by what Google renders in the local
    pack for a given query: service businesses often expose ``phone`` and
    ``hours``, while ``website`` is rarely surfaced in search results and
    ``price`` only appears for places that carry a price level. Missing values are
    ``None`` - never guessed.
    """

    position: int | None = None
    name: str | None = None
    rating: float | None = None
    reviews: int | None = None
    price: str | None = None
    category: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    hours: str | None = None
    review_snippet: str | None = None
    sponsored: bool = False
    keyword: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return the place as a plain, JSON-serializable dict."""
        return asdict(self)


def parse_float(value: Any) -> float | None:
    """Coerce a rating into a ``float``, tolerating strings like ``"4,6"``.

    Returns ``None`` when no numeric value can be recovered.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", ".")
        digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
        if not digits or digits == ".":
            return None
        try:
            return float(digits)
        except ValueError:
            return None
    return None


def parse_int(value: Any) -> int | None:
    """Coerce a review count into an ``int``, tolerating ``"2,200"`` / ``"1.2K"``.

    Plain thousands separators are stripped; a trailing ``k``/``m`` multiplier is
    honored so ``"1.2K"`` becomes ``1200``. Returns ``None`` on junk.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip().lower().replace(",", "")
        if not text:
            return None
        multiplier = 1
        if text.endswith("k"):
            multiplier, text = 1_000, text[:-1]
        elif text.endswith("m"):
            multiplier, text = 1_000_000, text[:-1]
        try:
            return int(round(float(text) * multiplier))
        except ValueError:
            digits = "".join(ch for ch in text if ch.isdigit())
            return int(digits) if digits else None
    return None


# Raw keys we lift onto typed fields; anything else is preserved under ``extra``.
_KNOWN_FIELDS = {
    "position",
    "name",
    "rating",
    "reviews",
    "price",
    "category",
    "address",
    "phone",
    "website",
    "hours",
    "review_snippet",
    "sponsored",
}


def normalize_item(item: dict[str, Any], *, keyword: str | None = None) -> Place:
    """Map one raw plugin item onto a :class:`Place`.

    Unknown keys are retained under :attr:`Place.extra` so forward-compatible
    fields are never silently dropped.
    """
    extra = {k: v for k, v in item.items() if k not in _KNOWN_FIELDS}
    return Place(
        position=parse_int(item.get("position")),
        name=item.get("name"),
        rating=parse_float(item.get("rating")),
        reviews=parse_int(item.get("reviews")),
        price=item.get("price"),
        category=item.get("category"),
        address=item.get("address"),
        phone=item.get("phone"),
        website=item.get("website"),
        hours=item.get("hours"),
        review_snippet=item.get("review_snippet"),
        sponsored=bool(item.get("sponsored", False)),
        keyword=keyword,
        extra=extra,
    )


def _dedupe_key(place: Place) -> tuple[str, str]:
    name = (place.name or "").strip().lower()
    address = (place.address or "").strip().lower()
    return (name, address)


def dedupe_places(places: Iterable[Place]) -> list[Place]:
    """Collapse duplicate places (same name + address), preserving first-seen order."""
    seen: set[tuple[str, str]] = set()
    unique: list[Place] = []
    for place in places:
        key = _dedupe_key(place)
        if key in seen:
            continue
        seen.add(key)
        unique.append(place)
    return unique


_CSV_COLUMNS = [
    "keyword",
    "position",
    "name",
    "rating",
    "reviews",
    "price",
    "category",
    "address",
    "phone",
    "website",
    "hours",
    "sponsored",
    "review_snippet",
]


def places_to_csv(places: Iterable[Place]) -> str:
    """Serialize places to a CSV string with a stable, flat column subset."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for place in places:
        writer.writerow({col: place.as_dict().get(col) for col in _CSV_COLUMNS})
    return buffer.getvalue()
