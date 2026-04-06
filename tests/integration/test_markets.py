"""Integration tests for markets scraper.

Tests cross-module workflows and end-to-end scenarios.
"""

from unittest.mock import patch

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.markets import Markets
from tv_scraper.scrapers.screening.market_movers import MarketMovers


class TestMarketsIntegration:
    """Integration tests for Markets scraper with other modules."""

    def test_markets_and_market_movers_independent(self) -> None:
        """Test Markets and MarketMovers can be used independently."""
        markets_scraper = Markets()
        movers_scraper = MarketMovers()

        markets_mock = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        movers_mock = {
            "data": [{"s": "NASDAQ:MSFT", "d": ["Microsoft", 350.0]}],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_markets:
            with patch.object(MarketMovers, "_request") as mock_movers:
                mock_markets.return_value = (markets_mock, None)
                mock_movers.return_value = (movers_mock, None)

                markets_result = markets_scraper.get_markets(market="america")
                movers_result = movers_scraper.get_market_movers(
                    market="stocks-usa", category="gainers"
                )

                assert markets_result["status"] == STATUS_SUCCESS
                assert movers_result["status"] == STATUS_SUCCESS
                assert markets_result["data"][0]["symbol"] == "NASDAQ:AAPL"
                assert movers_result["data"][0]["symbol"] == "NASDAQ:MSFT"

    def test_markets_multiple_regions_same_session(self) -> None:
        """Test fetching multiple market regions in same session."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "LSE:VOD", "d": ["Vodafone", 100.0]}],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            uk_result = scraper.get_markets(market="uk")
            assert uk_result["status"] == STATUS_SUCCESS
            assert uk_result["metadata"]["market"] == "uk"

            india_result = scraper.get_markets(market="india")
            assert india_result["status"] == STATUS_SUCCESS
            assert india_result["metadata"]["market"] == "india"

    def test_markets_multiple_sort_strategies(self) -> None:
        """Test fetching markets with different sort strategies."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            volume_result = scraper.get_markets(sort_by="volume")
            assert volume_result["status"] == STATUS_SUCCESS
            assert volume_result["metadata"]["sort_by"] == "volume"

            change_result = scraper.get_markets(sort_by="change")
            assert change_result["status"] == STATUS_SUCCESS
            assert change_result["metadata"]["sort_by"] == "change"

            price_result = scraper.get_markets(sort_by="price")
            assert price_result["status"] == STATUS_SUCCESS
            assert price_result["metadata"]["sort_by"] == "price"

    def test_markets_bulk_data_collection(self) -> None:
        """Test collecting bulk data from multiple markets."""
        scraper = Markets()
        mock_data = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
                {"s": "NASDAQ:MSFT", "d": ["Microsoft", 350.0]},
                {"s": "NASDAQ:GOOGL", "d": ["Google", 140.0]},
            ],
            "totalCount": 3,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            markets_to_fetch = ["america", "uk", "germany"]
            results = []

            for market in markets_to_fetch:
                result = scraper.get_markets(market=market, limit=10)
                results.append(result)

            assert len(results) == 3
            for result in results:
                assert result["status"] == STATUS_SUCCESS
                assert len(result["data"]) == 3

    def test_markets_combined_with_export(self) -> None:
        """Test Markets with export functionality."""
        scraper = Markets(export_result=True)
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            with patch.object(Markets, "_export") as mock_export:
                mock_request.return_value = (mock_data, None)
                result = scraper.get_markets(market="america")

                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_called_once()


