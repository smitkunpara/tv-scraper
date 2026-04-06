"""Unit tests for market movers.

Tests isolated functions and methods of the MarketMovers class
without network calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.screening.market_movers import MarketMovers


class TestMarketMoversInit:
    """Test MarketMovers initialization."""

    def test_default_initialization(self) -> None:
        """Test default initialization."""
        scraper = MarketMovers()
        assert scraper.export_result is False
        assert scraper.export_type == "json"
        assert scraper.timeout > 0

    def test_initialization_with_export(self) -> None:
        """Test initialization with export enabled."""
        scraper = MarketMovers(export_result=True, export_type="csv")
        assert scraper.export_result is True
        assert scraper.export_type == "csv"

    def test_supported_markets(self) -> None:
        """Test supported markets list."""
        expected = [
            "stocks-usa",
            "stocks-uk",
            "stocks-india",
            "stocks-australia",
            "stocks-canada",
            "crypto",
            "forex",
            "bonds",
            "futures",
        ]
        assert MarketMovers.SUPPORTED_MARKETS == expected

    def test_stock_categories(self) -> None:
        """Test stock categories list."""
        expected = [
            "gainers",
            "losers",
            "most-active",
            "penny-stocks",
            "pre-market-gainers",
            "pre-market-losers",
            "after-hours-gainers",
            "after-hours-losers",
        ]
        assert MarketMovers.STOCK_CATEGORIES == expected

    def test_non_stock_categories(self) -> None:
        """Test non-stock categories list."""
        expected = ["gainers", "losers", "most-active"]
        assert MarketMovers.NON_STOCK_CATEGORIES == expected


class TestGetScannerUrl:
    """Test scanner URL generation."""

    def test_stocks_usa_maps_to_america(self) -> None:
        """Test stocks-usa maps to america segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("stocks-usa")
        assert "america" in url

    def test_stocks_uk_maps_to_uk(self) -> None:
        """Test stocks-uk maps to uk segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("stocks-uk")
        assert "uk" in url

    def test_stocks_india_maps_to_india(self) -> None:
        """Test stocks-india maps to india segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("stocks-india")
        assert "india" in url

    def test_stocks_australia_maps_to_australia(self) -> None:
        """Test stocks-australia maps to australia segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("stocks-australia")
        assert "australia" in url

    def test_stocks_canada_maps_to_canada(self) -> None:
        """Test stocks-canada maps to canada segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("stocks-canada")
        assert "canada" in url

    def test_crypto_maps_to_crypto(self) -> None:
        """Test crypto maps to crypto segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("crypto")
        assert "crypto" in url

    def test_forex_maps_to_forex(self) -> None:
        """Test forex maps to forex segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("forex")
        assert "forex" in url

    def test_bonds_maps_to_bonds(self) -> None:
        """Test bonds maps to bonds segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("bonds")
        assert "bonds" in url

    def test_futures_maps_to_futures(self) -> None:
        """Test futures maps to futures segment."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("futures")
        assert "futures" in url

    def test_unknown_market_defaults_to_america(self) -> None:
        """Test unknown market defaults to america."""
        scraper = MarketMovers()
        url = scraper._get_scanner_url("unknown")
        assert "america" in url


