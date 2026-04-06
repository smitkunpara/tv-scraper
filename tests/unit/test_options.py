"""Unit tests for Options scraper.

Comprehensive tests covering valid inputs, invalid inputs, edge cases,
and various parameter combinations using mocking - no actual API calls.
"""

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
        options = Options(export_result=True, export_type="csv")
        assert options.export_result is True
        assert options.export_type == "csv"

    def test_inherits_from_scanner_scraper(self) -> None:
        """Verify Options inherits ScannerScraper methods."""
        options = Options()
        assert hasattr(options, "_success_response")
        assert hasattr(options, "_error_response")
        assert hasattr(options, "_request")
        assert hasattr(options, "_export")
        assert hasattr(options, "validator")


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


class TestValidateInputs:
    """Tests for _validate_inputs method."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validate_inputs_valid(self, mock_verify) -> None:
        """Verify valid inputs pass validation."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options._validate_inputs("NASDAQ", "AAPL", None)

        assert result is None
        mock_verify.assert_called_once_with("NASDAQ", "AAPL")

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validate_inputs_invalid_exchange(self, mock_verify) -> None:
        """Verify invalid exchange returns error."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid exchange")

        options = Options()
        result = options._validate_inputs("INVALID", "AAPL", None)

        assert result is not None
        assert result["status"] == STATUS_FAILED
        assert "metadata" in result

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validate_inputs_invalid_columns(self, mock_verify) -> None:
        """Verify invalid columns return error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options._validate_inputs(
            "NASDAQ", "AAPL", ["invalid_column", "bad_column"]
        )

        assert result is not None
        assert result["status"] == STATUS_FAILED
        assert "Invalid column names" in result["error"]
        assert "invalid_column" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validate_inputs_empty_columns(self, mock_verify) -> None:
        """Verify empty columns list passes validation."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options._validate_inputs("NASDAQ", "AAPL", [])

        assert result is None

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validate_inputs_mixed_valid_invalid_columns(self, mock_verify) -> None:
        """Verify mixed valid/invalid columns returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options._validate_inputs(
            "NASDAQ", "AAPL", ["bid", "ask", "invalid_field"]
        )

        assert result is not None
        assert result["status"] == STATUS_FAILED
        assert "invalid_field" in result["error"]


class TestBuildPayload:
    """Tests for _build_payload method."""

    def test_build_payload_basic(self) -> None:
        """Verify basic payload construction."""
        options = Options()
        payload = options._build_payload(
            cols=["bid", "ask", "strike"],
            underlying="NASDAQ:AAPL",
            filter_type="expiry",
            filter_value=20260219,
            additional_filters=[
                {"left": "type", "operation": "equal", "right": "option"},
            ],
        )

        assert payload["columns"] == ["bid", "ask", "strike"]
        assert payload["filter"] == [
            {"left": "type", "operation": "equal", "right": "option"},
        ]
        assert payload["index_filters"] == [
            {"name": "underlying_symbol", "values": ["NASDAQ:AAPL"]},
        ]

    def test_build_payload_with_strike_filter(self) -> None:
        """Verify strike filter payload construction."""
        options = Options()
        payload = options._build_payload(
            cols=DEFAULT_OPTION_COLUMNS,
            underlying="BSE:SENSEX",
            filter_type="strike",
            filter_value=83000,
            additional_filters=[
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "strike", "operation": "equal", "right": 83000},
            ],
        )

        assert "index_filters" in payload
        assert payload["index_filters"][0]["name"] == "underlying_symbol"
        assert payload["index_filters"][0]["values"] == ["BSE:SENSEX"]

    def test_build_payload_expiry_filter(self) -> None:
        """Verify expiry filter payload construction."""
        options = Options()
        payload = options._build_payload(
            cols=["strike", "bid", "ask"],
            underlying="NSE:NIFTY",
            filter_type="expiry",
            filter_value=20260320,
            additional_filters=[
                {"left": "type", "operation": "equal", "right": "option"},
                {"left": "expiration", "operation": "equal", "right": 20260320},
                {"left": "root", "operation": "equal", "right": "NIFTY"},
            ],
        )

        assert len(payload["filter"]) == 3
        expiry_filter = next(f for f in payload["filter"] if f["left"] == "expiration")
        assert expiry_filter["right"] == 20260320


