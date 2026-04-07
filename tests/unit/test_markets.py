"""Unit tests for markets scraper.

Tests isolated functionality without network calls.
"""

from unittest.mock import patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.markets import Markets


class TestMarketsClass:
    """Test Markets class attributes and initialization."""

    def test_valid_markets_list(self) -> None:
        """Test VALID_MARKETS contains expected markets."""
        expected_markets = [
            "america",
            "australia",
            "canada",
            "germany",
            "india",
            "uk",
            "crypto",
            "forex",
            "global",
        ]
        assert Markets.VALID_MARKETS == expected_markets

    def test_sort_criteria_mapping(self) -> None:
        """Test SORT_CRITERIA contains expected mappings."""
        expected = {
            "market_cap": "market_cap_basic",
            "volume": "volume",
            "change": "change",
            "price": "close",
            "volatility": "Volatility.D",
        }
        assert Markets.SORT_CRITERIA == expected

    def test_default_fields_not_empty(self) -> None:
        """Test DEFAULT_FIELDS contains expected fields."""
        assert len(Markets.DEFAULT_FIELDS) > 0
        assert "name" in Markets.DEFAULT_FIELDS
        assert "close" in Markets.DEFAULT_FIELDS
        assert "change" in Markets.DEFAULT_FIELDS
        assert "volume" in Markets.DEFAULT_FIELDS

    def test_stock_filters_not_empty(self) -> None:
        """Test STOCK_FILTERS contains expected filters."""
        assert len(Markets.STOCK_FILTERS) > 0
        assert any(f["left"] == "type" for f in Markets.STOCK_FILTERS)
        assert any(f["left"] == "market_cap_basic" for f in Markets.STOCK_FILTERS)


class TestMarketsInstantiation:
    """Test Markets class instantiation."""

    def test_default_instantiation(self) -> None:
        """Test default instantiation."""
        scraper = Markets()
        assert scraper is not None
        assert scraper.export_result is False
        assert scraper.export_type == "json"

    def test_instantiation_with_export(self) -> None:
        """Test instantiation with export enabled."""
        scraper = Markets(export_result=True)
        assert scraper.export_result is True

    def test_instantiation_with_csv_export(self) -> None:
        """Test instantiation with CSV export type."""
        scraper = Markets(export_result=True, export_type="csv")
        assert scraper.export_type == "csv"

    def test_instantiation_with_timeout(self) -> None:
        """Test instantiation with custom timeout."""
        scraper = Markets(timeout=30)
        assert scraper.timeout == 30

    def test_instantiation_invalid_export_type(self) -> None:
        """Test instantiation with invalid export type raises error."""
        with pytest.raises(ValueError, match="Invalid export_type"):
            Markets(export_type="xlsx")

    def test_instantiation_invalid_timeout_low(self) -> None:
        """Test instantiation with timeout below minimum raises error."""
        with pytest.raises(ValueError, match="Timeout must be"):
            Markets(timeout=0)

    def test_instantiation_invalid_timeout_high(self) -> None:
        """Test instantiation with timeout above maximum raises error."""
        with pytest.raises(ValueError, match="Timeout must be"):
            Markets(timeout=500)


class TestMarketsValidation:
    """Test parameter validation."""

    def test_invalid_market_error(self) -> None:
        """Test invalid market returns error response."""
        scraper = Markets()
        result = scraper.get_markets(market="invalid_market")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid market" in result["error"]
        assert "invalid_market" in result["error"]

    def test_invalid_sort_by_error(self) -> None:
        """Test invalid sort_by returns error response."""
        scraper = Markets()
        result = scraper.get_markets(sort_by="invalid_criterion")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid sort_by" in result["error"]

    def test_invalid_sort_order_error(self) -> None:
        """Test invalid sort_order returns error response."""
        scraper = Markets()
        result = scraper.get_markets(sort_order="invalid")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid sort_order" in result["error"]

    def test_limit_zero_error(self) -> None:
        """Test limit=0 returns error response."""
        scraper = Markets()
        result = scraper.get_markets(limit=0)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid limit" in result["error"]

    def test_limit_negative_error(self) -> None:
        """Test negative limit returns error response."""
        scraper = Markets()
        result = scraper.get_markets(limit=-1)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None

    def test_limit_too_large_error(self) -> None:
        """Test limit > 1000 returns error response."""
        scraper = Markets()
        result = scraper.get_markets(limit=1001)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None


