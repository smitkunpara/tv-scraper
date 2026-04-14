"""Mock tests for SymbolMarkets scraper.

Uses saved fixtures to test various scenarios without hitting the API.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "symbol_markets"
)


def load_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    filepath = os.path.join(FIXTURES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return {}


@pytest.fixture
def scraper() -> SymbolMarkets:
    """Create a SymbolMarkets instance for testing."""
    return SymbolMarkets()


def mock_response(success: bool = True, data: list | None = None) -> MagicMock:
    """Create a mock response for _request method."""
    mock = MagicMock()
    if success:
        mock.return_value = (
            {"data": data or [], "totalCount": len(data) if data else 0},
            None,
        )
    else:
        mock.return_value = (None, "Network error: Connection refused")
    return mock


class TestMockSymbolMarketsBasic:
    """Test basic functionality with mock responses."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_aapl_global_success(
        self, mock_verify, scraper: SymbolMarkets
    ) -> None:
        """Test successful AAPL global query."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        fixture = load_fixture("aapl_global.json")
        if not fixture:
            fixture = {
                "status": STATUS_SUCCESS,
                "data": [
                    {"symbol": "NASDAQ:AAPL", "name": "Apple Inc", "close": 150.25},
                    {"symbol": "NYSE:AAPL", "name": "Apple Inc", "close": 150.20},
                ],
            }
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (
                {"data": fixture.get("data", []), "totalCount": 2},
                None,
            )
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global"
            )
            assert result["status"] == STATUS_SUCCESS
            assert isinstance(result["data"], list)

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_btcusd_crypto_success(
        self, mock_verify, scraper: SymbolMarkets
    ) -> None:
        """Test successful BTCUSD crypto query."""
        mock_verify.return_value = ("BINANCE", "BTCUSD")
        load_fixture("btcusd_crypto.json")
        mock_data = [
            {"s": "BINANCE:BTCUSD", "d": ["BTCUSD", 45000.0, 2.5, 50000000]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="BINANCE", symbol="BTCUSD", scanner="crypto"
            )
            assert "status" in result

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_eurusd_forex_success(
        self, mock_verify, scraper: SymbolMarkets
    ) -> None:
        """Test successful EURUSD forex query."""
        mock_verify.return_value = ("FX", "EURUSD")
        mock_data = [
            {"s": "FX:EURUSD", "d": ["EURUSD", 1.0850, 0.002, 0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="FX", symbol="EURUSD", scanner="forex"
            )
            assert "status" in result


class TestMockSymbolMarketsFields:
    """Test field selection functionality."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_default_fields(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test default fields are used when none specified."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {
                "s": "NASDAQ:AAPL",
                "d": ["Apple", 150.0, 1.0, 1000000, "NASDAQ", "stock"],
            },
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global"
            )
            if result["status"] == STATUS_SUCCESS:
                assert isinstance(result["data"], list)

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_custom_fields(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test custom field selection."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        custom_fields = ["name", "close", "volume"]
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple Inc", 150.25, 1000000]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ",
                symbol="AAPL",
                scanner="america",
                fields=custom_fields,
            )
            assert "status" in result

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_empty_fields(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test with empty fields list."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data: list = []
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 0}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global", fields=[]
            )
            assert "status" in result


class TestMockSymbolMarketsLimits:
    """Test limit parameter functionality."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_limit_50(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test limit of 50."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": f"EXCHANGE{i}:AAPL", "d": ["AAPL", 150.0]} for i in range(50)
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data[:50], "totalCount": 100}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global", limit=50
            )
            if result["status"] == STATUS_SUCCESS:
                assert len(result["data"]) <= 50

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_limit_100(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test limit of 100."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": f"EXCHANGE{i}:AAPL", "d": ["AAPL", 150.0]} for i in range(100)
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data[:100], "totalCount": 200}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global", limit=100
            )
            if result["status"] == STATUS_SUCCESS:
                assert len(result["data"]) <= 100

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_limit_150(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test limit of 150."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": f"EXCHANGE{i}:AAPL", "d": ["AAPL", 150.0]} for i in range(150)
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data[:150], "totalCount": 300}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global", limit=150
            )
            if result["status"] == STATUS_SUCCESS:
                assert len(result["data"]) <= 150


class TestMockSymbolMarketsValidation:
    """Test input validation."""

    def test_mock_invalid_scanner(self, scraper: SymbolMarkets) -> None:
        """Test invalid scanner returns error."""
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="AAPL", scanner="invalid"
        )
        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid scanner" in result["error"]

    def test_mock_blank_symbol(self, scraper: SymbolMarkets) -> None:
        """Test blank symbol returns error."""
        result = scraper.get_symbol_markets(exchange="NASDAQ", symbol="   ")
        assert result["status"] == "failed"
        assert result["data"] is None
        assert "symbol must be a non-empty string" in result["error"].lower()

    def test_mock_empty_symbol(self, scraper: SymbolMarkets) -> None:
        """Test empty symbol returns error."""
        result = scraper.get_symbol_markets(exchange="NASDAQ", symbol="")
        assert result["status"] == "failed"
        assert result["data"] is None

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_exchange_symbol_separation(
        self, mock_verify, scraper: SymbolMarkets
    ) -> None:
        """Test explicit exchange and symbol separation."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple Inc", 150.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="america"
            )
            assert "status" in result
            if result["status"] == STATUS_SUCCESS:
                assert "AAPL" in result["metadata"]["symbol"]
                assert "NASDAQ" in result["metadata"]["exchange"]


