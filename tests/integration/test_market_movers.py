"""Integration tests for market movers.

Tests cross-module workflows and integration with other parts of tv_scraper.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.market_movers import MarketMovers


class TestMarketMoversIntegration:
    """Integration tests for market movers with other modules."""

    @pytest.fixture
    def mock_api_response(self) -> dict:
        """Mock API response for all markets."""
        return {
            "data": [
                {
                    "s": "NASDAQ:AAPL",
                    "d": [
                        "Apple Inc.",
                        175.50,
                        2.5,
                        2.52,
                        50000000,
                        2800000000000,
                        28.5,
                        6.15,
                        "logo_123",
                        "Leading tech company",
                    ],
                },
                {
                    "s": "NASDAQ:MSFT",
                    "d": [
                        "Microsoft Corp.",
                        380.00,
                        1.8,
                        1.91,
                        30000000,
                        2800000000000,
                        35.2,
                        10.85,
                        "logo_456",
                        "Software corporation",
                    ],
                },
            ],
            "totalCount": 2,
        }

    def test_workflow_multiple_markets(self, mock_api_response: dict) -> None:
        """Test workflow: scrape multiple markets sequentially."""
        mock_request = MagicMock()
        mock_request.return_value = (mock_api_response, None)

        scraper = MarketMovers()
        markets = ["stocks-usa", "crypto", "forex"]

        with patch.object(scraper, "_request", mock_request):
            results = {}
            for market in markets:
                result = scraper.get_market_movers(market=market, limit=5)
                results[market] = result
                assert result["status"] == STATUS_SUCCESS

        assert len(results) == 3
        assert all(r["status"] == STATUS_SUCCESS for r in results.values())

    def test_workflow_multiple_categories(self, mock_api_response: dict) -> None:
        """Test workflow: scrape multiple categories sequentially."""
        mock_request = MagicMock()
        mock_request.return_value = (mock_api_response, None)

        scraper = MarketMovers()
        categories = ["gainers", "losers", "most-active"]

        with patch.object(scraper, "_request", mock_request):
            results = {}
            for category in categories:
                result = scraper.get_market_movers(
                    market="stocks-usa", category=category, limit=5
                )
                results[category] = result
                assert result["status"] == STATUS_SUCCESS

        assert len(results) == 3

    def test_workflow_pagination_like_behavior(self, mock_api_response: dict) -> None:
        """Test workflow: simulate pagination with different limits."""
        scraper = MarketMovers()

        results_by_limit = {}
        for limit in [10, 50, 100]:
            mock_request = MagicMock()
            mock_request.return_value = (mock_api_response, None)
            with patch.object(scraper, "_request", mock_request):
                result = scraper.get_market_movers(
                    market="stocks-usa", category="gainers", limit=limit
                )
                results_by_limit[limit] = result
                assert result["status"] == STATUS_SUCCESS
                assert result["metadata"]["limit"] == limit

        assert len(results_by_limit) == 3

    def test_workflow_custom_fields_per_market(self) -> None:
        """Test workflow: different fields for different markets."""
        scraper = MarketMovers()

        crypto_response = {
            "data": [{"s": "BINANCE:BTCUSD", "d": ["Bitcoin", 50000, 2.5, 2500]}],
            "totalCount": 1,
        }
        forex_response = {
            "data": [{"s": "FX:EURUSD", "d": ["EUR/USD", 1.10, 0.5, 0.005]}],
            "totalCount": 1,
        }

        mock_request = MagicMock()

        def side_effect(*args, **kwargs):
            payload = kwargs.get("json_payload", {})
            columns = payload.get("columns", [])
            if "market_cap_calc" in columns:
                return (crypto_response, None)
            return (forex_response, None)

        mock_request.side_effect = side_effect

        with patch.object(scraper, "_request", mock_request):
            crypto_result = scraper.get_market_movers(
                market="crypto", category="gainers", limit=5
            )
            assert crypto_result["status"] == STATUS_SUCCESS

            forex_result = scraper.get_market_movers(
                market="forex", category="gainers", limit=5
            )
            assert forex_result["status"] == STATUS_SUCCESS

    def test_workflow_batch_processing(self, mock_api_response: dict) -> None:
        """Test workflow: batch process multiple requests."""
        mock_request = MagicMock()
        mock_request.return_value = (mock_api_response, None)

        scraper = MarketMovers()

        requests = [
            {"market": "stocks-usa", "category": "gainers", "limit": 10},
            {"market": "stocks-usa", "category": "losers", "limit": 10},
            {"market": "crypto", "category": "gainers", "limit": 10},
        ]

        with patch.object(scraper, "_request", mock_request):
            results = [scraper.get_market_movers(**req) for req in requests]

        assert len(results) == 3
        assert all(r["status"] == STATUS_SUCCESS for r in results)

    def test_workflow_aggregate_data(self, mock_api_response: dict) -> None:
        """Test workflow: aggregate data from multiple sources."""
        mock_request = MagicMock()
        mock_request.return_value = (mock_api_response, None)

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            gainers = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )
            losers = scraper.get_market_movers(
                market="stocks-usa", category="losers", limit=10
            )

        all_symbols = set()
        for item in gainers["data"]:
            all_symbols.add(item["symbol"])
        for item in losers["data"]:
            all_symbols.add(item["symbol"])

        assert len(all_symbols) >= 2


class TestMarketMoversWithExport:
    """Integration tests for market movers with export functionality."""

    def test_export_enabled_creates_no_error(self) -> None:
        """Test export enabled doesn't break functionality."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 175.50, 2.5]}],
                "totalCount": 1,
            },
            None,
        )

        scraper = MarketMovers(export_result=True, export_type="json")

        with patch.object(scraper, "_request", mock_request):
            with patch.object(scraper, "_export") as mock_export:
                result = scraper.get_market_movers(
                    market="stocks-usa", category="gainers", limit=10
                )

        assert result["status"] == STATUS_SUCCESS
        mock_export.assert_called_once()

    def test_export_csv_format(self) -> None:
        """Test CSV export format works."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 175.50, 2.5]}],
                "totalCount": 1,
            },
            None,
        )

        scraper = MarketMovers(export_result=True, export_type="csv")

        with patch.object(scraper, "_request", mock_request):
            with patch.object(scraper, "_export") as mock_export:
                result = scraper.get_market_movers(
                    market="stocks-usa", category="gainers", limit=10
                )

        assert result["status"] == STATUS_SUCCESS
        mock_export.assert_called_once()
        call_kwargs = mock_export.call_args[1]
        assert call_kwargs["data_category"] == "market_movers"


class TestMarketMoversValidationIntegration:
    """Integration tests for validation flows."""

    def test_validation_error_preserves_metadata(self) -> None:
        """Test validation errors preserve metadata."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="invalid", category="gainers", limit=10
        )

        assert result["status"] == "failed"
        assert result["metadata"]["market"] == "invalid"
        assert result["metadata"]["category"] == "gainers"
        assert result["metadata"]["limit"] == 10
        assert result["error"] is not None
        assert result["data"] is None

    def test_validation_chain(self) -> None:
        """Test validation chain: market -> category -> limit -> language."""
        scraper = MarketMovers()

        invalid_market = scraper.get_market_movers(
            market="invalid", category="gainers", limit=10
        )
        assert invalid_market["status"] == "failed"
        assert "Invalid market" in invalid_market["error"]

        invalid_category = scraper.get_market_movers(
            market="stocks-usa", category="invalid", limit=10
        )
        assert invalid_category["status"] == "failed"
        assert "Invalid category" in invalid_category["error"]

        invalid_limit = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=0
        )
        assert invalid_limit["status"] == "failed"
        assert "Invalid limit" in invalid_limit["error"]

        invalid_lang = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10, language="invalid"
        )
        assert invalid_lang["status"] == "failed"
        assert "Invalid language" in invalid_lang["error"]