class TestMarketsAllValidMarkets:
    """Test all valid market values."""

    @pytest.mark.parametrize(
        "market",
        [
            "america",
            "australia",
            "canada",
            "germany",
            "india",
            "uk",
            "crypto",
            "forex",
            "global",
        ],
    )
    def test_valid_market_no_error(self, market: str) -> None:
        """Test each valid market passes validation."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 2.5, 1000000]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(market=market)
            assert result["status"] == STATUS_SUCCESS


class TestMarketsAllSortCriteria:
    """Test all valid sort criteria."""

    @pytest.mark.parametrize(
        "sort_by",
        [
            "market_cap",
            "volume",
            "change",
            "price",
            "volatility",
        ],
    )
    def test_valid_sort_by_no_error(self, sort_by: str) -> None:
        """Test each valid sort criterion passes validation."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 2.5, 1000000]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(sort_by=sort_by)
            assert result["status"] == STATUS_SUCCESS


class TestMarketsSortOrder:
    """Test sort order variations."""

    def test_sort_order_asc(self) -> None:
        """Test ascending sort order passes validation."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(sort_order="asc")
            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["sort_order"] == "asc"

    def test_sort_order_desc(self) -> None:
        """Test descending sort order passes validation."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(sort_order="desc")
            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["sort_order"] == "desc"


class TestMarketsLimitVariations:
    """Test limit value variations."""

    @pytest.mark.parametrize("limit", [1, 10, 50, 100, 500, 1000])
    def test_valid_limits(self, limit: int) -> None:
        """Test various valid limit values."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": limit,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(limit=limit)
            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["limit"] == limit


class TestMarketsFieldsParameter:
    """Test fields parameter handling."""

    def test_none_fields_uses_default(self) -> None:
        """Test fields=None uses DEFAULT_FIELDS."""
        scraper = Markets()
        mock_data = {
            "data": [
                {
                    "s": "NASDAQ:AAPL",
                    "d": [
                        "Apple",
                        150.0,
                        2.5,
                        1000000,
                        0.5,
                        3000000000,
                        25.0,
                        6.5,
                        "Tech",
                        "Electronics",
                    ],
                }
            ],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(fields=None)

            assert result["status"] == STATUS_SUCCESS
            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]
            assert payload["columns"] == Markets.DEFAULT_FIELDS

    def test_custom_fields(self) -> None:
        """Test custom fields parameter."""
        scraper = Markets()
        custom_fields = ["name", "close", "change"]
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 2.5]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(fields=custom_fields)

            assert result["status"] == STATUS_SUCCESS
            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]
            assert payload["columns"] == custom_fields


class TestMarketsResponseMapping:
    """Test scanner row mapping functionality."""

    def test_row_mapping_includes_symbol(self) -> None:
        """Test that mapped rows include symbol field."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(fields=["name", "close"])

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) == 1
            assert result["data"][0]["symbol"] == "NASDAQ:AAPL"

    def test_row_mapping_all_fields(self) -> None:
        """Test that all fields are mapped correctly."""
        scraper = Markets()
        mock_fields = ["name", "close", "change"]
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0, 2.5]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(fields=mock_fields)

            assert result["status"] == STATUS_SUCCESS
            item = result["data"][0]
            assert item["name"] == "Apple"
            assert item["close"] == 150.0
            assert item["change"] == 2.5


