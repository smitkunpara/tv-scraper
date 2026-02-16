"""Import smoke tests for tv_scraper package.

Verifies that all public classes, constants, and exceptions are importable
from top-level and subpackage paths.
"""

import importlib


class TestTopLevelImports:
    """All classes listed in tv_scraper.__all__ should be importable directly."""

    def test_import_technicals(self) -> None:
        from tv_scraper import Technicals
        assert Technicals is not None

    def test_import_overview(self) -> None:
        from tv_scraper import Overview
        assert Overview is not None

    def test_import_fundamentals(self) -> None:
        from tv_scraper import Fundamentals
        assert Fundamentals is not None

    def test_import_markets(self) -> None:
        from tv_scraper import Markets
        assert Markets is not None

    def test_import_ideas(self) -> None:
        from tv_scraper import Ideas
        assert Ideas is not None

    def test_import_minds(self) -> None:
        from tv_scraper import Minds
        assert Minds is not None

    def test_import_news(self) -> None:
        from tv_scraper import News
        assert News is not None

    def test_import_screener(self) -> None:
        from tv_scraper import Screener
        assert Screener is not None

    def test_import_market_movers(self) -> None:
        from tv_scraper import MarketMovers
        assert MarketMovers is not None

    def test_import_symbol_markets(self) -> None:
        from tv_scraper import SymbolMarkets
        assert SymbolMarkets is not None

    def test_import_calendar(self) -> None:
        from tv_scraper import Calendar
        assert Calendar is not None

    def test_import_options(self) -> None:
        from tv_scraper import Options
        assert Options is not None

    def test_import_streamer(self) -> None:
        from tv_scraper import Streamer
        assert Streamer is not None

    def test_import_realtime_data(self) -> None:
        from tv_scraper import RealTimeData
        assert RealTimeData is not None


class TestSubpackageImports:
    """Public classes should also be importable via subpackage paths."""

    def test_import_from_market_data(self) -> None:
        from tv_scraper.scrapers.market_data import Technicals, Overview, Fundamentals, Markets, Options
        assert all(cls is not None for cls in [Technicals, Overview, Fundamentals, Markets, Options])

    def test_import_from_social(self) -> None:
        from tv_scraper.scrapers.social import Ideas, Minds, News
        assert all(cls is not None for cls in [Ideas, Minds, News])

    def test_import_from_screening(self) -> None:
        from tv_scraper.scrapers.screening import Screener, MarketMovers, SymbolMarkets
        assert all(cls is not None for cls in [Screener, MarketMovers, SymbolMarkets])

    def test_import_from_events(self) -> None:
        from tv_scraper.scrapers.events import Calendar
        assert Calendar is not None

    def test_import_from_streaming(self) -> None:
        from tv_scraper.streaming import Streamer, RealTimeData
        assert all(cls is not None for cls in [Streamer, RealTimeData])


class TestCoreImports:
    """Core module exports should be accessible."""

    def test_import_base_scraper(self) -> None:
        from tv_scraper.core import BaseScraper
        assert BaseScraper is not None

    def test_import_data_validator(self) -> None:
        from tv_scraper.core import DataValidator
        assert DataValidator is not None

    def test_import_constants(self) -> None:
        from tv_scraper.core import (
            BASE_URL, SCANNER_URL, WEBSOCKET_URL,
            STATUS_SUCCESS, STATUS_FAILED,
            DEFAULT_TIMEOUT, DEFAULT_LIMIT,
        )
        assert BASE_URL.startswith("https://")
        assert STATUS_SUCCESS == "success"
        assert STATUS_FAILED == "failed"
        assert isinstance(DEFAULT_TIMEOUT, int)
        assert isinstance(DEFAULT_LIMIT, int)

    def test_import_exceptions(self) -> None:
        from tv_scraper.core import (
            TvScraperError, ValidationError, DataNotFoundError,
            NetworkError, ExportError,
        )
        assert issubclass(ValidationError, TvScraperError)
        assert issubclass(DataNotFoundError, TvScraperError)
        assert issubclass(NetworkError, TvScraperError)
        assert issubclass(ExportError, TvScraperError)


class TestVersionAndAll:
    """Version string and __all__ list should be correct."""

    def test_version_is_1_0_0(self) -> None:
        import tv_scraper
        assert tv_scraper.__version__ == "1.0.0"

    def test_all_exports_match(self) -> None:
        """Every name in __all__ must be importable from tv_scraper."""
        import tv_scraper
        for name in tv_scraper.__all__:
            assert hasattr(tv_scraper, name), f"{name} listed in __all__ not found in tv_scraper"

    def test_all_count(self) -> None:
        """__all__ should have exactly 14 entries."""
        import tv_scraper
        assert len(tv_scraper.__all__) == 14

    def test_module_is_importable(self) -> None:
        """tv_scraper should be importable as a module."""
        mod = importlib.import_module("tv_scraper")
        assert mod is not None
