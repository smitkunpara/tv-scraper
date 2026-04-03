from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.options import Options


@pytest.fixture
def options() -> Iterator[Options]:
    """Create an Options instance for testing."""
    yield Options()


def _mock_response(data: dict[str, Any], status_code: int = 200) -> MagicMock:
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


class TestInheritance:
    """Verify Options inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Options must be a subclass of BaseScraper."""
        assert issubclass(Options, BaseScraper)


class TestGetOptionsChainSuccess:
    """Tests for successful option chain retrieval."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_get_chain_by_expiry_success(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Get chain by expiry returns mapped data."""
        mock_data = {
            "totalCount": 1,
            "fields": ["strike", "bid", "ask"],
            "symbols": [{"s": "BSE:BSX260219C83300", "f": [83300, 250.05, 251.5]}],
        }
        mock_post.return_value = _mock_response(mock_data)

        result = options.get_options_by_expiry(
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
        mock_post.assert_called_once()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_get_chain_by_strike_success(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Get chain by strike returns mapped data."""
        mock_data = {
            "totalCount": 1,
            "fields": ["expiration", "bid", "ask"],
            "symbols": [{"s": "BSE:BSX260219C83300", "f": [20260219, 250.05, 251.5]}],
        }
        mock_post.return_value = _mock_response(mock_data)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 1
        item = result["data"][0]
        assert item["expiration"] == 20260219
        assert result["metadata"]["filter_type"] == "strike"
        assert result["metadata"]["filter_value"] == 83300


class TestGetOptionsChainErrors:
    """Tests for error handling."""

    def test_invalid_exchange(self, options: Options) -> None:
        """Invalid exchange returns error response."""
        result = options.get_options_by_strike(
            exchange="INVALID", symbol="SENSEX", strike=83300
        )
        assert result["status"] == STATUS_FAILED
        assert "exchange" in result["error"].lower()

    def test_empty_symbol(self, options: Options) -> None:
        """Empty symbol returns error response."""
        result = options.get_options_by_strike(exchange="BSE", symbol="", strike=83300)
        assert result["status"] == STATUS_FAILED

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_network_error(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Network failure returns error response."""
        mock_post.side_effect = requests.RequestException("Timeout")
        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_FAILED
        assert "Timeout" in result["error"]

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_404_handling(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """HTTP 404 returns a specific 'not found' error response."""
        mock_post.return_value = _mock_response({}, status_code=404)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="NO_OPTIONS", strike=100
        )

        assert result["status"] == STATUS_FAILED
        assert "not found" in result["error"].lower()
        assert "NO_OPTIONS" in result["error"]
