"""Core module for tv_scraper."""

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import (
    BASE_URL,
    CAPTCHA_MARKER,
    DEFAULT_LIMIT,
    REQUEST_TIMEOUT,
    SCANNER_URL,
    STATUS_FAILED,
    STATUS_SUCCESS,
    WEBSOCKET_URL,
)
from tv_scraper.core.exceptions import (
    CaptchaError,
    DataNotFoundError,
    ExportError,
    NetworkError,
    TvScraperError,
    ValidationError,
)
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validators import DataValidator

__all__ = [
    "BASE_URL",
    "CAPTCHA_MARKER",
    "DEFAULT_LIMIT",
    "REQUEST_TIMEOUT",
    "SCANNER_URL",
    "STATUS_FAILED",
    "STATUS_SUCCESS",
    "WEBSOCKET_URL",
    "BaseScraper",
    "CaptchaError",
    "DataNotFoundError",
    "DataValidator",
    "ExportError",
    "NetworkError",
    "ScannerScraper",
    "TvScraperError",
    "ValidationError",
]
