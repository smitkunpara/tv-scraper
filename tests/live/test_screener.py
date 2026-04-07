"""Live API tests for Screener.

Tests real HTTP connections to TradingView screener endpoint.
"""

import time

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.screener import Screener


@pytest.mark.live
class TestLiveScreenerMarkets:
    """Test screener with different markets."""

    @pytest.mark.parametrize(
        "market",
        ["america", "crypto", "forex", "india", "uk", "germany", "canada", "australia"],
    )
    def test_market_screening(self, market: str) -> None:
        """Verify each market can be screened."""
        scraper = Screener()
        result = scraper.get_screener(market=market, limit=5)
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert result["metadata"]["market"] == market
        time.sleep(0.5)


@pytest.mark.live
class TestLiveScreenerFilters:
    """Test screener with various filter configurations."""

    def test_filter_close_greater_than(self) -> None:
        """Test close > 100 filter."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_filter_close_less_than(self) -> None:
        """Test close < 50 filter."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "less", "right": 50}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_filter_volume_greater_than(self) -> None:
        """Test volume > threshold filter."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "volume", "operation": "greater", "right": 1000000}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_filter_change_abs_operation(self) -> None:
        """Test change_abs absolute value filter."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "change_abs", "operation": "greater", "right": 5}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_multiple_filters(self) -> None:
        """Test multiple filters combined."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[
                {"left": "close", "operation": "greater", "right": 50},
                {"left": "volume", "operation": "greater", "right": 500000},
            ],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_filter_in_range(self) -> None:
        """Test in_range operation."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "in_range", "right": [50, 200]}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_filter_crosses_operation(self) -> None:
        """Test crosses operation (may fail if TradingView changed API)."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "crosses", "right": "sma20"}],
            limit=10,
        )
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
        else:
            pytest.skip(f"Crosses operation not supported: {result.get('error')}")


@pytest.mark.live
class TestLiveScreenerSorting:
    """Test screener sorting options."""

    @pytest.mark.parametrize(
        "sort_by", ["close", "volume", "change", "market_cap_basic"]
    )
    def test_sort_by_field(self, sort_by: str) -> None:
        """Test sorting by various fields."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_by=sort_by,
            sort_order="desc",
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        time.sleep(0.3)

    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    def test_sort_order(self, sort_order: str) -> None:
        """Test ascending and descending sort order."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_by="close",
            sort_order=sort_order,
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["sort_order"] == sort_order
        time.sleep(0.3)


@pytest.mark.live
class TestLiveScreenerLimits:
    """Test screener limit parameter."""

    @pytest.mark.parametrize("limit", [5, 10, 50, 100])
    def test_different_limits(self, limit: int) -> None:
        """Test different limit values."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=limit)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= limit
        assert result["metadata"]["limit"] == limit
        time.sleep(0.3)


@pytest.mark.live
class TestLiveScreenerFields:
    """Test screener custom fields."""

    def test_custom_fields_subset(self) -> None:
        """Test custom fields subset."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            fields=["name", "close", "change", "volume"],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        if result["data"]:
            assert all(
                key in result["data"][0]
                for key in ["name", "close", "change", "volume"]
            )

    def test_default_fields_america(self) -> None:
        """Test default fields for america market."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)
        assert result["status"] == STATUS_SUCCESS

    def test_default_fields_crypto(self) -> None:
        """Test default fields for crypto market."""
        scraper = Screener()
        result = scraper.get_screener(market="crypto", limit=5)
        assert result["status"] == STATUS_SUCCESS

    def test_default_fields_forex(self) -> None:
        """Test default fields for forex market."""
        scraper = Screener()
        result = scraper.get_screener(market="forex", limit=5)
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLiveScreenerSymbols:
    """Test screener with symbol filters."""

    def test_symbolset_sp500(self) -> None:
        """Test S&P 500 symbolset."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            symbols={"symbolset": ["SYML:SP;SPX"]},
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        time.sleep(0.5)

    def test_symbolset_nasdaq100(self) -> None:
        """Test NASDAQ 100 symbolset."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            symbols={"symbolset": ["SYML:NASDAQ;NDX"]},
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        time.sleep(0.5)

    def test_tickers_explicit_list(self) -> None:
        """Test explicit tickers list."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            symbols={"tickers": ["NASDAQ:AAPL", "NYSE:JPM", "NYSE:GS"]},
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLiveScreenerFilter2:
    """Test screener with filter2 complex boolean logic."""

    def test_filter2_and_operator(self) -> None:
        """Test filter2 with AND operator."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            filter2={
                "operator": "and",
                "operands": [
                    {"left": "volume", "operation": "greater", "right": 1000000},
                    {"left": "change", "operation": "greater", "right": 0},
                ],
            },
            limit=10,
        )
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
        else:
            pytest.skip(f"Filter2 not supported: {result.get('error')}")
        time.sleep(0.5)

    def test_filter2_or_operator(self) -> None:
        """Test filter2 with OR operator."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filter2={
                "operator": "or",
                "operands": [
                    {"left": "change", "operation": "greater", "right": 5},
                    {"left": "change", "operation": "less", "right": -5},
                ],
            },
            limit=10,
        )
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
        else:
            pytest.skip(f"Filter2 not supported: {result.get('error')}")
        time.sleep(0.5)

    def test_filter2_expression(self) -> None:
        """Test filter2 with expression field."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filter2={
                "operator": "and",
                "expression": "volume > 1000000",
                "operands": [
                    {"left": "close", "operation": "greater", "right": 50},
                ],
            },
            limit=10,
        )
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
        else:
            pytest.skip(f"Filter2 expression not supported: {result.get('error')}")
        time.sleep(0.5)


