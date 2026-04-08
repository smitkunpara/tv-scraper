"""Unit tests for Screener.

Tests isolated functionality without making real HTTP requests.
Tests internal methods, validation logic, and data transformation.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.scrapers.screening.screener import (
    MAX_LIMIT,
    MIN_LIMIT,
    SORT_ORDERS,
    Screener,
)


class TestScreenerInit:
    """Tests for Screener initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        scraper = Screener()
        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper.timeout == 10

    def test_custom_init(self) -> None:
        """Test custom initialization."""
        scraper = Screener(export_result=True, export_type="csv", timeout=30)
        assert scraper.export_result is True
        assert scraper.export_type == "csv"
        assert scraper.timeout == 30

    def test_supported_markets(self) -> None:
        """Test supported markets list."""
        expected_markets = {
            "america",
            "australia",
            "canada",
            "germany",
            "india",
            "israel",
            "italy",
            "luxembourg",
            "mexico",
            "spain",
            "turkey",
            "uk",
            "crypto",
            "forex",
            "cfd",
            "futures",
            "bonds",
            "global",
        }
        assert Screener.SUPPORTED_MARKETS == expected_markets

    def test_operations(self) -> None:
        """Test supported operations list."""
        expected_operations = frozenset(
            {
                "greater",
                "less",
                "egreater",
                "eless",
                "equal",
                "nequal",
                "in_range",
                "not_in_range",
                "above",
                "below",
                "crosses",
                "crosses_above",
                "crosses_below",
                "has",
                "has_none_of",
            }
        )
        assert Screener.OPERATIONS == expected_operations


class TestInheritance:
    """Test that Screener inherits from ScannerScraper."""

    def test_inherits_from_scanner_scraper(self) -> None:
        """Verify Screener inherits ScannerScraper methods."""
        scraper = Screener()
        assert hasattr(scraper, "_request")
        assert hasattr(scraper, "_success_response")
        assert hasattr(scraper, "_error_response")
        assert hasattr(scraper, "_export")
        assert hasattr(scraper, "_map_scanner_rows")


class TestGetDefaultFields:
    """Test _get_default_fields method."""

    def test_crypto_default_fields(self) -> None:
        """Test default fields for crypto market."""
        scraper = Screener()
        fields = scraper._get_default_fields("crypto")
        assert fields == Screener.DEFAULT_CRYPTO_FIELDS

    def test_forex_default_fields(self) -> None:
        """Test default fields for forex market."""
        scraper = Screener()
        fields = scraper._get_default_fields("forex")
        assert fields == Screener.DEFAULT_FOREX_FIELDS

    def test_stock_default_fields(self) -> None:
        """Test default fields for stock market (america)."""
        scraper = Screener()
        fields = scraper._get_default_fields("america")
        assert fields == Screener.DEFAULT_STOCK_FIELDS

    def test_india_default_fields(self) -> None:
        """Test default fields for india market."""
        scraper = Screener()
        fields = scraper._get_default_fields("india")
        assert fields == Screener.DEFAULT_STOCK_FIELDS


class TestValidateFilter:
    """Test _validate_filter method."""

    def test_valid_filter(self) -> None:
        """Test valid filter passes validation."""
        scraper = Screener()
        filters = [{"left": "close", "operation": "greater", "right": 100}]
        scraper._validate_filter(filters)

    def test_valid_multiple_filters(self) -> None:
        """Test multiple valid filters pass validation."""
        scraper = Screener()
        filters = [
            {"left": "close", "operation": "greater", "right": 50},
            {"left": "volume", "operation": "less", "right": 1000000},
        ]
        scraper._validate_filter(filters)

    def test_all_valid_operations(self) -> None:
        """Test all operations are valid."""
        scraper = Screener()
        for op in Screener.OPERATIONS:
            filters = [{"left": "close", "operation": op, "right": 100}]
            scraper._validate_filter(filters)

    def test_invalid_operation(self) -> None:
        """Test invalid operation fails validation."""
        scraper = Screener()
        filters = [{"left": "close", "operation": "invalid_op", "right": 100}]
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter(filters)
        assert "operation" in str(exc.value).lower()
        assert "invalid_op" in str(exc.value)

    def test_missing_left_key(self) -> None:
        """Test filter missing 'left' key fails validation."""
        scraper = Screener()
        filters = [{"operation": "greater", "right": 100}]
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter(filters)
        assert "left" in str(exc.value)

    def test_missing_operation_key(self) -> None:
        """Test filter missing 'operation' key fails validation."""
        scraper = Screener()
        filters = [{"left": "close", "right": 100}]
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter(filters)
        assert "operation" in str(exc.value)

    def test_filter_not_dict(self) -> None:
        """Test filter that is not a dict fails validation."""
        scraper = Screener()
        filters = ["not a dict"]
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter(filters)
        assert "dictionary" in str(exc.value).lower()

    def test_empty_filters_list(self) -> None:
        """Test empty filters list passes validation."""
        scraper = Screener()
        scraper._validate_filter([])


