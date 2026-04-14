"""Live API tests for Options scraper.

Tests hit TradingView endpoints directly with no mocks.
Requires live internet connection to TradingView.
"""

from typing import Any

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.options import Options


def _get_live_options_snapshot() -> tuple[str, str, int | float, int]:
    """Find a live symbol with options and return strike/expiry snapshot."""
    candidates: list[tuple[str, str, int | float]] = [
        ("NASDAQ", "AAPL", 200),
        ("BSE", "SENSEX", 83000),
        ("NSE", "NIFTY", 22000),
    ]

    scraper = Options()
    errors: list[str] = []
    for exchange, symbol, strike in candidates:
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)
        if result.get("status") == STATUS_SUCCESS and result.get("data"):
            first = result["data"][0]
            expiration = first.get("expiration")
            if isinstance(expiration, int):
                return exchange, symbol, strike, expiration
        errors.append(f"{exchange}:{symbol} -> {result.get('error')}")

    pytest.skip(
        "No live options symbol currently available from candidate set: "
        + " | ".join(errors)
    )


@pytest.mark.live
class TestLiveOptions:
    """Live tests for Options scraper."""

    def test_live_get_options_with_strike_basic(self) -> None:
        """Verify basic options by strike fetching works."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0

    def test_live_get_options_with_strike_and_columns(self) -> None:
        """Verify options by strike with custom columns."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(
            exchange=exchange,
            symbol=symbol,
            strike=strike,
            columns=["ask", "bid", "strike", "delta", "gamma"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)
        if result["data"]:
            first = result["data"][0]
            assert "strike" in first
            assert "delta" in first

    def test_live_get_options_with_expiry_basic(self) -> None:
        """Verify basic options by expiry fetching works."""
        exchange, symbol, _strike, expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(
            exchange=exchange,
            symbol=symbol,
            expiration=expiration,
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0

    def test_live_get_options_with_expiry_and_columns(self) -> None:
        """Verify options by expiry with custom columns."""
        exchange, symbol, _strike, expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(
            exchange=exchange,
            symbol=symbol,
            expiration=expiration,
            columns=["ask", "bid", "strike", "iv", "theta"],
        )

        assert result["status"] == STATUS_SUCCESS, result.get("error")
        assert isinstance(result["data"], list)
        if result["data"]:
            first = result["data"][0]
            assert "strike" in first
            assert "iv" in first

    def test_live_get_options_invalid_exchange(self) -> None:
        """Verify invalid exchange returns error."""
        scraper = Options()
        result = scraper.get_options(
            exchange="INVALID_EXCHANGE",
            symbol="AAPL",
            strike=200,
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None

    def test_live_get_options_invalid_columns(self) -> None:
        """Verify invalid column names return error."""
        scraper = Options()
        result = scraper.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=200,
            columns=["invalid_column", "another_invalid"],
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid values" in result["error"]

    def test_live_get_options_invalid_strike_type(self) -> None:
        """Verify invalid strike type returns error."""
        scraper = Options()
        result: dict[str, Any] = scraper.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike="bad",
        )

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid strike" in result["error"]

    def test_live_get_options_empty_strike(self) -> None:
        """Verify empty strike value returns error."""
        scraper = Options()
        result = scraper.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=None,
        )

        assert result["status"] == "failed"
        assert result["data"] is None

    def test_live_get_options_float_strike(self) -> None:
        """Verify float strike values work."""
        exchange, symbol, _strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(
            exchange=exchange,
            symbol=symbol,
            strike=200.50,
        )

        assert "status" in result

    def test_live_get_options_zero_strike(self) -> None:
        """Verify zero strike value is handled."""
        scraper = Options()
        result = scraper.get_options(
            exchange="NASDAQ",
            symbol="AAPL",
            strike=0,
        )

        assert "status" in result


@pytest.mark.live
class TestLiveOptionsMetadata:
    """Test metadata in live options responses."""

    def test_live_options_metadata_contains_exchange_symbol(self) -> None:
        """Verify metadata contains exchange and symbol."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        assert "metadata" in result
        assert result["metadata"]["exchange"] == exchange.upper()
        assert result["metadata"]["symbol"] == symbol.upper()

    def test_live_options_metadata_contains_filter_value(self) -> None:
        """Verify metadata contains filter value (strike or expiry)."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        assert "metadata" in result
        assert "filter_value" in result["metadata"]
        assert result["metadata"]["filter_value"] == strike

    def test_live_options_response_envelope_keys(self) -> None:
        """Verify response has all required envelope keys."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result


@pytest.mark.live
class TestLiveOptionsData:
    """Test data structure in live options responses."""

    def test_live_options_data_contains_required_fields(self) -> None:
        """Verify options data contains required fields."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        if result["status"] == STATUS_SUCCESS and result["data"]:
            first = result["data"][0]
            assert "symbol" in first
            assert "strike" in first

    def test_live_options_data_total_count(self) -> None:
        """Verify metadata contains total count."""
        exchange, symbol, strike, _expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(exchange=exchange, symbol=symbol, strike=strike)

        if result["status"] == STATUS_SUCCESS:
            assert "total" in result["metadata"]
            assert isinstance(result["metadata"]["total"], int)


@pytest.mark.live
class TestLiveOptionsBSE:
    """Test BSE-specific options (SENSEX)."""

    def test_live_bse_sensex_options(self) -> None:
        """Verify BSE SENSEX options work."""
        scraper = Options()
        result = scraper.get_options(
            exchange="BSE",
            symbol="SENSEX",
            strike=83000,
        )

        assert "status" in result

    def test_live_bse_sensex_expiry_options(self) -> None:
        """Verify BSE SENSEX expiry options work."""
        scraper = Options()
        result = scraper.get_options(
            exchange="BSE",
            symbol="SENSEX",
            expiration=20260219,
        )

        assert "status" in result

    def test_live_bse_sensex_expiry_and_strike_options(self) -> None:
        """Verify combined expiry and strike filters work in live mode."""
        exchange, symbol, strike, expiration = _get_live_options_snapshot()

        scraper = Options()
        result = scraper.get_options(
            exchange=exchange,
            symbol=symbol,
            expiration=expiration,
            strike=strike,
        )

        assert "status" in result
