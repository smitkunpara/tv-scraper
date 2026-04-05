from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals


@pytest.fixture
def fundamentals() -> Fundamentals:
    """Create a Fundamentals instance for testing."""
    return Fundamentals()


def _mock_response(data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = status_code
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"Error {status_code}"
        )
    else:
        response.raise_for_status.return_value = None
    return response


class TestFundamentalsInheritance:
    """Verify Fundamentals inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Fundamentals must be a subclass of BaseScraper."""
        assert issubclass(Fundamentals, BaseScraper)


class TestGetFundamentalsSuccess:
    """Tests for successful fundamentals retrieval."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_success(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """Get fundamentals with default (all) fields returns success envelope."""
        # Flat mock response as returned by GET /symbol endpoint
        mock_data: dict[str, Any] = {
            "total_revenue": 394000000000,
            "EBITDA": 130000000000,
            "market_cap_basic": 2800000000000,
        }
        mock_get.return_value = _mock_response(mock_data)

        result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] is not None
        assert result["data"]["total_revenue"] == 394000000000
        assert result["data"]["EBITDA"] == 130000000000

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_with_custom_fields(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """Custom fields are sent to the API and returned correctly."""
        custom_fields = ["total_revenue", "net_income", "EBITDA"]
        mock_data: dict[str, Any] = {
            "total_revenue": 394000000000,
            "net_income": 95000000000,
            "EBITDA": 130000000000,
        }
        mock_get.return_value = _mock_response(mock_data)

        result = fundamentals.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields=custom_fields
        )

        assert result["status"] == STATUS_SUCCESS
        # BaseScraper._fetch_symbol_fields adds 'symbol' key, so 3+1 = 4
        assert len(result["data"]) == 4
        assert result["data"]["total_revenue"] == 394000000000
        assert result["data"]["symbol"] == "NASDAQ:AAPL"

        # Verify fields param in request
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert "total_revenue" in params.get("fields", "")
        assert "net_income" in params.get("fields", "")

    def test_get_data_invalid_exchange(self, fundamentals: Fundamentals) -> None:
        """Invalid exchange returns error response."""
        result = fundamentals.get_fundamentals(exchange="INVALID", symbol="AAPL")
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_network_error(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Network error" in result["error"]


class TestCompareFundamentals:
    """Tests for multi-symbol comparison."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_compare_fundamentals_success(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """compare_fundamentals with valid symbols returns comparison data."""
        symbols: list[dict[str, str]] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"exchange": "NASDAQ", "symbol": "MSFT"},
        ]

        aapl_resp = _mock_response({"total_revenue": 394e9, "EBITDA": 130e9})
        msft_resp = _mock_response({"total_revenue": 211e9, "EBITDA": 102e9})

        # Mock gets for each symbol (direct calls)
        mock_get.side_effect = [aapl_resp, msft_resp]

        result = fundamentals.compare_fundamentals(symbols)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["items"]) == 2
        # Check comparison structure: result["data"]["comparison"][field][exchange:symbol]
        assert result["data"]["comparison"]["total_revenue"]["NASDAQ:AAPL"] == 394e9
        assert result["data"]["comparison"]["total_revenue"]["NASDAQ:MSFT"] == 211e9

    def test_compare_fundamentals_empty_list(self, fundamentals: Fundamentals) -> None:
        """Empty symbol list returns error response."""
        result = fundamentals.compare_fundamentals([])
        assert result["status"] == STATUS_FAILED
        assert "No symbols provided" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch("requests.get")
    def test_compare_fundamentals_partial_failure(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """One failed symbol doesn't crash the whole comparison."""
        # Use ValidationError so it is caught by get_fundamentals
        mock_verify.side_effect = [True, ValidationError("fail")]

        symbols = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"exchange": "NASDAQ", "symbol": "FAIL"},
        ]
        mock_get.return_value = _mock_response({"total_revenue": 394e9})

        result = fundamentals.compare_fundamentals(symbols)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]["items"]) == 1
        assert "NASDAQ:AAPL" in result["data"]["comparison"]["total_revenue"]
        assert "NASDAQ:FAIL" not in result["data"]["comparison"]["total_revenue"]
        assert "failed_symbols" in result["data"]
        assert len(result["data"]["failed_symbols"]) == 1

    def test_compare_fundamentals_invalid_symbol_dict_type(
        self, fundamentals: Fundamentals
    ) -> None:
        """Non-dict symbol entry returns error response."""
        symbols: list[Any] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            "invalid_string",
        ]
        result = fundamentals.compare_fundamentals(symbols)
        assert result["status"] == STATUS_FAILED
        assert "must be a dict" in result["error"]

    def test_compare_fundamentals_missing_exchange_key(
        self, fundamentals: Fundamentals
    ) -> None:
        """Symbol dict without 'exchange' key returns error response."""
        symbols: list[dict[str, str]] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"symbol": "MSFT"},
        ]
        result = fundamentals.compare_fundamentals(symbols)
        assert result["status"] == STATUS_FAILED
        assert "missing required keys" in result["error"]

    def test_compare_fundamentals_missing_symbol_key(
        self, fundamentals: Fundamentals
    ) -> None:
        """Symbol dict without 'symbol' key returns error response."""
        symbols: list[dict[str, str]] = [
            {"exchange": "NASDAQ", "symbol": "AAPL"},
            {"exchange": "NASDAQ"},
        ]
        result = fundamentals.compare_fundamentals(symbols)
        assert result["status"] == STATUS_FAILED
        assert "missing required keys" in result["error"]

    def test_compare_fundamentals_invalid_fields_type(
        self, fundamentals: Fundamentals
    ) -> None:
        """Non-list fields parameter returns error response."""
        symbols = [{"exchange": "NASDAQ", "symbol": "AAPL"}]
        result = fundamentals.compare_fundamentals(symbols, fields="not_a_list")
        assert result["status"] == STATUS_FAILED
        assert "Fields must be a list" in result["error"]

    def test_compare_fundamentals_invalid_field_name(
        self, fundamentals: Fundamentals
    ) -> None:
        """Invalid field name returns error response."""
        symbols = [{"exchange": "NASDAQ", "symbol": "AAPL"}]
        result = fundamentals.compare_fundamentals(
            symbols, fields=["total_revenue", "invalid_field_xyz"]
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid field" in result["error"]


class TestGetFundamentalsValidation:
    """Tests for get_fundamentals input validation."""

    def test_get_fundamentals_invalid_fields_type(
        self, fundamentals: Fundamentals
    ) -> None:
        """Non-list fields parameter returns error response."""
        result = fundamentals.get_fundamentals(
            exchange="NASDAQ", symbol="AAPL", fields="not_a_list"
        )
        assert result["status"] == STATUS_FAILED
        assert "Fields must be a list" in result["error"]

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    def test_get_fundamentals_invalid_field_name(
        self, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """Invalid field name returns error response."""
        result = fundamentals.get_fundamentals(
            exchange="NASDAQ",
            symbol="AAPL",
            fields=["total_revenue", "invalid_field_xyz"],
        )
        assert result["status"] == STATUS_FAILED
        assert "Invalid field" in result["error"]


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_response_has_standard_envelope(
        self, mock_get, mock_verify, fundamentals: Fundamentals
    ) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response({"total_revenue": 394e9})
        result = fundamentals.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}


class TestCookieHandling:
    """Tests for cookie authentication."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_cookie_header_applied(self, mock_get, mock_verify) -> None:
        """Cookie passed in constructor is sent as request header."""
        cookie_value = "sessionid=abc12345"
        scraper = Fundamentals(cookie=cookie_value)
        mock_get.return_value = _mock_response({"total_revenue": 100e9})

        scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("cookie") == cookie_value

    @patch.dict("os.environ", {"TRADINGVIEW_COOKIE": "env_cookie_xyz"})
    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_cookie_from_env_var(self, mock_get, mock_verify) -> None:
        """Cookie is loaded from env var if not passed to constructor."""
        # This will now pick up the env var via BaseScraper init
        scraper = Fundamentals()
        mock_get.return_value = _mock_response({"total_revenue": 100e9})

        scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

        call_kwargs = mock_get.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("cookie") == "env_cookie_xyz"
