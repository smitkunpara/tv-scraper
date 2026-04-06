"""Core exceptions for tv_scraper."""


class TvScraperError(Exception):
    """Base exception for tv_scraper."""


class ValidationError(TvScraperError):
    """Raised for validation failures."""


class DataNotFoundError(TvScraperError):
    """Raised when expected data is not found."""


class ExportError(TvScraperError):
    """Raised for export failures."""


class NetworkError(TvScraperError):
    """Raised for HTTP/network failures."""


class CaptchaError(TvScraperError):
    """Raised when TradingView returns a captcha challenge."""