class TestMarketsWorkflowIntegration:
    """Test complete workflow scenarios."""

    def test_market_analysis_workflow(self) -> None:
        """Test a typical market analysis workflow."""
        scraper = Markets()
        fields = ["name", "close", "change", "volume"]
        mock_data = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 2.5, 1000000]},
                {"s": "NASDAQ:MSFT", "d": ["Microsoft", 350.0, 1.5, 800000]},
                {"s": "NASDAQ:GOOGL", "d": ["Google", 140.0, -0.5, 600000]},
            ],
            "totalCount": 3,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            top_by_volume = scraper.get_markets(
                market="america",
                sort_by="volume",
                sort_order="desc",
                fields=fields,
                limit=10,
            )
            assert top_by_volume["status"] == STATUS_SUCCESS
            assert (
                top_by_volume["data"][0]["volume"]
                >= top_by_volume["data"][-1]["volume"]
            )

            gainers = scraper.get_markets(
                market="america",
                sort_by="change",
                sort_order="desc",
                fields=fields,
                limit=10,
            )
            assert gainers["status"] == STATUS_SUCCESS

            by_market_cap = scraper.get_markets(
                market="america",
                sort_by="market_cap",
                sort_order="desc",
                fields=fields,
                limit=10,
            )
            assert by_market_cap["status"] == STATUS_SUCCESS

    def test_multi_region_comparison(self) -> None:
        """Test comparing stocks across multiple regions."""
        scraper = Markets()
        mock_data = {
            "data": [
                {"s": "LSE:HSBA", "d": ["HSBC", 600.0, 1.0, 500000]},
            ],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            uk_stocks = scraper.get_markets(market="uk", limit=20)
            assert uk_stocks["status"] == STATUS_SUCCESS

            us_stocks = scraper.get_markets(market="america", limit=20)
            assert us_stocks["status"] == STATUS_SUCCESS

            europe_stocks = scraper.get_markets(market="germany", limit=20)
            assert europe_stocks["status"] == STATUS_SUCCESS

    def test_custom_fields_for_analysis(self) -> None:
        """Test using custom fields for specific analysis."""
        scraper = Markets()
        mock_data = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 25.0, 6.5]},
            ],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)

            result = scraper.get_markets(
                market="america",
                fields=[
                    "name",
                    "close",
                    "price_earnings_ttm",
                    "earnings_per_share_basic_ttm",
                ],
                limit=50,
            )

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) == 1
            item = result["data"][0]
            assert "name" in item
            assert "close" in item
            assert "price_earnings_ttm" in item
            assert "earnings_per_share_basic_ttm" in item


class TestMarketsErrorRecovery:
    """Test error recovery and fallback scenarios."""

    def test_partial_failure_handling(self) -> None:
        """Test handling partial failures across multiple requests."""
        scraper = Markets()

        def mock_request_effect(*args, **kwargs):
            payload = kwargs.get("json_payload", {})
            if payload.get("range", [0, 50])[1] == 50:
                return (None, "Network error")
            return (
                {
                    "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
                    "totalCount": 1,
                },
                None,
            )

        with patch.object(Markets, "_request") as mock_request:
            mock_request.side_effect = mock_request_effect

            result1 = scraper.get_markets(limit=50)
            assert result1["status"] == "failed"

            result2 = scraper.get_markets(limit=10)
            assert result2["status"] == STATUS_SUCCESS

    def test_validation_fails_fast(self) -> None:
        """Test that validation errors fail fast without network call."""
        scraper = Markets()

        with patch.object(Markets, "_request") as mock_request:
            result = scraper.get_markets(market="invalid_market")

            assert result["status"] == "failed"
            assert "Unsupported market" in result["error"]
            mock_request.assert_not_called()

    def test_all_markets_fail_validation_independently(self) -> None:
        """Test each invalid market fails independently."""
        scraper = Markets()
        invalid_markets = ["invalid1", "bad_market", "fake_region"]

        for market in invalid_markets:
            result = scraper.get_markets(market=market)
            assert result["status"] == "failed"
            assert market in result["error"]


class TestMarketsDataIntegrity:
    """Test data integrity across workflows."""

    def test_symbol_format_consistency(self) -> None:
        """Test that symbol format is consistent."""
        scraper = Markets()
        mock_data = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
                {"s": "NYSE:IBM", "d": ["IBM", 180.0]},
                {"s": "AMEX:GOLD", "d": ["Gold", 50.0]},
            ],
            "totalCount": 3,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(market="america", limit=10)

            assert result["status"] == STATUS_SUCCESS
            for item in result["data"]:
                assert "symbol" in item
                assert ":" in item["symbol"] or "/" in item["symbol"]

    def test_total_count_accuracy(self) -> None:
        """Test that total_count reflects actual data."""
        scraper = Markets()
        mock_data = {
            "data": [
                {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
                {"s": "NASDAQ:MSFT", "d": ["Microsoft", 350.0]},
            ],
            "totalCount": 100,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(limit=2)

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) == 2
            assert result["metadata"]["total_count"] == 100
            assert result["metadata"]["total"] == 2

    def test_metadata_traceability(self) -> None:
        """Test that metadata provides full traceability."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(
                market="uk",
                sort_by="change",
                sort_order="asc",
                limit=25,
            )

            assert result["status"] == STATUS_SUCCESS
            metadata = result["metadata"]
            assert metadata["market"] == "uk"
            assert metadata["sort_by"] == "change"
            assert metadata["sort_order"] == "asc"
            assert metadata["limit"] == 25
            assert "total" in metadata
            assert "total_count" in metadata