class TestGetDefaultFields:
    """Test default field selection."""

    def test_stocks_returns_stock_fields(self) -> None:
        """Test stocks-usa returns stock fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("stocks-usa")
        assert fields == MarketMovers.DEFAULT_STOCK_FIELDS

    def test_stocks_uk_returns_stock_fields(self) -> None:
        """Test stocks-uk returns stock fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("stocks-uk")
        assert fields == MarketMovers.DEFAULT_STOCK_FIELDS

    def test_crypto_returns_crypto_fields(self) -> None:
        """Test crypto returns crypto fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("crypto")
        assert fields == MarketMovers.DEFAULT_CRYPTO_FIELDS

    def test_forex_returns_forex_fields(self) -> None:
        """Test forex returns forex fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("forex")
        assert fields == MarketMovers.DEFAULT_FOREX_FIELDS

    def test_bonds_returns_basic_fields(self) -> None:
        """Test bonds returns basic fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("bonds")
        assert fields == MarketMovers.DEFAULT_BASIC_FIELDS

    def test_futures_returns_basic_fields(self) -> None:
        """Test futures returns basic fields."""
        scraper = MarketMovers()
        fields = scraper._get_default_fields("futures")
        assert fields == MarketMovers.DEFAULT_BASIC_FIELDS

    def test_returns_copies_not_references(self) -> None:
        """Test returned lists are copies, not references."""
        scraper = MarketMovers()
        fields1 = scraper._get_default_fields("stocks-usa")
        fields2 = scraper._get_default_fields("stocks-usa")
        fields1.append("new_field")
        assert "new_field" not in fields2


class TestGetSortConfig:
    """Test sort configuration."""

    def test_gainers_sort(self) -> None:
        """Test gainers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("gainers")
        assert config == {"sortBy": "change", "sortOrder": "desc"}

    def test_losers_sort(self) -> None:
        """Test losers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("losers")
        assert config == {"sortBy": "change", "sortOrder": "asc"}

    def test_most_active_sort(self) -> None:
        """Test most-active sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("most-active")
        assert config == {"sortBy": "volume", "sortOrder": "desc"}

    def test_penny_stocks_sort(self) -> None:
        """Test penny-stocks sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("penny-stocks")
        assert config == {"sortBy": "volume", "sortOrder": "desc"}

    def test_pre_market_gainers_sort(self) -> None:
        """Test pre-market-gainers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("pre-market-gainers")
        assert config == {"sortBy": "change", "sortOrder": "desc"}

    def test_pre_market_losers_sort(self) -> None:
        """Test pre-market-losers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("pre-market-losers")
        assert config == {"sortBy": "change", "sortOrder": "asc"}

    def test_after_hours_gainers_sort(self) -> None:
        """Test after-hours-gainers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("after-hours-gainers")
        assert config == {"sortBy": "change", "sortOrder": "desc"}

    def test_after_hours_losers_sort(self) -> None:
        """Test after-hours-losers sort configuration."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("after-hours-losers")
        assert config == {"sortBy": "change", "sortOrder": "asc"}

    def test_unknown_category_defaults_to_gainers(self) -> None:
        """Test unknown category defaults to gainers."""
        scraper = MarketMovers()
        config = scraper._get_sort_config("unknown")
        assert config == {"sortBy": "change", "sortOrder": "desc"}


class TestGetFilterConditions:
    """Test filter condition building."""

    def test_stocks_gainers_has_market_and_change_filters(self) -> None:
        """Test stocks gainers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "gainers")
        assert len(filters) == 2
        market_filter = next(f for f in filters if f["left"] == "market")
        assert market_filter["right"] == "america"
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "greater"

    def test_stocks_losers_has_market_and_change_filters(self) -> None:
        """Test stocks losers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "losers")
        assert len(filters) == 2
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "less"

    def test_penny_stocks_has_market_and_close_filters(self) -> None:
        """Test penny-stocks has market and close filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "penny-stocks")
        assert len(filters) == 2
        close_filter = next(f for f in filters if f["left"] == "close")
        assert close_filter["operation"] == "less"
        assert close_filter["right"] == 5

    def test_pre_market_gainers_has_market_and_change_filters(self) -> None:
        """Test pre-market-gainers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "pre-market-gainers")
        assert len(filters) == 2
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "greater"

    def test_pre_market_losers_has_market_and_change_filters(self) -> None:
        """Test pre-market-losers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "pre-market-losers")
        assert len(filters) == 2
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "less"

    def test_after_hours_gainers_has_market_and_change_filters(self) -> None:
        """Test after-hours-gainers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "after-hours-gainers")
        assert len(filters) == 2
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "greater"

    def test_after_hours_losers_has_market_and_change_filters(self) -> None:
        """Test after-hours-losers has market and change filters."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "after-hours-losers")
        assert len(filters) == 2
        change_filter = next(f for f in filters if f["left"] == "change")
        assert change_filter["operation"] == "less"

    def test_most_active_only_has_market_filter(self) -> None:
        """Test most-active only has market filter."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("stocks-usa", "most-active")
        assert len(filters) == 1
        assert filters[0]["left"] == "market"

    def test_crypto_no_market_filter(self) -> None:
        """Test crypto has no market filter."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("crypto", "gainers")
        market_filters = [f for f in filters if f["left"] == "market"]
        assert len(market_filters) == 0

    def test_crypto_gainers_has_change_filter(self) -> None:
        """Test crypto gainers has change filter."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("crypto", "gainers")
        assert len(filters) == 1
        change_filter = filters[0]
        assert change_filter["left"] == "change"
        assert change_filter["operation"] == "greater"

    def test_forex_no_market_filter(self) -> None:
        """Test forex has no market filter."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("forex", "losers")
        market_filters = [f for f in filters if f["left"] == "market"]
        assert len(market_filters) == 0

    def test_bonds_no_market_filter(self) -> None:
        """Test bonds has no market filter."""
        scraper = MarketMovers()
        filters = scraper._get_filter_conditions("bonds", "gainers")
        market_filters = [f for f in filters if f["left"] == "market"]
        assert len(market_filters) == 0