class TestGetOptionsByStrike:
    """Tests for get_options_by_strike method."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_strike_success(self, mock_request, mock_verify) -> None:
        """Verify successful options by strike fetching."""
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
        result = options.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=200,
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["strike"] == 200
        assert result["metadata"]["filter_value"] == 200

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_get_options_by_strike_invalid_strike_type(self, mock_verify) -> None:
        """Verify invalid strike type returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike="invalid",
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid strike value" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_get_options_by_strike_none_strike(self, mock_verify) -> None:
        """Verify None strike returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=None,
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid strike value" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_get_options_by_strike_string_strike(self, mock_verify) -> None:
        """Verify string strike returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        options = Options()
        result = options.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike="200",
        )

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_strike_with_custom_columns(
        self, mock_request, mock_verify
    ) -> None:
        """Verify options by strike with custom columns."""
        mock_verify.return_value = ("BSE", "SENSEX")
        mock_request.return_value = (
            {
                "fields": ["strike", "bid", "ask"],
                "symbols": [
                    {"s": "BSE:SENSEX240419C083000", "f": [83000, 500, 510]},
                ],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options_by_strike(
            exchange="BSE",
            symbol="SENSEX",
            strike=83000,
            columns=["strike", "bid", "ask"],
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["data"][0]["strike"] == 83000

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_strike_float_strike(
        self, mock_request, mock_verify
    ) -> None:
        """Verify float strike values work."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_request.return_value = (
            {
                "fields": ["strike", "bid", "ask"],
                "symbols": [
                    {"s": "NASDAQ:AAPL240419C00200500", "f": [200.5, 2.5, 2.6]},
                ],
                "totalCount": 1,
            },
            None,
        )

        options = Options()
        result = options.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=200.5,
        )

        assert result["status"] == STATUS_SUCCESS


class TestGetOptionsByExpiry:
    """Tests for get_options_by_expiry method."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_expiry_success(self, mock_request, mock_verify) -> None:
        """Verify successful options by expiry fetching."""
        mock_verify.return_value = ("BSE", "SENSEX")
        mock_request.return_value = (
            {
                "fields": ["expiration", "strike", "bid", "ask", "root"],
                "symbols": [
                    {
                        "s": "BSE:SENSEX240419C083000",
                        "f": [20260419, 83000, 500, 510, "BSX"],
                    },
                    {
                        "s": "BSE:SENSEX240419P083000",
                        "f": [20260419, 83000, 100, 110, "BSX"],
                    },
                ],
                "totalCount": 2,
            },
            None,
        )

        options = Options()
        result = options.get_options_by_expiry(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260419,
            root="BSX",
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["expiration"] == 20260419
        assert result["metadata"]["filter_value"] == 20260419

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    @patch.object(Options, "_request")
    def test_get_options_by_expiry_with_custom_columns(
        self, mock_request, mock_verify
    ) -> None:
        """Verify options by expiry with custom columns."""
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
        result = options.get_options_by_expiry(
            exchange="NSE",
            symbol="NIFTY",
            expiration=20260419,
            root="NIFTY",
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

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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
        result = options.get_options_by_strike(
            exchange="NASDAQ", symbol="AAPL", strike=100
        )

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_error_response_has_all_keys(self, mock_verify) -> None:
        """Verify error response has all required keys."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid exchange")

        options = Options()
        result = options.get_options_by_strike(
            exchange="INVALID", symbol="INVALID", strike=100
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

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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
        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83000
        )

        assert result["metadata"]["exchange"] == "BSE"
        assert result["metadata"]["symbol"] == "SENSEX"

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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
        result = options.get_options_by_strike(
            exchange="NASDAQ", symbol="AAPL", strike=200.5
        )

        assert result["metadata"]["filter_value"] == 200.5

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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
        result = options.get_options_by_strike(
            exchange="NASDAQ", symbol="AAPL", strike=200
        )

        assert result["metadata"]["total"] == 10


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_empty_symbol_string(self, mock_verify) -> None:
        """Verify empty symbol string returns error."""
        mock_verify.return_value = ("NASDAQ", "")

        options = Options()
        result = options.get_options_by_strike(exchange="NASDAQ", symbol="", strike=100)

        assert result["status"] == STATUS_FAILED

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_whitespace_symbol(self, mock_verify) -> None:
        """Verify whitespace symbol returns error."""
        mock_verify.return_value = ("NASDAQ", "  ")

        options = Options()
        result = options.get_options_by_strike(
            exchange="NASDAQ", symbol="   ", strike=100
        )

        assert result["status"] == STATUS_FAILED

    @patch.object(Options, "_request")
    def test_very_large_strike_value(self, mock_request) -> None:
        """Verify very large strike value is handled."""
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [],
                "totalCount": 0,
            },
            None,
        )

        options = Options()
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options.get_options_by_strike(
                exchange="NASDAQ", symbol="AAPL", strike=999999999
            )

            assert "status" in result

    @patch.object(Options, "_request")
    def test_negative_strike_value(self, mock_request) -> None:
        """Verify negative strike value is handled."""
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [],
                "totalCount": 0,
            },
            None,
        )

        options = Options()
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options.get_options_by_strike(
                exchange="NASDAQ", symbol="AAPL", strike=-100
            )

            assert "status" in result


class TestExport:
    """Tests for export functionality."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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

        options = Options(export_result=True, export_type="json")
        options.get_options_by_strike(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert mock_save.called

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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

        options = Options(export_result=True, export_type="csv")
        options.get_options_by_strike(exchange="NASDAQ", symbol="AAPL", strike=200)

        assert mock_save.called

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
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
            options.get_options_by_strike(exchange="NASDAQ", symbol="AAPL", strike=200)
            mock_save.assert_not_called()
