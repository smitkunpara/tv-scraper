"""Integration tests for SymbolMarkets scraper.

Tests cross-module workflows and real-world usage patterns.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals
from tv_scraper.scrapers.market_data.technicals import Technicals
from tv_scraper.scrapers.screening.screener import Screener
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets


@pytest.mark.live
class TestSymbolMarketsIntegration:
    """Integration tests for SymbolMarkets with other modules."""

    def test_integration_symbol_markets_then_technicals(self) -> None:
        """Test fetching symbol markets then getting technicals for found exchange."""
        sm = SymbolMarkets()
        markets = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=10)

        if markets["status"] == STATUS_SUCCESS and markets["data"]:
            tech = Technicals()
            first_market = markets["data"][0]
            exchange = first_market.get("exchange", "")
            if exchange:
                result = tech.get_technicals(
                    exchange=exchange, symbol="AAPL", technical_indicators=["RSI"]
                )
                assert "status" in result

    def test_integration_symbol_markets_then_fundamentals(self) -> None:
        """Test fetching symbol markets then getting fundamentals."""
        sm = SymbolMarkets()
        markets = sm.get_symbol_markets(symbol="AAPL", scanner="america", limit=5)

        if markets["status"] == STATUS_SUCCESS and markets["data"]:
            fund = Fundamentals()
            result = fund.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
            assert "status" in result

    def test_integration_multiple_scanners(self) -> None:
        """Test querying same symbol across multiple scanners."""
        scanners = ["global", "america", "crypto", "forex", "cfd"]
        sm = SymbolMarkets()
        results = {}

        for scanner in scanners:
            symbol = "AAPL" if scanner != "forex" else "EURUSD"
            result = sm.get_symbol_markets(symbol=symbol, scanner=scanner, limit=10)
            results[scanner] = result
            assert "status" in result

        assert len(results) == 5

    def test_integration_different_symbols_same_scanner(self) -> None:
        """Test querying different symbols on same scanner."""
        sm = SymbolMarkets()
        symbols = ["AAPL", "MSFT", "GOOGL"]
        results = {}

        for symbol in symbols:
            result = sm.get_symbol_markets(symbol=symbol, scanner="america", limit=10)
            results[symbol] = result
            assert "status" in result

        assert len(results) == 3

    def test_integration_symbol_markets_with_screener(self) -> None:
        """Test SymbolMarkets combined with Screener module."""
        sm = SymbolMarkets()
        screener = Screener()

        sm.get_symbol_markets(symbol="AAPL", scanner="america", limit=20)

        screener_result = screener.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            limit=10,
        )
        assert "status" in screener_result


@pytest.mark.live
class TestSymbolMarketsWorkflows:
    """Test real-world workflows involving SymbolMarkets."""

    def test_workflow_find_all_exchanges_for_symbol(self) -> None:
        """Test finding all exchanges where a symbol trades."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=150)

        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
            exchanges = {
                item.get("exchange") for item in result["data"] if "exchange" in item
            }
            assert len(exchanges) > 0

    def test_workflow_compare_crypto_across_exchanges(self) -> None:
        """Test comparing crypto symbol across crypto scanner."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="BTCUSD", scanner="crypto", limit=50)

        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)

    def test_workflow_forex_cross_rates(self) -> None:
        """Test forex cross rates search."""
        sm = SymbolMarkets()
        pairs = ["EURUSD", "GBPUSD", "USDJPY"]
        results = []

        for pair in pairs:
            result = sm.get_symbol_markets(symbol=pair, scanner="forex", limit=20)
            results.append(result)

        assert len(results) == 3

    def test_workflow_limit_and_pagination(self) -> None:
        """Test limit parameter effect on results."""
        sm = SymbolMarkets()
        results_50 = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=50)
        results_100 = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=100)
        results_150 = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=150)

        for result in [results_50, results_100, results_150]:
            assert "status" in result

        if (
            results_50["status"] == STATUS_SUCCESS
            and results_100["status"] == STATUS_SUCCESS
        ):
            assert len(results_100["data"]) >= len(results_50["data"])

    def test_workflow_custom_fields_selection(self) -> None:
        """Test using custom fields for specific data needs."""
        sm = SymbolMarkets()
        custom_fields = ["name", "close", "volume", "market_cap_basic"]

        result = sm.get_symbol_markets(
            symbol="AAPL", scanner="america", fields=custom_fields, limit=50
        )

        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
            for item in result["data"]:
                assert "symbol" in item

    def test_workflow_export_and_process(self) -> None:
        """Test workflow with export enabled."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                sm = SymbolMarkets(export="json")
                result = sm.get_symbol_markets(
                    symbol="AAPL", scanner="america", limit=10
                )

                assert "status" in result
            finally:
                os.chdir(original_cwd)


class TestSymbolMarketsDataQuality:
    """Test data quality from SymbolMarkets responses."""

    def test_data_quality_has_required_fields(self) -> None:
        """Test response data has required fields."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=10)

        if result["status"] == STATUS_SUCCESS:
            for item in result["data"]:
                assert "symbol" in item
                assert item["symbol"] != ""

    def test_data_quality_metadata_counts(self) -> None:
        """Test metadata contains accurate counts."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=50)

        if result["status"] == STATUS_SUCCESS:
            metadata = result["metadata"]
            assert "total" in metadata
            assert "total_available" in metadata
            assert metadata["total"] == len(result["data"])
            assert metadata["total_available"] >= metadata["total"]

    def test_data_quality_symbol_format(self) -> None:
        """Test symbol format in results."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=10)

        if result["status"] == STATUS_SUCCESS:
            for item in result["data"]:
                symbol = item.get("symbol", "")
                if symbol:
                    assert ":" in symbol or "/" in symbol


@pytest.mark.live
class TestSymbolMarketsPerformance:
    """Test performance characteristics of SymbolMarkets."""

    def test_performance_multiple_requests(self) -> None:
        """Test making multiple requests doesn't cause issues."""
        import time

        sm = SymbolMarkets()
        start = time.time()

        for _i in range(3):
            result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=20)
            assert "status" in result

        elapsed = time.time() - start
        assert elapsed < 30

    def test_performance_large_limit(self) -> None:
        """Test large limit request completes."""
        sm = SymbolMarkets()
        result = sm.get_symbol_markets(symbol="AAPL", scanner="global", limit=150)
        assert "status" in result
        if result["status"] == STATUS_SUCCESS:
            assert len(result["data"]) <= 150
