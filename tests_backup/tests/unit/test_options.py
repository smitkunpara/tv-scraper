import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
        assert result["metadata"]["filter_value"] == 20260219
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
        assert result["metadata"]["filter_value"] == 83300

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_custom_columns(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Custom columns are passed in the request."""
        mock_data = {
            "totalCount": 1,
            "fields": ["strike", "bid"],
            "symbols": [{"s": "BSE:BSX260219C83300", "f": [83300, 250.05]}],
        }
        mock_post.return_value = _mock_response(mock_data)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300, columns=["strike", "bid"]
        )

        assert result["status"] == STATUS_SUCCESS
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        assert payload["columns"] == ["strike", "bid"]


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

    def test_invalid_columns(self, options: Options) -> None:
        """Invalid column names return error response."""
        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=True,
        ):
            result = options.get_options_by_strike(
                exchange="BSE",
                symbol="SENSEX",
                strike=83300,
                columns=["invalid_col", "another_invalid"],
            )
        assert result["status"] == STATUS_FAILED
        assert "invalid" in result["error"].lower()
        assert "invalid_col" in result["error"]

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

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_empty_response(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Empty symbols list returns error response."""
        mock_data = {
            "totalCount": 0,
            "fields": ["strike", "bid"],
            "symbols": [],
        }
        mock_post.return_value = _mock_response(mock_data)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_FAILED
        assert "no options found" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_invalid_response_format(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Non-dict response returns error."""
        mock_post.return_value = _mock_response("not a dict")

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_FAILED
        assert "invalid" in result["error"].lower()
        assert "format" in result["error"].lower()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_malformed_symbols(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """Malformed symbol items are skipped gracefully."""
        mock_data = {
            "totalCount": 2,
            "fields": ["strike", "bid"],
            "symbols": [
                {"s": "BSE:BSX260219C83300", "f": [83300, 250.05]},
                "not a dict",
                {"f": [84400, 300.0]},
            ],
        }
        mock_post.return_value = _mock_response(mock_data)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_options_symbol",
        return_value=True,
    )
    @patch("requests.post")
    def test_http_error_other_than_404(
        self, mock_post: MagicMock, mock_verify, options: Options
    ) -> None:
        """HTTP errors other than 404 are caught."""
        mock_post.return_value = _mock_response({}, status_code=500)

        result = options.get_options_by_strike(
            exchange="BSE", symbol="SENSEX", strike=83300
        )

        assert result["status"] == STATUS_FAILED
        assert "request failed" in result["error"].lower()
