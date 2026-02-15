"""Tests for Technicals scraper module."""

import re
from typing import Dict
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL, STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.market_data.technicals import Technicals


@pytest.fixture
def technicals() -> Technicals:
    """Create a Technicals instance for testing."""
    return Technicals()


def _mock_response(data: Dict) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


class TestTechnicalsInheritance:
    """Verify Technicals inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Technicals must be a subclass of BaseScraper."""
        assert issubclass(Technicals, BaseScraper)


class TestScrapeSuccess:
    """Tests for successful scraping scenarios."""

    def test_scrape_success_default_indicators(self, technicals: Technicals) -> None:
        """Scrape with a few indicators and verify envelope format."""
        mock_resp = _mock_response({
            "RSI": 55.0,
            "Recommend.All": 0.7,
            "CCI20": 45.0
        })
        with mock.patch.object(technicals, "_make_request", return_value=mock_resp):
            result = technicals.scrape(
                exchange="BITSTAMP",
                symbol="BTCUSD",
                technical_indicators=["RSI", "Recommend.All", "CCI20"],
            )
        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["RSI"] == 55.0
        assert result["data"]["Recommend.All"] == 0.7
        assert result["data"]["CCI20"] == 45.0
        assert result["error"] is None
        assert "metadata" in result

    def test_scrape_success_specific_indicators(self, technicals: Technicals) -> None:
        """Scrape with specific indicators returns correct mapped data."""
        mock_resp = _mock_response({
            "RSI": 50.0,
            "Stoch.K": 80.0
        })
        with mock.patch.object(technicals, "_make_request", return_value=mock_resp):
            result = technicals.scrape(
                exchange="BINANCE",
                symbol="BTCUSD",
                timeframe="1d",
                technical_indicators=["RSI", "Stoch.K"],
            )
        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["RSI"] == 50.0
        assert result["data"]["Stoch.K"] == 80.0
        assert result["error"] is None

    def test_scrape_all_indicators(self, technicals: Technicals) -> None:
        """all_indicators=True loads every indicator from the data file."""
        all_inds = technicals.validator.get_indicators()
        mock_data = {ind: float(i) for i, ind in enumerate(all_inds)}
        mock_resp = _mock_response(mock_data)
        with mock.patch.object(technicals, "_make_request", return_value=mock_resp):
            result = technicals.scrape(
                exchange="BINANCE",
                symbol="BTCUSD",
                all_indicators=True,
            )
        assert result["status"] == STATUS_SUCCESS
        for ind in all_inds:
            assert ind in result["data"]

    def test_scrape_with_timeframe(self, technicals: Technicals) -> None:
        """Non-daily timeframe appends |{value} suffix to indicator names."""
        mock_resp = _mock_response({
            "RSI|240": 60.0
        })
        with mock.patch.object(
            technicals, "_make_request", return_value=mock_resp
        ) as mock_req:
            result = technicals.scrape(
                exchange="BINANCE",
                symbol="BTCUSD",
                timeframe="4h",
                technical_indicators=["RSI"],
            )

        # Verify the API request is GET with timeframe-suffixed indicator in params
        call_kwargs = mock_req.call_args[1]
        params = call_kwargs["params"]
        assert "RSI|240" in params["fields"]
        assert params["symbol"] == "BINANCE:BTCUSD"
        assert params["no_404"] == "true"

        # Verify response keys have the suffix stripped
        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "RSI|240" not in result["data"]
        assert result["data"]["RSI"] == 60.0


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_scrape_invalid_exchange(self, technicals: Technicals) -> None:
        """Invalid exchange returns error response, does not raise."""
        result = technicals.scrape(
            exchange="INVALID_EXCHANGE",
            symbol="BTCUSD",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid exchange" in result["error"]

    def test_scrape_invalid_timeframe(self, technicals: Technicals) -> None:
        """Invalid timeframe returns error response."""
        result = technicals.scrape(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="99x",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid timeframe" in result["error"]

    def test_scrape_invalid_indicators(self, technicals: Technicals) -> None:
        """Invalid indicator name returns error response."""
        result = technicals.scrape(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["NONEXISTENT_INDICATOR"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid indicator" in result["error"]

    def test_scrape_empty_symbol(self, technicals: Technicals) -> None:
        """Empty symbol returns error response."""
        result = technicals.scrape(
            exchange="BINANCE",
            symbol="",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_scrape_network_error(self, technicals: Technicals) -> None:
        """Network error returns error response, does not raise."""
        with mock.patch.object(
            technicals,
            "_make_request",
            side_effect=NetworkError("Connection refused"),
        ):
            result = technicals.scrape(
                exchange="BINANCE",
                symbol="BTCUSD",
                technical_indicators=["RSI"],
            )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]

    def test_scrape_no_indicators_no_all(self, technicals: Technicals) -> None:
        """No indicators and all_indicators=False returns error."""
        result = technicals.scrape(
            exchange="BINANCE",
            symbol="BTCUSD",
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestResponseFormat:
    """Tests for response envelope structure."""

    def test_response_has_standard_envelope(self, technicals: Technicals) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_resp = _mock_response({
            "data": [{"s": "BINANCE:BTCUSD", "d": [50.0]}]
        })
        with mock.patch.object(technicals, "_make_request", return_value=mock_resp):
            result = technicals.scrape(
                exchange="BINANCE",
                symbol="BTCUSD",
                technical_indicators=["RSI"],
            )
        assert set(result.keys()) == {"status", "data", "metadata", "error"}
        assert result["metadata"]["exchange"] == "BINANCE"
        assert result["metadata"]["symbol"] == "BTCUSD"
        assert result["metadata"]["timeframe"] == "1d"


class TestReviseResponse:
    """Tests for _revise_response helper method."""

    def test_revise_response_strips_timeframe_suffix(
        self, technicals: Technicals
    ) -> None:
        """Keys with |timeframe are cleaned to bare indicator names."""
        data = {"RSI|240": 50.0, "Stoch.K|240": 80.0, "close|240": 100.0}
        result = technicals._revise_response(data, "240")
        assert "RSI" in result
        assert "Stoch.K" in result
        assert "close" in result
        assert "RSI|240" not in result
        assert result["RSI"] == 50.0
        assert result["close"] == 100.0

    def test_revise_response_no_suffix_when_daily(
        self, technicals: Technicals
    ) -> None:
        """When timeframe_value is empty, keys remain unchanged."""
        data = {"RSI": 50.0, "Stoch.K": 80.0}
        result = technicals._revise_response(data, "")
        assert result == data