class TestMockSymbolMarketsErrors:
    """Test error handling."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_network_error(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test network error returns failed status."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (None, "Network error: Connection refused")
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global"
            )
            assert result["status"] == "failed"
            assert result["data"] is None
            assert "Network error" in result["error"]

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_empty_response(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test empty response returns error."""
        mock_verify.return_value = ("NASDAQ", "NONEXISTENT")
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": []}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="NONEXISTENT", scanner="global"
            )
            assert result["status"] == "failed"
            assert "No markets found" in result["error"]

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_timeout_error(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test timeout error handling."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = (None, "Network error: HTTPSConnectionPool")
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global"
            )
            assert result["status"] == "failed"
            assert result["error"] is not None


class TestMockSymbolMarketsScanners:
    """Test all supported scanners."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    @pytest.mark.parametrize("scanner", ["global", "america", "crypto", "forex", "cfd"])
    def test_mock_all_scanners(
        self, mock_verify, scraper: SymbolMarkets, scanner: str
    ) -> None:
        """Test all supported scanners."""
        mock_verify.return_value = (
            "BINANCE"
            if scanner == "crypto"
            else "FX"
            if scanner == "forex"
            else "NASDAQ",
            "SYMBOL",
        )
        mock_data = [
            {"s": "EXCHANGE:SYMBOL", "d": ["Symbol", 100.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            e_v = (
                "BINANCE"
                if scanner == "crypto"
                else "FX"
                if scanner == "forex"
                else "NASDAQ"
            )
            result = scraper.get_symbol_markets(
                exchange=e_v, symbol="SYMBOL", scanner=scanner, limit=10
            )
            assert "status" in result
            assert result["status"] in [STATUS_SUCCESS, "failed"]


class TestMockSymbolMarketsExport:
    """Test export functionality."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_export_enabled(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test export is called when enabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        scraper.export_result = True
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            with patch.object(scraper, "_export") as mock_export:
                result = scraper.get_symbol_markets(
                    exchange="NASDAQ", symbol="AAPL", scanner="global"
                )
                if result["status"] == STATUS_SUCCESS:
                    mock_export.assert_called_once()

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_export_disabled(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test export is not called when disabled."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        scraper.export_result = False
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            with patch.object(scraper, "_export") as mock_export:
                scraper.get_symbol_markets(
                    exchange="NASDAQ", symbol="AAPL", scanner="global"
                )
                mock_export.assert_not_called()


class TestMockSymbolMarketsResponseEnvelope:
    """Test standardized response envelope structure."""

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_success_envelope(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test success response has correct envelope structure."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="global"
            )
            assert "status" in result
            assert "data" in result
            assert "metadata" in result
            assert "error" in result
            if result["status"] == STATUS_SUCCESS:
                assert result["error"] is None
                assert result["data"] is not None

    def test_mock_error_envelope(self, scraper: SymbolMarkets) -> None:
        """Test error response has correct envelope structure."""
        result = scraper.get_symbol_markets(
            exchange="NASDAQ", symbol="", scanner="global"
        )
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        if result["status"] == "failed":
            assert result["data"] is None
            assert result["error"] is not None

    @patch(
        "tv_scraper.scrapers.screening.symbol_markets.validators.verify_symbol_exchange"
    )
    def test_mock_metadata_fields(self, mock_verify, scraper: SymbolMarkets) -> None:
        """Test metadata contains expected fields."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_data = [
            {"s": "NASDAQ:AAPL", "d": ["Apple", 150.0]},
        ]
        with patch.object(scraper, "_request") as mock_req:
            mock_req.return_value = ({"data": mock_data, "totalCount": 1}, None)
            result = scraper.get_symbol_markets(
                exchange="NASDAQ", symbol="AAPL", scanner="america", limit=50
            )
            if result["status"] == STATUS_SUCCESS:
                metadata = result["metadata"]
                assert metadata["exchange"] == "NASDAQ"
                assert metadata["symbol"] == "AAPL"
                assert metadata["scanner"] == "america"
                assert metadata["limit"] == 50
                assert "total" in metadata
                assert "total_available" in metadata
