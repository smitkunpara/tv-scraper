"""Type definitions for tv_scraper."""

from typing import Any, Literal, TypedDict


class ResponseMetadata(TypedDict, total=False):
    """Metadata for scraper responses."""

    symbol: str
    exchange: str
    timestamp: int
    total: int
    total_available: int


class ScraperResponseSuccess(TypedDict):
    """Standardized success response envelope for all scrapers."""

    status: Literal["success"]
    data: Any
    metadata: ResponseMetadata
    error: None


class ScraperResponseFailed(TypedDict):
    """Standardized failure response envelope for all scrapers."""

    status: Literal["failed"]
    data: None
    metadata: ResponseMetadata
    error: str


ScraperResponse = ScraperResponseSuccess | ScraperResponseFailed