class TestMarketsPayloadBuilding:
    """Test API payload construction."""

    def test_payload_structure(self) -> None:
        """Test payload contains required keys."""
        scraper = Markets()
        mock_data = {"data": [], "totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            scraper.get_markets(
                market="america",
                sort_by="market_cap",
                sort_order="desc",
                limit=50,
            )

            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]

            assert "columns" in payload
            assert "options" in payload
            assert "range" in payload
            assert "sort" in payload
            assert "filter" in payload

    def test_payload_sort_config(self) -> None:
        """Test payload sort configuration."""
        scraper = Markets()
        mock_data = {"data": [], "totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            scraper.get_markets(
                market="america",
                sort_by="volume",
                sort_order="asc",
                limit=100,
            )

            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]
            sort = payload["sort"]

            assert sort["sortBy"] == "volume"
            assert sort["sortOrder"] == "asc"

    def test_payload_range(self) -> None:
        """Test payload range matches limit."""
        scraper = Markets()
        mock_data = {"data": [], "totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            scraper.get_markets(limit=75)

            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]

            assert payload["range"] == [0, 75]

    def test_payload_filter(self) -> None:
        """Test payload contains stock filters."""
        scraper = Markets()
        mock_data = {"data": [], "totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            scraper.get_markets()

            call_args = mock_request.call_args
            payload = call_args[1]["json_payload"]

            assert payload["filter"] == Markets.STOCK_FILTERS


class TestMarketsEmptyData:
    """Test empty data handling."""

    def test_empty_data_returns_error(self) -> None:
        """Test empty data array returns error."""
        scraper = Markets()
        mock_data = {"data": [], "totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED
            assert result["data"] is None
            assert "No data found" in result["error"]

    def test_missing_data_key_returns_error(self) -> None:
        """Test missing data key returns error."""
        scraper = Markets()
        mock_data = {"totalCount": 0}
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED


class TestMarketsNetworkErrors:
    """Test network error handling."""

    def test_network_error_returns_failed(self) -> None:
        """Test network error returns failed status."""
        scraper = Markets()
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (None, "Network error: Connection refused")
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED
            assert result["data"] is None
            assert "Network error" in result["error"]

    def test_timeout_error_returns_failed(self) -> None:
        """Test timeout error returns failed status."""
        scraper = Markets()
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (None, "Timeout error")
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED
            assert result["data"] is None


class TestMarketsExport:
    """Test export functionality."""

    def test_export_called_when_enabled(self) -> None:
        """Test _export is called when export_result=True."""
        scraper = Markets(export_result=True)
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            with patch.object(Markets, "_export") as mock_export:
                result = scraper.get_markets()

                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_called_once()
                call_kwargs = mock_export.call_args[1]
                assert call_kwargs["symbol"] == "america_top_stocks"
                assert call_kwargs["data_category"] == "markets"

    def test_export_not_called_when_disabled(self) -> None:
        """Test _export is not called when export_result=False."""
        scraper = Markets(export_result=False)
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            with patch.object(Markets, "_export") as mock_export:
                result = scraper.get_markets()

                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_not_called()


class TestMarketsMetadata:
    """Test metadata in responses."""

    def test_metadata_on_success(self) -> None:
        """Test metadata is present on success."""
        scraper = Markets()
        mock_data = {
            "data": [{"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]}],
            "totalCount": 1,
        }
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = (mock_data, None)
            result = scraper.get_markets(
                market="crypto",
                sort_by="volume",
                sort_order="asc",
                limit=25,
            )

            assert result["status"] == STATUS_SUCCESS
            metadata = result["metadata"]
            assert metadata["market"] == "crypto"
            assert metadata["sort_by"] == "volume"
            assert metadata["sort_order"] == "asc"
            assert metadata["limit"] == 25
            assert metadata["total"] == 1
            assert metadata["total_count"] == 1

    def test_metadata_on_error(self) -> None:
        """Test metadata is present on error (for debugging)."""
        scraper = Markets()
        result = scraper.get_markets(
            market="invalid",
            sort_by="market_cap",
            sort_order="desc",
            limit=50,
        )

        assert result["status"] == STATUS_FAILED
        metadata = result["metadata"]
        assert metadata["market"] == "invalid"
        assert metadata["sort_by"] == "market_cap"
        assert metadata["sort_order"] == "desc"
        assert metadata["limit"] == 50


class TestMarketsErrorMessage:
    """Test error message content."""

    def test_invalid_market_error_message(self) -> None:
        """Test error message for invalid market."""
        scraper = Markets()
        result = scraper.get_markets(market="invalid_market")

        assert result["status"] == STATUS_FAILED
        assert "Invalid market" in result["error"]
        assert "invalid_market" in result["error"]
        for valid in Markets.VALID_MARKETS:
            # Note: validate_choice sorts the allowed values
            assert valid in result["error"]

    def test_invalid_sort_by_error_message(self) -> None:
        """Test error message for invalid sort criterion."""
        scraper = Markets()
        result = scraper.get_markets(sort_by="invalid")

        assert result["status"] == STATUS_FAILED
        assert "Invalid sort_by" in result["error"]
        assert "invalid" in result["error"]
        for valid in Markets.SORT_CRITERIA.keys():
            assert valid in result["error"]

    def test_invalid_limit_error_message(self) -> None:
        """Test error message for invalid limit."""
        scraper = Markets()
        result = scraper.get_markets(limit=0)

        assert result["status"] == STATUS_FAILED
        assert "Invalid limit" in result["error"]
        assert "0" in result["error"]