class TestMarketMoversDataMapping:
    """Integration tests for data mapping flows."""

    def test_map_scanner_rows_integration(self) -> None:
        """Test row mapping integrates with get_market_movers."""
        raw_items = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 175.50, 2.5]},
            {"s": "NASDAQ:MSFT", "d": ["Microsoft", 380.00, 1.8]},
        ]
        fields = ["name", "close", "change"]

        scraper = MarketMovers()
        result = scraper._map_scanner_rows(raw_items, fields)

        assert len(result) == 2
        assert result[0]["symbol"] == "NASDAQ:AAPL"
        assert result[0]["name"] == "Apple"
        assert result[0]["close"] == 175.50
        assert result[0]["change"] == 2.5

    def test_payload_builds_correctly(self) -> None:
        """Test payload building integrates correctly."""
        scraper = MarketMovers()
        payload = scraper._build_payload(
            market="stocks-usa",
            category="gainers",
            fields=["name", "close"],
            limit=10,
        )

        assert "columns" in payload
        assert "filter" in payload
        assert "options" in payload
        assert "range" in payload
        assert "sort" in payload

        assert payload["columns"] == ["name", "close"]
        assert payload["range"] == [0, 10]

    def test_filter_conditions_for_different_markets(self) -> None:
        """Test filter conditions work correctly for different markets."""
        scraper = MarketMovers()

        stock_filters = scraper._get_filter_conditions("stocks-usa", "gainers")
        assert len(stock_filters) == 2

        crypto_filters = scraper._get_filter_conditions("crypto", "gainers")
        assert len(crypto_filters) == 1

        forex_filters = scraper._get_filter_conditions("forex", "losers")
        assert len(forex_filters) == 1


