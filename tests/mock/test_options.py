"""Mock tests for Options scraper using saved fixtures.

Tests use pre-recorded API responses from tests/fixtures/options/.
These tests do not make actual network calls.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.options import Options

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "options"


def _load_fixture(name: str) -> dict[str, Any]:
    """Load a saved fixture from the fixtures directory."""
    fixture_file = FIXTURES_DIR / f"{name}.json"
    if not fixture_file.exists():
        pytest.skip(f"Fixture not found: {fixture_file}")
    with open(fixture_file) as f:
        return json.load(f)


@pytest.fixture
def options_scraper() -> Options:
    """Create an Options scraper instance."""
    return Options()


@pytest.fixture
def mock_response_factory():
    """Factory for creating mock responses."""

    def _create_response(
        fields: list[str],
        symbols: list[dict[str, Any]],
        total_count: int | None = None,
    ) -> tuple[dict[str, Any], None]:
        """Create a mock API response tuple."""
        data = {
            "fields": fields,
            "symbols": symbols,
        }
        if total_count is not None:
            data["totalCount"] = total_count
        elif symbols:
            data["totalCount"] = len(symbols)
        return (data, None)

    return _create_response


class TestMockGetOptionsByStrike:
    """Tests for get_options_by_strike using mocks."""

    def test_mock_by_strike_basic_response_structure(
        self, options_scraper: Options
    ) -> None:
        """Verify basic by-strike response structure."""
        mock_response = _load_fixture("by_strike_basic")

        assert mock_response["status"] == STATUS_SUCCESS
        assert isinstance(mock_response["data"], list)
        assert "metadata" in mock_response
        assert "error" in mock_response

    def test_mock_by_strike_with_columns_response_structure(
        self, options_scraper: Options
    ) -> None:
        """Verify by-strike with columns response structure."""
        mock_response = _load_fixture("by_strike_with_columns")

        assert mock_response["status"] == STATUS_SUCCESS
        if mock_response["data"]:
            first = mock_response["data"][0]
            assert "strike" in first
            assert "delta" in first or "bid" in first

    @patch.object(Options, "_request")
    def test_mock_by_strike_parses_symbol_data(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify symbol data is parsed correctly."""
        mock_request.return_value = (
            {
                "fields": [
                    "strike",
                    "bid",
                    "ask",
                    "delta",
                    "gamma",
                    "theta",
                    "vega",
                    "iv",
                ],
                "symbols": [
                    {
                        "s": "NASDAQ:AAPL240419C00200000",
                        "f": [200, 5.0, 5.1, 0.5, 0.02, -0.1, 0.15, 0.25],
                    },
                    {
                        "s": "NASDAQ:AAPL240419P00200000",
                        "f": [200, 0.1, 0.15, -0.5, -0.02, 0.1, 0.15, 0.25],
                    },
                ],
                "totalCount": 2,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["symbol"] == "NASDAQ:AAPL240419C00200000"
        assert result["data"][0]["strike"] == 200

    @patch.object(Options, "_request")
    def test_mock_by_strike_handles_empty_response(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify empty response is handled correctly."""
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [],
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=999,
            )

        assert result["status"] == STATUS_FAILED
        assert "No options found" in result["error"]


class TestMockGetOptionsByExpiry:
    """Tests for get_options_by_expiry using mocks."""

    def test_mock_by_expiry_basic_response_structure(
        self, options_scraper: Options
    ) -> None:
        """Verify basic by-expiry response structure."""
        mock_response = _load_fixture("by_expiry_basic")

        assert mock_response["status"] == STATUS_SUCCESS
        assert isinstance(mock_response["data"], list)
        assert "metadata" in mock_response

    def test_mock_by_expiry_with_columns_response_structure(
        self, options_scraper: Options
    ) -> None:
        """Verify by-expiry with columns response structure."""
        mock_response = _load_fixture("by_expiry_with_columns")

        assert mock_response["status"] == STATUS_SUCCESS
        if mock_response["data"]:
            first = mock_response["data"][0]
            assert "strike" in first
            assert "iv" in first or "theta" in first

    @patch.object(Options, "_request")
    def test_mock_by_expiry_parses_expiration_data(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify expiration data is parsed correctly."""
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

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("BSE", "SENSEX"),
        ):
            result = options_scraper.get_options_by_expiry(
                exchange="BSE",
                symbol="SENSEX",
                expiration=20260419,
                root="BSX",
            )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["data"][0]["expiration"] == 20260419
        assert result["data"][0]["root"] == "BSX"

    @patch.object(Options, "_request")
    def test_mock_by_expiry_multiple_expirations(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify multiple expiration dates are handled."""
        mock_request.return_value = (
            {
                "fields": ["expiration", "strike", "bid"],
                "symbols": [
                    {"s": "T1", "f": [20260320, 83000, 600]},
                    {"s": "T2", "f": [20260417, 83000, 500]},
                    {"s": "T3", "f": [20260515, 83000, 450]},
                ],
                "totalCount": 3,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("BSE", "SENSEX"),
        ):
            result = options_scraper.get_options_by_expiry(
                exchange="BSE",
                symbol="SENSEX",
                expiration=20260417,
                root="BSX",
            )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 3


class TestMockValidation:
    """Tests for validation using mocks."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_mock_invalid_exchange(self, mock_verify, options_scraper: Options) -> None:
        """Verify invalid exchange returns error."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError(
            "Invalid exchange: 'INVALID'. Valid exchanges include: ..."
        )

        result = options_scraper.get_options_by_strike(
            exchange="INVALID",
            symbol="AAPL",
            strike=200,
        )

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_mock_invalid_columns(self, mock_verify, options_scraper: Options) -> None:
        """Verify invalid columns return error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        result = options_scraper.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=200,
            columns=["invalid_column"],
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid column names" in result["error"]

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_mock_invalid_strike_type(
        self, mock_verify, options_scraper: Options
    ) -> None:
        """Verify invalid strike type returns error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        result = options_scraper.get_options_by_strike(
            exchange="NASDAQ",
            symbol="AAPL",
            strike="not_a_number",
        )

        assert result["status"] == STATUS_FAILED
        assert "Invalid strike value" in result["error"]


class TestMockMetadata:
    """Tests for metadata using mocks."""

    def test_mock_metadata_contains_exchange_symbol(
        self, options_scraper: Options
    ) -> None:
        """Verify metadata contains exchange and symbol."""
        mock_response = _load_fixture("by_strike_basic")

        assert "metadata" in mock_response
        assert "exchange" in mock_response["metadata"]
        assert "symbol" in mock_response["metadata"]

    def test_mock_metadata_contains_filter_value(
        self, options_scraper: Options
    ) -> None:
        """Verify metadata contains filter value."""
        mock_response = _load_fixture("by_strike_basic")

        assert "metadata" in mock_response
        assert "filter_value" in mock_response["metadata"]

    def test_mock_metadata_contains_total(self, options_scraper: Options) -> None:
        """Verify metadata contains total count."""
        mock_response = _load_fixture("by_strike_basic")

        assert "metadata" in mock_response
        assert "total" in mock_response["metadata"]

    @patch.object(Options, "_request")
    def test_mock_expiry_metadata_has_filter_value(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify expiry metadata has filter value as expiration date."""
        mock_request.return_value = (
            {
                "fields": ["expiration"],
                "symbols": [{"s": "TEST", "f": [20260419]}],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("BSE", "SENSEX"),
        ):
            result = options_scraper.get_options_by_expiry(
                exchange="BSE",
                symbol="SENSEX",
                expiration=20260419,
                root="BSX",
            )

        assert result["metadata"]["filter_value"] == 20260419


class TestMockErrorHandling:
    """Tests for error handling using mocks."""

    @patch.object(Options, "_request")
    def test_mock_network_error(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify network error is handled."""
        mock_request.return_value = (None, "Connection timeout after 10s")

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_FAILED
        assert "Connection timeout" in result["error"]

    @patch.object(Options, "_request")
    def test_mock_404_error(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify 404 error is handled."""
        mock_request.return_value = (None, "HTTP 404 Not Found")

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("INVALID", "INVALID"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="INVALID",
                symbol="INVALID",
                strike=100,
            )

        assert result["status"] == STATUS_FAILED
        assert "Options chain not found" in result["error"]

    @patch.object(Options, "_request")
    def test_mock_invalid_response_format(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify invalid response format is handled."""
        mock_request.return_value = ("not a dict", None)

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_FAILED
        assert "Invalid API response format" in result["error"]


class TestMockDataMapping:
    """Tests for data field mapping using mocks."""

    @patch.object(Options, "_request")
    def test_mock_all_greeks_parsed(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify all Greek letters are parsed correctly."""
        mock_request.return_value = (
            {
                "fields": ["delta", "gamma", "theta", "vega", "rho"],
                "symbols": [
                    {"s": "TEST", "f": [0.5, 0.02, -0.1, 0.15, 0.01]},
                ],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_SUCCESS
        option = result["data"][0]
        assert option["delta"] == 0.5
        assert option["gamma"] == 0.02
        assert option["theta"] == -0.1
        assert option["vega"] == 0.15
        assert option["rho"] == 0.01

    @patch.object(Options, "_request")
    def test_mock_iv_columns_parsed(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify bid_iv and ask_iv columns are parsed."""
        mock_request.return_value = (
            {
                "fields": ["bid_iv", "ask_iv", "iv"],
                "symbols": [
                    {"s": "TEST", "f": [0.22, 0.28, 0.25]},
                ],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_SUCCESS
        option = result["data"][0]
        assert "bid_iv" in option
        assert "ask_iv" in option
        assert "iv" in option


class TestMockResponseEnvelope:
    """Tests for response envelope structure using mocks."""

    def test_mock_success_has_all_keys(self, options_scraper: Options) -> None:
        """Verify success response has all required keys."""
        mock_response = _load_fixture("by_strike_basic")

        assert "status" in mock_response
        assert "data" in mock_response
        assert "metadata" in mock_response
        assert "error" in mock_response
        assert mock_response["status"] == STATUS_SUCCESS
        assert mock_response["error"] is None

    @patch.object(Options, "_request")
    def test_mock_error_has_all_keys(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify error response has all required keys."""
        from tv_scraper.core.exceptions import ValidationError

        mock_request.return_value = (None, "Network error")

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            side_effect=ValidationError("Invalid exchange"),
        ):
            result = options_scraper.get_options_by_strike(
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


class TestMockExport:
    """Tests for export functionality using mocks."""

    @patch.object(Options, "_request")
    @patch("tv_scraper.core.base.save_json_file")
    def test_mock_export_json(
        self, mock_save: MagicMock, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify JSON export works."""
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            options_scraper.export_result = True
            options_scraper.export_type = "json"
            options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert mock_save.called

    @patch.object(Options, "_request")
    @patch("tv_scraper.core.base.save_csv_file")
    def test_mock_export_csv(
        self, mock_save: MagicMock, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify CSV export works."""
        mock_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            options_scraper.export_result = True
            options_scraper.export_type = "csv"
            options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert mock_save.called