class TestValidateFilter2:
    """Test _validate_filter2 method."""

    def test_valid_filter2(self) -> None:
        """Test valid filter2 passes validation."""
        scraper = Screener()
        filter2 = {
            "operator": "and",
            "operands": [
                {"left": "volume", "operation": "greater", "right": 1000000},
            ],
        }
        scraper._validate_filter2(filter2)

    def test_filter2_missing_operator(self) -> None:
        """Test filter2 missing 'operator' key fails validation."""
        scraper = Screener()
        filter2 = {"operands": []}
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter2(filter2)
        assert "operator" in str(exc.value)

    def test_filter2_not_dict(self) -> None:
        """Test filter2 that is not a dict fails validation."""
        scraper = Screener()
        with pytest.raises(ValidationError) as exc:
            scraper._validate_filter2("not a dict")
        assert "dictionary" in str(exc.value).lower()


class TestGetScreenerValidation:
    """Test get_screener validation logic."""

    def test_invalid_market(self) -> None:
        """Test invalid market returns error response."""
        scraper = Screener()
        result = scraper.get_screener(market="invalid_market", limit=5)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid market" in result["error"]
        assert result["metadata"]["market"] == "invalid_market"

    def test_invalid_sort_order(self) -> None:
        """Test invalid sort_order returns error response."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_order="invalid",
            limit=5,
        )

        assert result["status"] == STATUS_FAILED
        assert "sort_order" in result["error"].lower()

    @pytest.mark.parametrize("invalid_limit", [0, -1, -100])
    def test_invalid_limit_too_small(self, invalid_limit: int) -> None:
        """Test limit below minimum returns error response."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=invalid_limit)

        assert result["status"] == STATUS_FAILED
        assert "limit" in result["error"].lower()

    def test_invalid_limit_too_large(self) -> None:
        """Test limit above maximum returns error response."""
        scraper = Screener()
        result = scraper.get_screener(market="america", limit=MAX_LIMIT + 1)

        assert result["status"] == STATUS_FAILED
        assert "limit" in result["error"].lower()

    def test_invalid_filter_operation(self) -> None:
        """Test invalid filter operation returns error response."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "invalid", "right": 100}],
            limit=5,
        )

        assert result["status"] == STATUS_FAILED
        assert "operation" in result["error"].lower()

    def test_invalid_filter2(self) -> None:
        """Test invalid filter2 returns error response."""
        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filter2={"operands": []},
            limit=5,
        )

        assert result["status"] == STATUS_FAILED
        assert "operator" in result["error"]


class TestGetScreenerLimits:
    """Test get_screener limit parameter."""

    @pytest.mark.parametrize("limit", [MIN_LIMIT, 5, 10, 50, 100, MAX_LIMIT])
    @patch.object(Screener, "_request")
    def test_valid_limits(self, mock_request: MagicMock, limit: int) -> None:
        """Test valid limit values are accepted."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=limit)

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["limit"] == limit


class TestGetScreenerSortOrder:
    """Test get_screener sort_order parameter."""

    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    @patch.object(Screener, "_request")
    def test_valid_sort_orders(self, mock_request: MagicMock, sort_order: str) -> None:
        """Test valid sort_order values are accepted."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            sort_order=sort_order,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["sort_order"] == sort_order


class TestGetScreenerMarkets:
    """Test get_screener with various markets."""

    @pytest.mark.parametrize("market", list(Screener.SUPPORTED_MARKETS))
    @patch.object(Screener, "_request")
    def test_all_supported_markets(self, mock_request: MagicMock, market: str) -> None:
        """Test all supported markets are accepted."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market=market, limit=5)

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["market"] == market


class TestGetScreenerFields:
    """Test get_screener fields parameter."""

    @patch.object(Screener, "_request")
    def test_custom_fields(self, mock_request: MagicMock) -> None:
        """Test custom fields are passed to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        custom_fields = ["name", "close", "change"]
        result = scraper.get_screener(
            market="america",
            fields=custom_fields,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["columns"] == custom_fields

    @patch.object(Screener, "_request")
    def test_none_fields_uses_default(self, mock_request: MagicMock) -> None:
        """Test None fields uses market-specific defaults."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market="crypto", fields=None, limit=5)

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["columns"] == Screener.DEFAULT_CRYPTO_FIELDS


class TestGetScreenerFilters:
    """Test get_screener filters parameter."""

    @patch.object(Screener, "_request")
    def test_filters_passed_to_request(self, mock_request: MagicMock) -> None:
        """Test filters are passed to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        filters = [{"left": "close", "operation": "greater", "right": 100}]
        result = scraper.get_screener(
            market="america",
            filters=filters,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["filter"] == filters

    @patch.object(Screener, "_request")
    def test_none_filters(self, mock_request: MagicMock) -> None:
        """Test None filters doesn't add filter to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", filters=None, limit=5)

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert "filter" not in payload