class TestMarketMoversErrorHandling:
    """Integration tests for error handling flows."""

    def test_network_error_handling(self) -> None:
        """Test network errors are properly handled."""
        mock_request = MagicMock()
        mock_request.return_value = (None, "Network error: Connection refused")

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == "failed"
        assert "Network error" in result["error"]
        assert result["data"] is None
        assert result["metadata"]["market"] == "stocks-usa"

    def test_invalid_json_handling(self) -> None:
        """Test invalid JSON responses are handled."""
        mock_request = MagicMock()
        mock_request.return_value = (
            None,
            "Failed to parse API response: Expecting value",
        )

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == "failed"
        assert "Failed to parse" in result["error"]

    def test_invalid_response_structure(self) -> None:
        """Test invalid response structure is handled."""
        mock_request = MagicMock()
        mock_request.return_value = (["not", "a", "dict"], None)

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == "failed"
        assert "Invalid response format" in result["error"]

    def test_empty_data_handling(self) -> None:
        """Test empty data is handled correctly."""
        mock_request = MagicMock()
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["metadata"]["total"] == 0


class TestMarketMoversTimeout:
    """Integration tests for timeout handling."""

    def test_timeout_respected(self) -> None:
        """Test timeout is respected in requests."""
        scraper = MarketMovers(timeout=5)
        assert scraper.timeout == 5

        scraper_custom = MarketMovers(timeout=30)
        assert scraper_custom.timeout == 30

    def test_custom_timeout_in_request(self) -> None:
        """Test custom timeout is used in requests."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {"data": [], "totalCount": 0},
            None,
        )

        scraper = MarketMovers(timeout=15)

        with patch.object(scraper, "_request", mock_request):
            scraper.get_market_movers(market="stocks-usa", category="gainers", limit=10)

        assert scraper.timeout == 15


class TestMarketMoversFieldCombinations:
    """Integration tests for different field combinations."""

    def test_all_stock_fields(self) -> None:
        """Test all stock default fields are present."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {
                "data": [
                    {
                        "s": "NASDAQ:AAPL",
                        "d": [
                            "Apple",
                            175.50,
                            2.5,
                            2.52,
                            50000000,
                            2800000000000,
                            28.5,
                            6.15,
                            "logo",
                            "desc",
                        ],
                    }
                ],
                "totalCount": 1,
            },
            None,
        )

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == STATUS_SUCCESS
        item = result["data"][0]
        for field in MarketMovers.DEFAULT_STOCK_FIELDS:
            assert field in item

    def test_minimal_fields(self) -> None:
        """Test minimal custom fields work."""
        mock_request = MagicMock()
        mock_request.return_value = (
            {"data": [{"s": "NASDAQ:AAPL", "d": ["Apple"]}], "totalCount": 1},
            None,
        )

        scraper = MarketMovers()

        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa",
                category="gainers",
                limit=10,
                fields=["name"],
            )

        assert result["status"] == STATUS_SUCCESS
        assert "name" in result["data"][0]
