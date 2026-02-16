"""Cross-module integration tests for tv_scraper.

Verifies cross-cutting concerns such as inheritance, response format,
export validation, and singleton consistency — all without network calls.
"""

from unittest.mock import patch

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.scrapers.events.calendar import Calendar
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals
from tv_scraper.scrapers.market_data.markets import Markets
from tv_scraper.scrapers.market_data.overview import Overview
from tv_scraper.scrapers.market_data.technicals import Technicals
from tv_scraper.scrapers.screening.market_movers import MarketMovers
from tv_scraper.scrapers.screening.screener import Screener
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets
from tv_scraper.scrapers.social.ideas import Ideas
from tv_scraper.scrapers.social.minds import Minds
from tv_scraper.scrapers.social.news import News

ALL_SCRAPER_CLASSES = [
    Technicals, Overview, Fundamentals, Markets,
    Ideas, Minds, News,
    Screener, MarketMovers, SymbolMarkets,
    Calendar,
]


class TestScraperInheritance:
    """All scrapers must inherit from BaseScraper."""

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_inherits_base_scraper(self, cls) -> None:
        assert issubclass(cls, BaseScraper), f"{cls.__name__} must inherit BaseScraper"


class TestScraperResponseMethods:
    """All scrapers must provide _success_response and _error_response."""

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_has_success_response(self, cls) -> None:
        instance = cls()
        assert hasattr(instance, "_success_response")
        assert callable(instance._success_response)

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_has_error_response(self, cls) -> None:
        instance = cls()
        assert hasattr(instance, "_error_response")
        assert callable(instance._error_response)


class TestScraperConstructorParams:
    """All scrapers must accept export_result and export_type params."""

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_accepts_export_params(self, cls) -> None:
        instance = cls(export_result=True, export_type="csv")
        assert instance.export_result is True
        assert instance.export_type == "csv"


class TestExportTypeValidation:
    """Invalid export_type must raise ValueError."""

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_invalid_export_type_raises(self, cls) -> None:
        with pytest.raises(ValueError, match="Invalid export_type"):
            cls(export_type="xml")


class TestResponseEnvelopeFormat:
    """Success and error envelopes must have the standard shape."""

    def test_success_envelope_shape(self) -> None:
        scraper = Technicals()
        resp = scraper._success_response({"RSI": 65}, symbol="AAPL")
        assert resp["status"] == STATUS_SUCCESS
        assert resp["data"] == {"RSI": 65}
        assert resp["metadata"]["symbol"] == "AAPL"
        assert resp["error"] is None

    def test_error_envelope_shape(self) -> None:
        scraper = Technicals()
        resp = scraper._error_response("something went wrong", symbol="AAPL")
        assert resp["status"] == STATUS_FAILED
        assert resp["data"] is None
        assert resp["metadata"]["symbol"] == "AAPL"
        assert resp["error"] == "something went wrong"


class TestDataValidatorSingleton:
    """DataValidator singleton must be consistent across scraper instances."""

    def test_same_singleton_across_scrapers(self) -> None:
        t = Technicals()
        o = Overview()
        m = Markets()
        # All validators should be the same object
        assert t.validator is o.validator
        assert o.validator is m.validator


class TestMakeRequestAvailable:
    """All scrapers should have _make_request method from BaseScraper."""

    @pytest.mark.parametrize("cls", ALL_SCRAPER_CLASSES, ids=lambda c: c.__name__)
    def test_has_make_request(self, cls) -> None:
        instance = cls()
        assert hasattr(instance, "_make_request")
        assert callable(instance._make_request)
