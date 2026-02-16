"""Core module for tv_scraper."""

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import (
    BASE_URL, SCANNER_URL, WEBSOCKET_URL,
    STATUS_SUCCESS, STATUS_FAILED,
    DEFAULT_TIMEOUT, DEFAULT_LIMIT,
)
from tv_scraper.core.exceptions import (
    TvScraperError, ValidationError, DataNotFoundError,
    NetworkError, ExportError,
)
from tv_scraper.core.validators import DataValidator

__all__ = [
    "BaseScraper", "DataValidator",
    "BASE_URL", "SCANNER_URL", "WEBSOCKET_URL",
    "STATUS_SUCCESS", "STATUS_FAILED",
    "DEFAULT_TIMEOUT", "DEFAULT_LIMIT",
    "TvScraperError", "ValidationError", "DataNotFoundError",
    "NetworkError", "ExportError",
]
