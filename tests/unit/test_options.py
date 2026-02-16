"""Tests for Options scraper module."""

from typing import Any, Dict, Iterator, List
from unittest import mock
from unittest.mock import MagicMock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.exceptions import NetworkError
from tv_scraper.scrapers.market_data.options import Options


@pytest.fixture
def options() -> Iterator[Options]:
    """Create an Options instance for testing."""
    yield Options()


def _mock_response(data: Dict[str, Any]) -> MagicMock:
    """Create a mock requests.Response with a .json() method."""
    response = MagicMock()
    response.json.return_value = data
    response.status_code = 200
    return response


class TestInheritance:
    """Verify Options inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Options must be a subclass of BaseScraper."""
        assert issubclass(Options, BaseScraper)


class TestGetOptionsChainSuccess:
    """Tests for successful option chain retrieval."""

    def test_get_chain_by_expiry_success(self, options: Options) -> None:
        """Get chain by expiry returns mapped data."""
        mock_data = {
            "totalCount": 1,
            "fields": ["strike", "bid", "ask"],
            "symbols": [
                {"s": "BSE:BSX260219C83300", "f": [83300, 250.05, 251.5]}
            ]
        }
        mock_resp = _mock_response(mock_data)
        
        with mock.patch.object(options, "_make_request", return_value=mock_resp):
            result = options.get_chain_by_expiry(
                exchange="BSE", symbol="SENSEX", expiration=20260219, root="BSX"
            )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        item = result["data"][0]
        assert item["symbol"] == "BSE:BSX260219C83300"
        assert item["strike"] == 83300
        assert item["bid"] == 250.05
        assert item["ask"] == 251.5
        assert result["metadata"]["exchange"] == "BSE"
        assert result["metadata"]["symbol"] == "SENSEX"

    def test_get_chain_by_strike_success(self, options: Options) -> None:
        """Get chain by strike returns mapped data."""
        mock_data = {
            "totalCount": 1,
            "fields": ["expiration", "bid", "ask"],
            "symbols": [
                {"s": "BSE:BSX260219C83300", "f": [20260219, 250.05, 251.5]}
            ]
        }
        mock_resp = _mock_response(mock_data)
        
        with mock.patch.object(options, "_make_request", return_value=mock_resp):
            result = options.get_chain_by_strike(
                exchange="BSE", symbol="SENSEX", strike=83300
            )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        item = result["data"][0]
        assert item["expiration"] == 20260219
        assert result["metadata"]["filter_type"] == "strike"
        assert result["metadata"]["filter_value"] == 83300

    def test_combined_symbol_support(self, options: Options) -> None:
        """Combined EXCHANGE:SYMBOL is supported."""
        mock_data = {
            "totalCount": 0,
            "fields": [],
            "symbols": []
        }
        mock_resp = _mock_response(mock_data)
        
        with mock.patch.object(options, "_make_request", return_value=mock_resp) as mock_req:
            options.get_chain_by_strike(exchange="", symbol="BSE:SENSEX", strike=83300)
            
            # Verify payload has correct underlying
            payload = mock_req.call_args[1]["json_data"]
            assert payload["index_filters"][0]["values"] == ["BSE:SENSEX"]


class TestGetOptionsChainErrors:
    """Tests for error handling."""

    def test_invalid_exchange(self, options: Options) -> None:
        """Invalid exchange returns error response."""
        result = options.get_chain_by_strike(exchange="INVALID", symbol="SENSEX", strike=83300)
        assert result["status"] == STATUS_FAILED
        assert "exchange" in result["error"].lower()

    def test_empty_symbol(self, options: Options) -> None:
        """Empty symbol returns error response."""
        result = options.get_chain_by_strike(exchange="BSE", symbol="", strike=83300)
        assert result["status"] == STATUS_FAILED

    def test_network_error(self, options: Options) -> None:
        """Network failure returns error response."""
        with mock.patch.object(options, "_make_request", side_effect=NetworkError("Timeout")):
            result = options.get_chain_by_strike(exchange="BSE", symbol="SENSEX", strike=83300)
        
        assert result["status"] == STATUS_FAILED
        assert "Timeout" in result["error"]

    def test_404_handling(self, options: Options) -> None:
        """HTTP 404 returns a specific 'not found' error response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        
        with mock.patch.object(options, "_make_request", return_value=mock_resp):
            result = options.get_chain_by_strike(exchange="BSE", symbol="NO_OPTIONS", strike=100)
            
        assert result["status"] == STATUS_FAILED
        assert "not found" in result["error"].lower()
        assert "NO_OPTIONS" in result["error"]
