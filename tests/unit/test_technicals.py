from unittest.mock import MagicMock, patch

import pytest
import requests

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.technicals import Technicals


@pytest.fixture
def technicals() -> Technicals:
    """Create a Technicals instance for testing."""
    return Technicals()


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


class TestTechnicalsInheritance:
    """Verify Technicals inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Technicals must be a subclass of BaseScraper."""
        assert issubclass(Technicals, BaseScraper)


class TestScrapeSuccess:
    """Tests for successful scraping scenarios."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_success_default_indicators(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Scrape with a few indicators and verify envelope format."""
        mock_get.return_value = _mock_response(
            {"RSI": 55.0, "Recommend.All": 0.7, "CCI20": 45.0}
        )
        result = technicals.get_technicals(
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
        mock_get.assert_called_once()

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_success_specific_indicators(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Scrape with specific indicators returns correct mapped data."""
        mock_get.return_value = _mock_response({"RSI": 50.0, "Stoch.K": 80.0})
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="1d",
            technical_indicators=["RSI", "Stoch.K"],
        )
        assert result["status"] == STATUS_SUCCESS
        assert result["data"]["RSI"] == 50.0
        assert result["data"]["Stoch.K"] == 80.0
        assert result["error"] is None

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_all_indicators(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """all_indicators=True loads every indicator from the data file."""
        all_inds = technicals.validator.get_indicators()
        mock_data = {ind: float(i) for i, ind in enumerate(all_inds)}
        mock_get.return_value = _mock_response(mock_data)
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            all_indicators=True,
        )
        assert result["status"] == STATUS_SUCCESS
        for ind in all_inds:
            assert ind in result["data"]

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_with_timeframe(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Non-daily timeframe appends |{value} suffix to indicator names."""
        mock_get.return_value = _mock_response({"RSI|240": 60.0})
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="4h",
            technical_indicators=["RSI"],
        )

        # Verify the API request is GET with timeframe-suffixed indicator in params
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        assert "RSI|240" in params["fields"]
        assert params["symbol"] == "BINANCE:BTCUSD"
        assert params["no_404"] == "true"

        # Verify response keys have the suffix stripped
        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "RSI|240" not in result["data"]
        assert result["data"]["RSI"] == 60.0

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_with_weekly_monthly_timeframe(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Weekly and Monthly timeframes use |1W and |1M suffixes."""
        # Test Weekly
        mock_get.return_value = _mock_response({"RSI|1W": 70.0})
        result_w = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="1w",
            technical_indicators=["RSI"],
        )
        assert "RSI|1W" in mock_get.call_args[1]["params"]["fields"]
        assert result_w["data"]["RSI"] == 70.0

        # Test Monthly
        mock_get.reset_mock()
        mock_get.return_value = _mock_response({"RSI|1M": 75.0})
        result_m = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="1M",
            technical_indicators=["RSI"],
        )
        assert "RSI|1M" in mock_get.call_args[1]["params"]["fields"]
        assert result_m["data"]["RSI"] == 75.0

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_fields_filtering_with_timeframe_suffix(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Fields parameter works with timeframe suffixes."""
        mock_get.return_value = _mock_response(
            {
                "RSI|240": 60.0,
                "CCI20|240": 45.0,
                "EMA10|240": 100.0,
            }
        )
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="4h",
            technical_indicators=["RSI", "CCI20", "EMA10"],
            fields=["RSI|240", "CCI20"],
        )
        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "CCI20" in result["data"]
        assert "EMA10" not in result["data"]

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_fields_filtering_without_suffix(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Fields parameter works without timeframe suffixes."""
        mock_get.return_value = _mock_response({"RSI|240": 60.0, "CCI20|240": 45.0})
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="4h",
            technical_indicators=["RSI", "CCI20"],
            fields=["RSI"],
        )
        assert result["status"] == STATUS_SUCCESS
        assert "RSI" in result["data"]
        assert "CCI20" not in result["data"]


class TestScrapeErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_data_invalid_exchange(self, technicals: Technicals) -> None:
        """Invalid exchange returns error response, does not raise."""
        result = technicals.get_technicals(
            exchange="INVALID_EXCHANGE",
            symbol="BTCUSD",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid exchange" in result["error"]

    def test_get_data_invalid_timeframe(self, technicals: Technicals) -> None:
        """Invalid timeframe returns error response."""
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            timeframe="99x",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid timeframe" in result["error"]

    def test_get_data_invalid_indicators(self, technicals: Technicals) -> None:
        """Invalid indicator name returns error response."""
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["NONEXISTENT_INDICATOR"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Invalid indicator" in result["error"]

    def test_get_data_empty_symbol(self, technicals: Technicals) -> None:
        """Empty symbol returns error response."""
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_get_data_network_error(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Network error returns error response, does not raise."""
        mock_get.side_effect = requests.RequestException("Connection refused")
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["RSI"],
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert "Connection refused" in result["error"]

    def test_get_data_no_indicators_no_all(self, technicals: Technicals) -> None:
        """No indicators and all_indicators=False returns error."""
        result = technicals.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
        )
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch(
        "tv_scraper.core.validators.DataValidator.verify_symbol_exchange",
        return_value=True,
    )
    @patch("requests.get")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, mock_verify: MagicMock, technicals: Technicals
    ) -> None:
        """Success response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response({"RSI": 50.0})
        result = technicals.get_technicals(
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

    def test_revise_response_no_suffix_when_daily(self, technicals: Technicals) -> None:
        """When timeframe_value is empty, keys remain unchanged."""
        data = {"RSI": 50.0, "Stoch.K": 80.0}
        result = technicals._revise_response(data, "")
        assert result == data
