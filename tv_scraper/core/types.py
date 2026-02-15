"""Type definitions for tv_scraper."""

from typing import Any, Optional, TypedDict


class ResponseMetadata(TypedDict, total=False):
    """Metadata for scraper responses."""

    symbol: str
    exchange: str
    timestamp: int
    total: int
    total_count: int


class ScraperResponse(TypedDict):
    """Standardized response envelope for all scrapers."""

    status: str  # "success" or "failed"
    data: Any
    metadata: ResponseMetadata
    error: Optional[str]
