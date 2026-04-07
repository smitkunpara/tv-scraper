"""Live API tests for market movers.

Tests real HTTP connections to TradingView market movers endpoint.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.screening.market_movers import MarketMovers


@pytest.mark.live
class TestLiveMarketMovers:
    """Test market movers with real API calls."""

    def test_live_stocks_usa_gainers(self) -> None:
        """Test stocks-usa market with gainers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0
        assert result["metadata"]["market"] == "stocks-usa"
        assert result["metadata"]["category"] == "gainers"

    def test_live_stocks_usa_losers(self) -> None:
        """Test stocks-usa market with losers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="losers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_most_active(self) -> None:
        """Test stocks-usa market with most-active category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="most-active", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_penny_stocks(self) -> None:
        """Test stocks-usa market with penny-stocks category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="penny-stocks", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_pre_market_gainers(self) -> None:
        """Test stocks-usa market with pre-market-gainers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="pre-market-gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_pre_market_losers(self) -> None:
        """Test stocks-usa market with pre-market-losers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="pre-market-losers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_after_hours_gainers(self) -> None:
        """Test stocks-usa market with after-hours-gainers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="after-hours-gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_usa_after_hours_losers(self) -> None:
        """Test stocks-usa market with after-hours-losers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="after-hours-losers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_uk(self) -> None:
        """Test stocks-uk market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-uk", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_india(self) -> None:
        """Test stocks-india market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-india", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_australia(self) -> None:
        """Test stocks-australia market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-australia", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_stocks_canada(self) -> None:
        """Test stocks-canada market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-canada", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_crypto(self) -> None:
        """Test crypto market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="crypto", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_crypto_losers(self) -> None:
        """Test crypto market with losers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(market="crypto", category="losers", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_crypto_most_active(self) -> None:
        """Test crypto market with most-active category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="crypto", category="most-active", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_forex(self) -> None:
        """Test forex market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(market="forex", category="gainers", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_forex_losers(self) -> None:
        """Test forex market with losers category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(market="forex", category="losers", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_forex_most_active(self) -> None:
        """Test forex market with most-active category."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="forex", category="most-active", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_bonds(self) -> None:
        """Test bonds market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(market="bonds", category="gainers", limit=10)
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_futures(self) -> None:
        """Test futures market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="futures", category="gainers", limit=10
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_different_limits(self) -> None:
        """Test limit parameter with different values."""
        for limit in [10, 50, 100]:
            scraper = MarketMovers()
            result = scraper.get_market_movers(
                market="stocks-usa", category="gainers", limit=limit
            )
            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) <= limit
            assert result["metadata"]["limit"] == limit

    def test_live_custom_fields(self) -> None:
        """Test custom fields parameter."""
        scraper = MarketMovers()
        fields = ["name", "close", "change"]
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5, fields=fields
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0
        for item in result["data"]:
            assert "name" in item
            assert "close" in item
            assert "change" in item

    def test_live_language_parameter(self) -> None:
        """Test language parameter."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5, language="en"
        )
        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) > 0

    def test_live_response_structure(self) -> None:
        """Verify response has correct structure."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5
        )
        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["error"] is None

    def test_live_data_has_required_fields(self) -> None:
        """Verify data items have required fields for stocks."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=5
        )
        assert result["status"] == STATUS_SUCCESS
        for item in result["data"]:
            assert "symbol" in item
            assert "name" in item
            assert "close" in item
            assert "change" in item


@pytest.mark.live
class TestLiveMarketMoversValidation:
    """Test validation and error handling."""

    def test_live_invalid_market(self) -> None:
        """Test invalid market returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="invalid_market", category="gainers", limit=10
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Unsupported market" in result["error"]

    def test_live_invalid_category_for_stocks(self) -> None:
        """Test invalid category for stocks market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="invalid_category", limit=10
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Unsupported category" in result["error"]

    def test_live_invalid_category_for_crypto(self) -> None:
        """Test stock-only category rejected for crypto market."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="crypto", category="penny-stocks", limit=10
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Unsupported category" in result["error"]

    def test_live_invalid_limit_zero(self) -> None:
        """Test limit of 0 returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=0
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid limit" in result["error"]

    def test_live_invalid_limit_negative(self) -> None:
        """Test negative limit returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=-1
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid limit" in result["error"]

    def test_live_invalid_limit_exceeds_max(self) -> None:
        """Test limit exceeding 1000 returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=1001
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid limit" in result["error"]

    def test_live_invalid_language(self) -> None:
        """Test invalid language returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10, language="invalid_lang"
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid language" in result["error"]

    def test_live_invalid_fields_type(self) -> None:
        """Test invalid fields type returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10, fields="not_a_list"
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid fields parameter" in result["error"]

    def test_live_invalid_fields_content(self) -> None:
        """Test invalid fields content returns error."""
        scraper = MarketMovers()
        result = scraper.get_market_movers(
            market="stocks-usa", category="gainers", limit=10, fields=[123, 456]
        )
        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "Invalid fields parameter" in result["error"]