class TestBuildPayload:
    """Test payload building."""

    def test_payload_structure(self) -> None:
        """Test payload has correct structure."""
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

    def test_payload_columns(self) -> None:
        """Test payload columns."""
        scraper = MarketMovers()
        payload = scraper._build_payload(
            market="stocks-usa",
            category="gainers",
            fields=["name", "close", "change"],
            limit=10,
        )
        assert payload["columns"] == ["name", "close", "change"]

    def test_payload_range(self) -> None:
        """Test payload range."""
        scraper = MarketMovers()
        payload = scraper._build_payload(
            market="stocks-usa",
            category="gainers",
            fields=["name"],
            limit=25,
        )
        assert payload["range"] == [0, 25]

    def test_payload_options_language(self) -> None:
        """Test payload options includes language."""
        scraper = MarketMovers()
        payload = scraper._build_payload(
            market="stocks-usa",
            category="gainers",
            fields=["name"],
            limit=10,
            language="en",
        )
        assert payload["options"]["lang"] == "en"

    def test_payload_sort(self) -> None:
        """Test payload sort configuration."""
        scraper = MarketMovers()
        payload = scraper._build_payload(
            market="stocks-usa",
            category="gainers",
            fields=["name"],
            limit=10,
        )
        assert payload["sort"] == {"sortBy": "change", "sortOrder": "desc"}


class TestMapScannerRows:
    """Test scanner row mapping."""

    def test_maps_symbol(self) -> None:
        """Test symbol is correctly extracted."""
        scraper = MarketMovers()
        items = [{"s": "NASDAQ:AAPL", "d": ["Apple"]}]
        result = scraper._map_scanner_rows(items, ["name"])
        assert result[0]["symbol"] == "NASDAQ:AAPL"

    def test_maps_all_fields(self) -> None:
        """Test all fields are correctly mapped."""
        scraper = MarketMovers()
        items = [{"s": "NASDAQ:AAPL", "d": ["Apple", 175.50, 2.5]}]
        result = scraper._map_scanner_rows(items, ["name", "close", "change"])
        assert result[0]["name"] == "Apple"
        assert result[0]["close"] == 175.50
        assert result[0]["change"] == 2.5

    def test_handles_missing_data(self) -> None:
        """Test handles missing data gracefully."""
        scraper = MarketMovers()
        items = [{"s": "NASDAQ:AAPL", "d": ["Apple"]}]
        result = scraper._map_scanner_rows(items, ["name", "close", "change"])
        assert result[0]["name"] == "Apple"
        assert result[0]["close"] is None
        assert result[0]["change"] is None

    def test_handles_empty_items(self) -> None:
        """Test handles empty items list."""
        scraper = MarketMovers()
        items: list = []
        result = scraper._map_scanner_rows(items, ["name"])
        assert result == []

    def test_handles_missing_symbol(self) -> None:
        """Test handles missing symbol field."""
        scraper = MarketMovers()
        items = [{"d": ["Apple"]}]
        result = scraper._map_scanner_rows(items, ["name"])
        assert result[0]["symbol"] == ""

    def test_handles_missing_d(self) -> None:
        """Test handles missing d field."""
        scraper = MarketMovers()
        items = [{"s": "NASDAQ:AAPL"}]
        result = scraper._map_scanner_rows(items, ["name"])
        assert result[0]["symbol"] == "NASDAQ:AAPL"
        assert result[0]["name"] is None