class TestGetScreenerSymbols:
    """Test get_screener symbols parameter."""

    @patch.object(Screener, "_request")
    def test_symbols_passed_to_request(self, mock_request: MagicMock) -> None:
        """Test symbols are passed to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        symbols = {"symbolset": ["SYML:SP;SPX"]}
        result = scraper.get_screener(
            market="america",
            symbols=symbols,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["symbols"] == symbols

    @patch.object(Screener, "_request")
    def test_tickers_symbols(self, mock_request: MagicMock) -> None:
        """Test tickers symbols format."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        symbols = {"tickers": ["NASDAQ:AAPL", "NYSE:JPM"]}
        result = scraper.get_screener(
            market="america",
            symbols=symbols,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["symbols"] == symbols


class TestGetScreenerFilter2:
    """Test get_screener filter2 parameter."""

    @patch.object(Screener, "_request")
    def test_filter2_passed_to_request(self, mock_request: MagicMock) -> None:
        """Test filter2 is passed to request."""
        mock_request.return_value = ({"data": [], "totalCount": 0}, None)

        scraper = Screener()
        filter2 = {"operator": "and", "operands": []}
        result = scraper.get_screener(
            market="america",
            filter2=filter2,
            limit=5,
        )

        assert result["status"] == STATUS_SUCCESS
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json_payload", {})
        assert payload["filter2"] == filter2


class TestGetScreenerErrorHandling:
    """Test get_screener error handling."""

    @patch.object(Screener, "_request")
    def test_network_error(self, mock_request: MagicMock) -> None:
        """Test network error returns error response."""
        mock_request.return_value = (None, "Network error: Connection refused")

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] == "Network error: Connection refused"


class TestGetScreenerResponseEnvelope:
    """Test get_screener response envelope structure."""

    @patch.object(Screener, "_request")
    def test_success_has_all_keys(self, mock_request: MagicMock) -> None:
        """Test success response has all required keys."""
        mock_response = {
            "data": [{"symbol": "AAPL", "close": 150.0}],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch.object(Screener, "_request")
    def test_error_has_all_keys(self, mock_request: MagicMock) -> None:
        """Test error response has all required keys."""
        mock_request.return_value = (None, "Test error")

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=5)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] == "Test error"


class TestGetScreenerMetadata:
    """Test get_screener metadata handling."""

    @patch.object(Screener, "_request")
    def test_metadata_contains_all_params(self, mock_request: MagicMock) -> None:
        """Test metadata contains all input parameters."""
        mock_response = {
            "data": [{"symbol": "AAPL", "close": 150.0}],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(
            market="america",
            filters=[{"left": "close", "operation": "greater", "right": 100}],
            sort_by="volume",
            sort_order="desc",
            limit=10,
        )

        meta = result["metadata"]
        assert meta["market"] == "america"
        assert meta["sort_order"] == "desc"
        assert meta["limit"] == 10
        assert meta["sort_by"] == "volume"
        assert meta["total"] == 1
        assert meta["total_available"] == 1

    @patch.object(Screener, "_request")
    def test_total_and_total_available(self, mock_request: MagicMock) -> None:
        """Test total and total_available fields."""
        mock_response = {
            "data": [{"symbol": "AAPL"}, {"symbol": "MSFT"}],
            "totalCount": 100,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener()
        result = scraper.get_screener(market="america", limit=2)

        assert result["metadata"]["total"] == 2
        assert result["metadata"]["total_available"] == 100


class TestGetScreenerExport:
    """Test get_screener export functionality."""

    @patch.object(Screener, "_request")
    @patch.object(Screener, "_export")
    def test_export_called_when_enabled(
        self, mock_export: MagicMock, mock_request: MagicMock
    ) -> None:
        """Test export is called when enabled."""
        mock_response = {
            "data": [{"symbol": "AAPL", "close": 150.0}],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener(export_result=True)
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS
        mock_export.assert_called_once()

    @patch.object(Screener, "_request")
    @patch.object(Screener, "_export")
    def test_export_not_called_when_disabled(
        self, mock_export: MagicMock, mock_request: MagicMock
    ) -> None:
        """Test export is not called when disabled."""
        mock_response = {
            "data": [{"symbol": "AAPL", "close": 150.0}],
            "totalCount": 1,
        }
        mock_request.return_value = (mock_response, None)

        scraper = Screener(export_result=False)
        result = scraper.get_screener(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS
        mock_export.assert_not_called()


class TestConstants:
    """Test Screener constants."""

    def test_sort_orders(self) -> None:
        """Test SORT_ORDERS constant."""
        assert SORT_ORDERS == frozenset({"asc", "desc"})

    def test_min_limit(self) -> None:
        """Test MIN_LIMIT constant."""
        assert MIN_LIMIT == 1

    def test_max_limit(self) -> None:
        """Test MAX_LIMIT constant."""
        assert MAX_LIMIT == 10000
