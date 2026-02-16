"""Core module for tv_scraper."""

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import (
    BASE_URL,
    DEFAULT_LIMIT,
    DEFAULT_TIMEOUT,
    SCANNER_URL,
    STATUS_FAILED,
    STATUS_SUCCESS,
    WEBSOCKET_URL,
)
from tv_scraper.core.exceptions import (
    DataNotFoundError,
    ExportError,
    NetworkError,
    TvScraperError,
    ValidationError,
)
from tv_scraper.core.validators import DataValidator

__all__ = [
    "BASE_URL",
    "DEFAULT_LIMIT",
    "DEFAULT_TIMEOUT",
    "SCANNER_URL",
    "STATUS_FAILED",
    "STATUS_SUCCESS",
    "WEBSOCKET_URL",
    "BaseScraper",
    "DataNotFoundError",
    "DataValidator",
    "ExportError",
    "NetworkError",
    "TvScraperError",
    "ValidationError",
]
