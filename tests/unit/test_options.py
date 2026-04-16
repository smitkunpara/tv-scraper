"""Unit tests for Options scraper."""

from unittest.mock import patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.options import (
    DEFAULT_OPTION_COLUMNS,
    VALID_OPTION_COLUMNS,
    Options,
)


class TestOptionsInit:
    """Tests for Options initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        options = Options()
        assert options.export_result is False
        assert options.export_type == "json"

    def test_custom_init(self) -> None:
        """Test custom initialization."""
        options = Options(export="csv")
        assert options.export_result is True
        assert options.export_type == "csv"

    def test_inherits_from_scanner_scraper(self) -> None:
        """Verify Options inherits ScannerScraper methods."""
        options = Options()
        assert hasattr(options, "_success_response")
        assert hasattr(options, "_error_response")
        assert hasattr(options, "_request")
        assert hasattr(options, "_export")


class TestDefaultColumns:
    """Tests for DEFAULT_OPTION_COLUMNS."""

    def test_default_columns_not_empty(self) -> None:
        """Verify default columns list is not empty."""
        assert len(DEFAULT_OPTION_COLUMNS) > 0

    def test_default_columns_contains_common_fields(self) -> None:
        """Verify default columns contain essential fields."""
        essential_fields = {
            "strike",
            "bid",
            "ask",
            "delta",
            "gamma",
            "theta",
            "vega",
            "iv",
        }
        assert essential_fields.issubset(DEFAULT_OPTION_COLUMNS)

    def test_valid_option_columns_matches_default(self) -> None:
        """Verify VALID_OPTION_COLUMNS matches DEFAULT_OPTION_COLUMNS."""
        assert VALID_OPTION_COLUMNS == set(DEFAULT_OPTION_COLUMNS)


class TestPublicValidation:
    """Tests for validation in public method."""

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_exchange(self, mock_verify) -> None:
        """Verify invalid exchange returns failed envelope."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid value")

        options = Options()
        result = options.get_options(
            exchange="INVALID",
            symbol="AAPL",
            strike=100,
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_columns(self, mock_verify) -> None:
        """Verify invalid columns return failed envelope."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=100,
            columns=["invalid_column"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid values" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_requires_at_least_one_filter(self, mock_verify) -> None:
        """Verify request fails if both expiration and strike are missing."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert "At least one filter" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_strike_type(self, mock_verify) -> None:
        """Verify invalid strike type returns failed envelope."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike="invalid",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid strike value" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_expiration_type(self, mock_verify) -> None:
        """Verify invalid expiration type returns failed envelope."""
        mock_verify.return_value = ("BSE", "SENSEX")

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration="20260419",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid date value" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_expiration_month(self, mock_verify) -> None:
        """Verify invalid expiration month returns failed envelope."""
        mock_verify.return_value = ("BSE", "SENSEX")

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20261319,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "0 < MM <= 12" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_expiration_day(self, mock_verify) -> None:
        """Verify invalid expiration day returns failed envelope."""
        mock_verify.return_value = ("BSE", "SENSEX")

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260400,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "0 < DD <= 31" in result["error"]

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_get_options_invalid_calendar_date(self, mock_verify) -> None:
        """Verify invalid calendar date returns failed envelope."""
        mock_verify.return_value = ("BSE", "SENSEX")

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260231,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "day is out of range" in result["error"]


class TestGetOptions:
    """Tests for get_options method."""

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_with_strike_success(self, mock_request, mock_verify) -> None:
        """Verify successful options fetching by strike filter."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike", "bid", "ask", "delta"],
                "symbols": [
                    {"s": "NASDAQ:AAPL240419C00200000", "f": [200, 5.0, 5.1, 0.5]},
                    {"s": "NASDAQ:AAPL240419P00200000", "f": [200, 0.1, 0.15, -0.5]},
                ],
                "totalCount": 2,
            },
            None,
        )

        options = Options()
        result = options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["strike"] == 200
        assert result["metadata"]["filter_value"] == 200

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_with_expiration_success(
        self, mock_request, mock_verify
    ) -> None:
        """Verify successful options fetching by expiration filter."""
        mock_verify.return_value = ("BSE", "SENSEX")
        mock_request.return_value = (
            {
                "fields": ["expiration", "strike", "bid", "ask"],
                "symbols": [
                    {"s": "BSE:SENSEX240419C083000", "f": [20260419, 83000, 500, 510]},
                    {"s": "BSE:SENSEX240419P083000", "f": [20260419, 83000, 100, 110]},
                ],
                "totalCount": 2,
            },
            None,
        )

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260419,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["filter_value"] == 20260419
        assert result["data"][0]["expiration"] == 20260419

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_expiration_and_strike(
        self, mock_request, mock_verify
    ) -> None:
        """Verify successful options fetching with combined filters."""
        mock_verify.return_value = ("BSE", "SENSEX")
        mock_request.return_value = (
            {
                "fields": ["expiration", "strike", "bid", "ask"],
                "symbols": [
                    {"s": "BSE:SENSEX240419C083000", "f": [20260419, 83000, 500, 510]},
                ],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260419,
            strike=83000,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["filter_value"] == {
            "expiration": 20260419,
            "strike": 83000,
        }

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_with_custom_columns(self, mock_request, mock_verify) -> None:
        """Verify options fetching with custom columns."""
        mock_verify.return_value = ("NSE", "NIFTY")
        mock_request.return_value = (
            {
                "fields": ["strike", "iv", "theta"],
                "symbols": [
                    {"s": "NSE:NIFTY240419C22000", "f": [22000, 0.25, -0.05]},
                ],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options(
            exchange="NSE",
            symbol="NIFTY",
            strike=22000,
            columns=["strike", "iv", "theta"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert "strike" in result["data"][0]
        assert "iv" in result["data"][0]


class TestExecuteRequest:
    """Tests for _execute_request method."""

    @patch.object(Options, "_request")
    def test_execute_request_network_error(self, mock_request) -> None:
        """Verify network error handling."""
        mock_request.return_value = (None, "Connection timeout")

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="NASDAQ",
            symbol="AAPL",
            filter_value=200,
        )

        assert result["status"] == STATUS_FAILED
        assert "Connection timeout" in result["error"]

    @patch.object(Options, "_request")
    def test_execute_request_404_error(self, mock_request) -> None:
        """Verify 404 error handling."""
        mock_request.return_value = (None, "HTTP 404 Not Found")

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="INVALID",
            symbol="INVALID",
            filter_value=100,
        )

        assert result["status"] == STATUS_FAILED
        assert "Options chain not found" in result["error"]

    @patch.object(Options, "_request")
    def test_execute_request_invalid_response_format(self, mock_request) -> None:
        """Verify invalid response format handling."""
        mock_request.return_value = ("not a dict", None)

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="NASDAQ",
            symbol="AAPL",
            filter_value=200,
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid API response format" in result["error"]

    @patch.object(Options, "_request")
    def test_execute_request_invalid_fields_type(self, mock_request) -> None:
        """Verify invalid fields type handling."""
        mock_request.return_value = ({"fields": "not a list", "symbols": []}, None)

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="NASDAQ",
            symbol="AAPL",
            filter_value=200,
        )

        assert result["status"] == STATUS_FAILED
        assert "'fields' and 'symbols' must be lists" in result["error"]

    @patch.object(Options, "_request")
    def test_execute_request_empty_symbols(self, mock_request) -> None:
        """Verify empty symbols handling."""
        mock_request.return_value = ({"fields": ["strike"], "symbols": []}, None)

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="NASDAQ",
            symbol="AAPL",
            filter_value=200,
        )

        assert result["status"] == STATUS_FAILED
        assert "No options found" in result["error"]

    @patch.object(Options, "_request")
    def test_execute_request_skips_non_dict_items(self, mock_request) -> None:
        """Verify non-dict items in symbols are skipped."""
        mock_request.return_value = (
            {
                "fields": ["strike", "bid"],
                "symbols": [
                    {"s": "NASDAQ:AAPL240419C00200000", "f": [200, 5.0]},
                    "not a dict",
                    {"s": "NASDAQ:AAPL240419P00200000", "f": [200, 0.1]},
                ],
                "totalCount": 2,
            },
            None,
        )

        options = Options()
        result = options._execute_request(
            payload={},
            exchange="NASDAQ",
            symbol="AAPL",
            filter_value=200,
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2


class TestResponseEnvelope:
    """Tests for standardized response envelope."""

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_success_response_has_all_keys(self, mock_request, mock_verify) -> None:
        """Verify success response has all required keys."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [100]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options(exchange="NASDAQ", symbol="AAPL", strike=100)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    def test_error_response_has_all_keys(self, mock_verify) -> None:
        """Verify error response has all required keys."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid value")

        options = Options()
        result = options.get_options(
            exchange="INVALID",
            symbol="INVALID",
            strike=100,
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestMetadata:
    """Tests for metadata in responses."""

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_metadata_contains_exchange_symbol(self, mock_request, mock_verify) -> None:
        """Verify metadata contains exchange and symbol."""
        mock_verify.return_value = ("BSE", "SENSEX")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [83000]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options(exchange="BSE", symbol="SENSEX", strike=83000)

        assert result["metadata"]["exchange"] == "BSE"
        assert result["metadata"]["symbol"] == "SENSEX"

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_metadata_contains_filter_value(self, mock_request, mock_verify) -> None:
        """Verify metadata contains filter value."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200.5)

        assert result["metadata"]["filter_value"] == 200.5

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_metadata_contains_total(self, mock_request, mock_verify) -> None:
        """Verify metadata contains total count."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "T1", "f": [200]}, {"s": "T2", "f": [200]}],
                "totalCount": 10,
            },
            None,
        )

        options = Options()
        result = options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert result["metadata"]["total"] == 2
        assert result["metadata"]["total_available"] == 10


class TestExport:
    """Tests for export functionality."""

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_json_enabled(self, mock_save, mock_request, mock_verify) -> None:
        """Verify JSON export when enabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options(export="json")
        options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert mock_save.called

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_export_csv_enabled(self, mock_save, mock_request, mock_verify) -> None:
        """Verify CSV export when enabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options(export="csv")
        options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert mock_save.called

    @patch("tv_scraper.scrapers.market_data.options.Options._verify_options_symbol")
    @patch.object(Options, "_request")
    def test_export_disabled_by_default(self, mock_request, mock_verify) -> None:
        """Verify export is disabled by default."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        with patch("tv_scraper.core.base.save_json_file") as mock_save:
            options.get_options(exchange="NASDAQ", symbol="AAPL", strike=200)
            mock_save.assert_not_called()