class TestGetMarketMoversValidation:
    """Test get_market_movers validation."""

    def test_invalid_market(self) -> None:
        """Test invalid market returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="invalid", category="gainers", limit=10
        )
        assert result["status"] == STATUS_FAILED
        assert "Unsupported market" in result["error"]

    def test_invalid_category_for_stocks(self) -> None:
        """Test invalid category for stocks returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="invalid", limit=10
        )
        assert result["status"] == STATUS_FAILED
        assert "Unsupported category" in result["error"]

    def test_stock_category_for_crypto(self) -> None:
        """Test stock-only category rejected for crypto."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="crypto", category="penny-stocks", limit=10
        )
        assert result["status"] == STATUS_FAILED
        assert "Unsupported category" in result["error"]

    def test_limit_zero(self) -> None:
        """Test limit of 0 returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=0
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid limit" in result["error"]

    def test_limit_negative(self) -> None:
        """Test negative limit returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=-1
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid limit" in result["error"]

    def test_limit_exceeds_max(self) -> None:
        """Test limit > 1000 returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=1001
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid limit" in result["error"]

    def test_limit_not_integer(self) -> None:
        """Test non-integer limit returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            limit="10",  # type: ignore
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid limit" in result["error"]

    def test_invalid_language(self) -> None:
        """Test invalid language returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10, language="invalid"
        )
        assert result["status"] == STATUS_FAILED
        assert "Unsupported language" in result["error"]

    def test_invalid_fields_type(self) -> None:
        """Test invalid fields type returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            limit=10,
            fields="not_list",  # type: ignore
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid fields parameter" in result["error"]

    def test_invalid_fields_content(self) -> None:
        """Test invalid fields content returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa",
            category="gainers",
            limit=10,
            fields=[123],  # type: ignore
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid fields parameter" in result["error"]


class TestGetMarketMoversSuccess:
    """Test get_market_movers success cases with mocks."""

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock for _request."""
        mock = MagicMock()
        mock.return_value = (
            {
                "data": [
                    {"s": "NASDAQ:AAPL", "d": ["Apple", 175.50, 2.5]},
                ],
                "totalCount": 1,
            },
            None,
        )
        return mock

    def test_success_response_structure(self, mock_request: MagicMock) -> None:
        """Test success response has correct structure."""
        scraper = MarketMovers()
        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert result["status"] == STATUS_SUCCESS
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is None

    def test_metadata_includes_parameters(self, mock_request: MagicMock) -> None:
        """Test metadata includes input parameters."""
        scraper = MarketMovers()
        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=25
            )

        assert result["metadata"]["market"] == "stocks-usa"
        assert result["metadata"]["category"] == "gainers"
        assert result["metadata"]["limit"] == 25

    def test_data_is_list(self, mock_request: MagicMock) -> None:
        """Test data is a list."""
        scraper = MarketMovers()
        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert isinstance(result["data"], list)

    def test_data_items_have_symbol(self, mock_request: MagicMock) -> None:
        """Test data items have symbol field."""
        scraper = MarketMovers()
        with patch.object(scraper, "_request", mock_request):
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=10
            )

        assert len(result["data"]) > 0
        assert "symbol" in result["data"][0]


class TestResponseEnvelope:
    """Test standardized response envelope."""

    def test_success_response_has_all_fields(self) -> None:
        """Test success response has all required fields."""
        scraper = MarketMovers()
        response = scraper._success_response(
            data=[{"symbol": "AAPL"}],
            market="stocks-usa",
            category="gainers",
            limit=10,
        )

        assert response["status"] == STATUS_SUCCESS
        assert response["data"] == [{"symbol": "AAPL"}]
        assert response["metadata"]["market"] == "stocks-usa"
        assert response["metadata"]["category"] == "gainers"
        assert response["metadata"]["limit"] == 10
        assert response["error"] is None

    def test_error_response_has_all_fields(self) -> None:
        """Test error response has all required fields."""
        scraper = MarketMovers()
        response = scraper._error_response(
            error="Something went wrong",
            market="stocks-usa",
            category="gainers",
            limit=10,
        )

        assert response["status"] == STATUS_FAILED
        assert response["data"] is None
        assert response["metadata"]["market"] == "stocks-usa"
        assert response["metadata"]["category"] == "gainers"
        assert response["metadata"]["limit"] == 10
        assert response["error"] == "Something went wrong"
