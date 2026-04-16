"""Live API tests for markets scraper.

These tests hit TradingView endpoints directly with no mocks.
"""

import pytest

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.scrapers.market_data.markets import Markets


@pytest.mark.live
class TestLiveMarkets:
    """Live tests for Markets.get_markets."""

    def test_live_get_markets_default(self) -> None:
        """Test default parameters (america, market_cap, desc, limit=50)."""
        scraper = Markets()
        result = scraper.get_markets()

        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0
        assert result["error"] is None
        assert result["metadata"]["market"] == "america"
        assert result["metadata"]["sort_by"] == "market_cap"
        assert result["metadata"]["sort_order"] == "desc"
        assert result["metadata"]["limit"] == 50

    def test_live_get_markets_all_markets(self) -> None:
        """Test all supported market regions."""
        scraper = Markets()
        markets = [
            "america",
            "australia",
            "canada",
            "germany",
            "india",
            "uk",
            "global",
        ]

        for market in markets:
            result = scraper.get_markets(market=market, limit=5)
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for market '{market}': {result.get('error')}"
            )
            assert isinstance(result["data"], list)
            assert result["metadata"]["market"] == market

    def test_live_get_markets_all_sort_options(self) -> None:
        """Test all sort criteria."""
        scraper = Markets()
        sort_options = ["market_cap", "volume", "change", "price", "volatility"]

        for sort_by in sort_options:
            result = scraper.get_markets(market="america", sort_by=sort_by, limit=10)
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for sort_by '{sort_by}': {result.get('error')}"
            )
            assert result["metadata"]["sort_by"] == sort_by
            assert isinstance(result["data"], list)

    def test_live_get_markets_sort_order(self) -> None:
        """Test asc and desc sort orders."""
        scraper = Markets()

        for sort_order in ["asc", "desc"]:
            result = scraper.get_markets(
                market="america",
                sort_by="market_cap",
                sort_order=sort_order,
                limit=10,
            )
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for sort_order '{sort_order}': {result.get('error')}"
            )
            assert result["metadata"]["sort_order"] == sort_order

    def test_live_get_markets_limit_variations(self) -> None:
        """Test various limit values."""
        scraper = Markets()
        limits = [10, 50, 100]

        for limit in limits:
            result = scraper.get_markets(
                market="america",
                sort_by="market_cap",
                limit=limit,
            )
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for limit {limit}: {result.get('error')}"
            )
            assert len(result["data"]) <= limit
            assert result["metadata"]["limit"] == limit

    def test_live_get_markets_custom_fields(self) -> None:
        """Test custom fields parameter."""
        scraper = Markets()
        custom_fields = ["name", "close", "change", "volume"]

        result = scraper.get_markets(
            market="america",
            sort_by="volume",
            fields=custom_fields,
            limit=10,
        )
        assert result["status"] == STATUS_SUCCESS
        assert isinstance(result["data"], list)

        if result["data"]:
            first_item = result["data"][0]
            for field in custom_fields:
                assert field in first_item, f"Field '{field}' not in response"

    def test_live_get_markets_combined_params(self) -> None:
        """Test combined parameter variations."""
        scraper = Markets()
        combinations = [
            {"market": "uk", "sort_by": "change", "sort_order": "asc", "limit": 20},
            {"market": "india", "sort_by": "price", "sort_order": "desc", "limit": 50},
            {"market": "germany", "sort_by": "volatility", "limit": 10},
        ]

        for params in combinations:
            result = scraper.get_markets(**params)
            assert result["status"] == STATUS_SUCCESS, (
                f"Failed for {params}: {result.get('error')}"
            )
            assert isinstance(result["data"], list)


@pytest.mark.live
class TestLiveMarketsValidation:
    """Test validation and error handling."""

    def test_live_invalid_market(self) -> None:
        """Test invalid market returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(market="invalid_market")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid value" in result["error"]

    def test_live_invalid_sort_by(self) -> None:
        """Test invalid sort_by returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(sort_by="invalid_criterion")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid value" in result["error"]

    def test_live_invalid_sort_order(self) -> None:
        """Test invalid sort_order returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(sort_order="invalid_order")

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid value" in result["error"]

    def test_live_invalid_limit_zero(self) -> None:
        """Test limit=0 returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(limit=0)

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid value" in result["error"]

    def test_live_invalid_limit_negative(self) -> None:
        """Test negative limit returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(limit=-1)

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None

    def test_live_invalid_limit_too_large(self) -> None:
        """Test limit > 1000 returns failed status."""
        scraper = Markets()
        result = scraper.get_markets(limit=1001)

        assert result["status"] == "failed"
        assert result["data"] is None
        assert result["error"] is not None


@pytest.mark.live
class TestLiveMarketsEdgeCases:
    """Test edge cases and data integrity."""

    def test_live_markets_response_structure(self) -> None:
        """Verify response has all required fields."""
        scraper = Markets()
        result = scraper.get_markets(market="america", limit=10)

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result

        metadata = result["metadata"]
        assert "market" in metadata
        assert "sort_by" in metadata
        assert "sort_order" in metadata
        assert "limit" in metadata
        assert "total" in metadata
        assert "total_available" in metadata

    def test_live_markets_data_fields(self) -> None:
        """Verify data items have expected structure."""
        scraper = Markets()
        result = scraper.get_markets(
            market="america",
            sort_by="market_cap",
            limit=10,
        )

        if result["status"] == STATUS_SUCCESS and result["data"]:
            for item in result["data"]:
                assert "symbol" in item
                assert isinstance(item["symbol"], str)
                assert ":" in item["symbol"] or "/" in item["symbol"]

    def test_live_markets_metadata_preserved(self) -> None:
        """Verify metadata is preserved on success."""
        scraper = Markets()
        result = scraper.get_markets(
            market="india",
            sort_by="volume",
            sort_order="asc",
            limit=25,
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["market"] == "india"
        assert result["metadata"]["sort_by"] == "volume"
        assert result["metadata"]["sort_order"] == "asc"
        assert result["metadata"]["limit"] == 25

    def test_live_markets_exports_enabled(self) -> None:
        """Test export functionality when enabled."""
        scraper = Markets(export="json")
        result = scraper.get_markets(market="america", limit=5)

        assert result["status"] == STATUS_SUCCESS