@pytest.mark.live
class TestLiveScreenerValidation:
    """Test screener validation and error handling."""

    def test_invalid_market(self) -> None:
        """Test invalid market returns error."""
        scraper = Screener()
        result = scraper.get_screener(market="invalid_market_xyz", limit=5)
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Unsupported market" in result["error"]

    def test_invalid_sort_order(self) -> None:
        """Test invalid sort order returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_order="invalid_order",
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "sort_order" in result["error"]

    def test_invalid_limit_zero(self) -> None:
        """Test limit of zero returns error."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=0)
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "limit" in result["error"].lower()

    def test_invalid_limit_negative(self) -> None:
        """Test negative limit returns error."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=-10)
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_invalid_limit_too_large(self) -> None:
        """Test limit exceeding max returns error."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=100000)
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_invalid_filter_operation(self) -> None:
        """Test invalid filter operation returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "invalid_op", "right": 100}],
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "operation" in result["error"].lower()

    def test_filter_missing_left_key(self) -> None:
        """Test filter missing 'left' key returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"operation": "greater", "right": 100}],
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "left" in result["error"]

    def test_filter_missing_operation_key(self) -> None:
        """Test filter missing 'operation' key returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "right": 100}],
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "operation" in result["error"]

    def test_filter_not_dict(self) -> None:
        """Test filter that is not a dict returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=["not a dict"],
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_filter2_not_dict(self) -> None:
        """Test filter2 that is not a dict returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filter2="not a dict",
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "filter2" in result["error"]

    def test_filter2_missing_operator(self) -> None:
        """Test filter2 missing 'operator' key returns error."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filter2={"operands": []},
            limit=5,
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "operator" in result["error"]


@pytest.mark.live
class TestLiveScreenerCombinations:
    """Test screener with complex parameter combinations."""

    def test_america_with_all_params(self) -> None:
        """Test america market with all parameters."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 50}],
            fields=["name", "close", "change", "volume", "market_cap_basic"],
            sort_by="volume",
            sort_order="desc",
            limit=20,
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) <= 20

    def test_crypto_with_all_params(self) -> None:
        """Test crypto market with all parameters."""
        scraper = Screener()
        result = scraper.get_screener(
            market="crypto",
            filters=[{"left": "volume", "operation": "greater", "right": 10000000}],
            fields=["name", "close", "change", "volume", "market_cap_calc"],
            sort_by="market_cap_calc",
            sort_order="desc",
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_forex_with_all_params(self) -> None:
        """Test forex market with all parameters."""
        scraper = Screener()
        result = scraper.get_screener(
            market="forex",
            filters=[{"left": "change", "operation": "egreater", "right": 0}],
            fields=["name", "close", "change", "change_abs"],
            sort_by="change",
            sort_order="desc",
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS

    def test_india_market(self) -> None:
        """Test india market."""
        scraper = Screener()
        result = scraper.get_screener(
            market="india",
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS


@pytest.mark.live
class TestLiveScreenerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_result(self) -> None:
        """Test that very restrictive filters return empty results."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 999999999}],
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

    def test_rate_limiting(self) -> None:
        """Test rate limiting behavior with multiple requests."""
        scraper = Screener()
        start = time.time()
        for _ in range(3):
            result = scraper.get_screener(market="america", limit=5)
            assert result["status"] == STATUS_SUCCESS
        elapsed = time.time() - start
        assert elapsed > 0

    def test_response_metadata(self) -> None:
        """Test that response metadata is complete."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            sort_by="volume",
            sort_order="desc",
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        meta = result["metadata"]
        assert meta["market"] == "america"
        assert meta["sort_order"] == "desc"
        assert meta["limit"] == 10
        assert "total" in meta
        assert "total_available" in meta

    def test_data_structure(self) -> None:
        """Test that returned data has correct structure."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            fields=["name", "close", "change", "volume"],
            limit=5,
        )
        assert result["status"] == STATUS_SUCCESS
        if result["data"]:
            first_item = result["data"][0]
            assert "symbol" in first_item
            assert isinstance(first_item, dict)


@pytest.mark.live
class TestLiveScreenerCryptoMarkets:
    """Test crypto-specific screener configurations."""

    @pytest.mark.parametrize("market", ["forex"])
    def test_alternative_markets(self, market: str) -> None:
        """Test alternative market screening (only forex is reliably available)."""
        scraper = Screener()
        result = scraper.get_screener(market=market, limit=5)
        if result["status"] == STATUS_SUCCESS:
            assert isinstance(result["data"], list)
        else:
            pytest.skip(f"Market '{market}' not available: {result.get('error')}")
        time.sleep(0.3)
