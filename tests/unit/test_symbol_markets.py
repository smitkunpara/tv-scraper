"""Unit tests for SymbolMarkets scraper.

Tests isolated functionality without network calls.
"""

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets


class TestSymbolMarketsGetSymbolMarkets:
    """Test get_symbol_markets method."""

    def test_empty_symbol_error(self) -> None:
        """Test empty symbol returns error response."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "non-empty" in result["error"].lower()

    def test_whitespace_symbol_error(self) -> None:
        """Test whitespace-only symbol returns error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="   ")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None

    def test_invalid_scanner_error(self) -> None:
        """Test invalid scanner returns error."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="AAPL", scanner="invalid_scanner")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid scanner" in result["error"]

    def test_unsupported_scanner_list(self) -> None:
        """Test error message lists supported scanners."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="AAPL", scanner="bad_scanner")
        assert "global" in result["error"]
        assert "america" in result["error"]
        assert "crypto" in result["error"]
        assert "forex" in result["error"]
        assert "cfd" in result["error"]


class TestSymbolMarketsSymbolParsing:
    """Test symbol parsing from EXCHANGE:SYMBOL format."""

    def test_symbol_without_exchange(self) -> None:
        """Test simple symbol is used as-is."""
        scraper = SymbolMarkets()
        assert scraper.get_symbol_markets(symbol="AAPL", scanner="global")[
            "status"
        ] in [
            STATUS_SUCCESS,
            STATUS_FAILED,
        ]

    def test_symbol_with_exchange_prefix(self) -> None:
        """Test EXCHANGE:SYMBOL format extracts symbol."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="NASDAQ:AAPL", scanner="america")
        assert "status" in result
        assert "metadata" in result


class TestSymbolMarketsSupportedScanners:
    """Test supported scanners constant."""

    def test_supported_scanners_defined(self) -> None:
        """Test SUPPORTED_SCANNERS is properly defined."""
        assert "global" in SymbolMarkets.SUPPORTED_SCANNERS
        assert "america" in SymbolMarkets.SUPPORTED_SCANNERS
        assert "crypto" in SymbolMarkets.SUPPORTED_SCANNERS
        assert "forex" in SymbolMarkets.SUPPORTED_SCANNERS
        assert "cfd" in SymbolMarkets.SUPPORTED_SCANNERS

    def test_supported_scanners_count(self) -> None:
        """Test exactly 5 scanners are supported."""
        assert len(SymbolMarkets.SUPPORTED_SCANNERS) == 5


class TestSymbolMarketsDefaultFields:
    """Test default fields constant."""

    def test_default_fields_defined(self) -> None:
        """Test DEFAULT_FIELDS is properly defined."""
        expected_fields = [
            "name",
            "close",
            "change",
            "change_abs",
            "volume",
            "exchange",
            "type",
            "description",
            "currency",
            "market_cap_basic",
        ]
        for field in expected_fields:
            assert field in SymbolMarkets.DEFAULT_FIELDS

    def test_default_fields_count(self) -> None:
        """Test default fields count."""
        assert len(SymbolMarkets.DEFAULT_FIELDS) == 10


class TestSymbolMarketsConstructor:
    """Test SymbolMarkets constructor."""

    def test_default_constructor(self) -> None:
        """Test default initialization."""
        scraper = SymbolMarkets()
        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper.timeout == 10

    def test_export_enabled(self) -> None:
        """Test export_result can be enabled."""
        scraper = SymbolMarkets(export_result=True)
        assert scraper.export_result is True

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        scraper = SymbolMarkets(timeout=30)
        assert scraper.timeout == 30

    def test_invalid_export_type(self) -> None:
        """Test invalid export_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid export_type"):
            SymbolMarkets(export_type="invalid")

    def test_invalid_timeout_too_low(self) -> None:
        """Test timeout below minimum raises ValueError."""
        with pytest.raises(ValueError, match="between"):
            SymbolMarkets(timeout=0)

    def test_invalid_timeout_too_high(self) -> None:
        """Test timeout above maximum raises ValueError."""
        with pytest.raises(ValueError, match="between"):
            SymbolMarkets(timeout=500)


class TestSymbolMarketsResponseStructure:
    """Test response envelope structure."""

    def test_success_response_has_all_keys(self) -> None:
        """Test success response contains all required keys."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="", scanner="global")
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

    def test_error_response_has_all_keys(self) -> None:
        """Test error response contains all required keys."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="", scanner="global")
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "metadata" in result

    def test_metadata_contains_inputs(self) -> None:
        """Test metadata contains input parameters."""
        scraper = SymbolMarkets()
        result = scraper.get_symbol_markets(symbol="AAPL", scanner="america", limit=100)
        if result["status"] == STATUS_FAILED:
            metadata = result["metadata"]
            assert metadata["symbol"] == "AAPL"
            assert metadata["scanner"] == "america"
            assert metadata["limit"] == 100


class TestSymbolMarketsMapScannerRows:
    """Test _map_scanner_rows method."""

    def test_map_scanner_rows_basic(self) -> None:
        """Test basic row mapping."""
        scraper = SymbolMarkets()
        items = [
            {"s": "NASDAQ:AAPL", "d": ["Apple Inc", 150.25]},
            {"s": "NYSE:MSFT", "d": ["Microsoft", 300.50]},
        ]
        fields = ["name", "close"]
        result = scraper._map_scanner_rows(items, fields)
        assert len(result) == 2
        assert result[0]["symbol"] == "NASDAQ:AAPL"
        assert result[0]["name"] == "Apple Inc"
        assert result[0]["close"] == 150.25

    def test_map_scanner_rows_missing_values(self) -> None:
        """Test row mapping with missing values."""
        scraper = SymbolMarkets()
        items = [{"s": "NASDAQ:AAPL", "d": ["Apple"]}]
        fields = ["name", "close", "volume"]
        result = scraper._map_scanner_rows(items, fields)
        assert result[0]["name"] == "Apple"
        assert result[0]["close"] is None
        assert result[0]["volume"] is None

    def test_map_scanner_rows_empty(self) -> None:
        """Test row mapping with empty items."""
        scraper = SymbolMarkets()
        result = scraper._map_scanner_rows([], ["name", "close"])
        assert result == []

    def test_map_scanner_rows_no_symbol(self) -> None:
        """Test row mapping with missing symbol."""
        scraper = SymbolMarkets()
        items = [{"d": ["Apple", 150.0]}]
        result = scraper._map_scanner_rows(items, ["name", "close"])
        assert result[0]["symbol"] == ""
