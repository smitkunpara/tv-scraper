"""Mock tests for markets scraper.

Uses saved JSON fixtures to test without network calls.
"""

import json
import os
from unittest.mock import patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.markets import Markets

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "markets")


def _load_fixture(name: str) -> dict:
    """Load a fixture file by name."""
    filepath = os.path.join(FIXTURES_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        pytest.skip(f"Fixture not found: {name}")
    with open(filepath) as f:
        return json.load(f)


def _mock_request_success(mock_data: dict) -> tuple[dict, None]:
    """Create a mock that returns success with the provided data."""
    return mock_data, None


def _mock_request_error(error_msg: str) -> tuple[None, str]:
    """Create a mock that returns an error."""
    return None, error_msg


class TestMockMarkets:
    """Test Markets with mocked HTTP responses."""

    def test_mock_default_parameters(self) -> None:
        """Test default parameters match expected behavior."""
        fixture = _load_fixture("default")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets()

            assert result["status"] == STATUS_SUCCESS
            assert isinstance(result["data"], list)
            assert result["metadata"]["market"] == "america"
            assert result["metadata"]["sort_by"] == "market_cap"
            assert result["metadata"]["sort_order"] == "desc"
            assert result["metadata"]["limit"] == 50

    def test_mock_all_markets(self) -> None:
        """Test all market regions with fixtures."""
        # Only test markets that have fixtures saved
        markets_with_fixtures = [
            "america",
            "australia",
            "canada",
            "germany",
            "india",
            "uk",
        ]

        for market in markets_with_fixtures:
            fixture_name = f"market_{market}"
            fixture = _load_fixture(fixture_name)

            with patch.object(Markets, "_request") as mock_request:
                mock_request.return_value = _mock_request_success(fixture)
                scraper = Markets()
                result = scraper.get_markets(market=market, limit=5)

                assert result["status"] == STATUS_SUCCESS, (
                    f"Failed for market '{market}': {result.get('error')}"
                )
                assert result["metadata"]["market"] == market

    def test_mock_all_sort_criteria(self) -> None:
        """Test all sort criteria with fixtures."""
        sort_options = ["market_cap", "volume", "change", "price", "volatility"]

        for sort_by in sort_options:
            fixture_name = f"sort_{sort_by}"
            fixture = _load_fixture(fixture_name)

            with patch.object(Markets, "_request") as mock_request:
                mock_request.return_value = _mock_request_success(fixture)
                scraper = Markets()
                result = scraper.get_markets(market="america", sort_by=sort_by)

                assert result["status"] == STATUS_SUCCESS, (
                    f"Failed for sort_by '{sort_by}': {result.get('error')}"
                )
                assert result["metadata"]["sort_by"] == sort_by

    def test_mock_sort_order_asc(self) -> None:
        """Test ascending sort order."""
        fixture = _load_fixture("sort_order_asc")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(
                market="america", sort_by="market_cap", sort_order="asc"
            )

            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["sort_order"] == "asc"

    def test_mock_sort_order_desc(self) -> None:
        """Test descending sort order."""
        fixture = _load_fixture("sort_order_desc")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(
                market="america", sort_by="market_cap", sort_order="desc"
            )

            assert result["status"] == STATUS_SUCCESS
            assert result["metadata"]["sort_order"] == "desc"

    def test_mock_limit_10(self) -> None:
        """Test limit=10."""
        fixture = _load_fixture("limit_10")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(market="america", limit=10)

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) <= 10
            assert result["metadata"]["limit"] == 10

    def test_mock_limit_50(self) -> None:
        """Test limit=50."""
        fixture = _load_fixture("limit_50")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(market="america", limit=50)

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) <= 50
            assert result["metadata"]["limit"] == 50

    def test_mock_limit_100(self) -> None:
        """Test limit=100."""
        fixture = _load_fixture("limit_100")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(market="america", limit=100)

            assert result["status"] == STATUS_SUCCESS
            assert len(result["data"]) <= 100
            assert result["metadata"]["limit"] == 100

    def test_mock_custom_fields(self) -> None:
        """Test custom fields parameter."""
        fixture = _load_fixture("custom_fields")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(
                market="america",
                sort_by="volume",
                fields=["name", "close", "change", "volume"],
                limit=10,
            )

            assert result["status"] == STATUS_SUCCESS
            if result["data"]:
                first_item = result["data"][0]
                for field in ["name", "close", "change", "volume"]:
                    assert field in first_item

    def test_mock_combined_params(self) -> None:
        """Test combined parameter variations."""
        # Use markets that have fixtures saved
        combinations = [
            {"market": "america", "sort_by": "volume", "limit": 10},
            {"market": "uk", "sort_by": "change", "sort_order": "asc", "limit": 20},
            {"market": "india", "sort_by": "price", "sort_order": "desc", "limit": 50},
        ]

        for params in combinations:
            fixture = _load_fixture("default")

            with patch.object(Markets, "_request") as mock_request:
                mock_request.return_value = _mock_request_success(fixture)
                scraper = Markets()
                result = scraper.get_markets(**params)

                assert result["status"] == STATUS_SUCCESS, (
                    f"Failed for {params}: {result.get('error')}"
                )


class TestMockMarketsValidation:
    """Test validation and error handling with mocks."""

    def test_mock_invalid_market(self) -> None:
        """Test invalid market returns error."""
        scraper = Markets()
        result = scraper.get_markets(market="invalid_market")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "Unsupported market" in result["error"]
        assert "invalid_market" in result["error"]

    def test_mock_invalid_sort_by(self) -> None:
        """Test invalid sort_by returns error."""
        scraper = Markets()
        result = scraper.get_markets(sort_by="invalid_criterion")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "Unsupported sort criterion" in result["error"]

    def test_mock_invalid_sort_order(self) -> None:
        """Test invalid sort_order returns error."""
        scraper = Markets()
        result = scraper.get_markets(sort_order="invalid_order")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid sort_order" in result["error"]

    def test_mock_invalid_limit_zero(self) -> None:
        """Test limit=0 returns error."""
        scraper = Markets()
        result = scraper.get_markets(limit=0)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "Invalid limit" in result["error"]

    def test_mock_invalid_limit_negative(self) -> None:
        """Test negative limit returns error."""
        scraper = Markets()
        result = scraper.get_markets(limit=-5)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    def test_mock_invalid_limit_too_large(self) -> None:
        """Test limit > 1000 returns error."""
        scraper = Markets()
        result = scraper.get_markets(limit=1001)

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestMockMarketsNetworkErrors:
    """Test network error handling."""

    def test_mock_network_error(self) -> None:
        """Test network error returns failed status."""
        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_error(
                "Network error: Connection refused"
            )
            scraper = Markets()
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED
            assert result["data"] is None
            assert result["error"] is not None
            assert "Network error" in result["error"]

    def test_mock_empty_response(self) -> None:
        """Test empty response returns error."""
        empty_response = {"data": []}

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(empty_response)
            scraper = Markets()
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED
            assert result["data"] is None
            assert result["error"] is not None
            assert "No data found" in result["error"]

    def test_mock_missing_data_key(self) -> None:
        """Test response without data key returns error."""
        no_data_response = {}

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(no_data_response)
            scraper = Markets()
            result = scraper.get_markets()

            assert result["status"] == STATUS_FAILED


class TestMockMarketsDataMapping:
    """Test scanner row mapping functionality."""

    def test_mock_scanner_row_mapping(self) -> None:
        """Test that scanner rows are correctly mapped to field names."""
        fixture = _load_fixture("default")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets()

            if result["status"] == STATUS_SUCCESS and result["data"]:
                for item in result["data"]:
                    assert "symbol" in item
                    assert isinstance(item["symbol"], str)

    def test_mock_export_enabled(self) -> None:
        """Test export functionality with mocked data."""
        fixture = _load_fixture("default")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            with patch.object(Markets, "_export") as mock_export:
                scraper = Markets(export_result=True)
                result = scraper.get_markets()

                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_called_once()
                call_args = mock_export.call_args
                assert call_args[1]["data_category"] == "markets"

    def test_mock_export_disabled(self) -> None:
        """Test export is not called when disabled."""
        fixture = _load_fixture("default")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            with patch.object(Markets, "_export") as mock_export:
                scraper = Markets(export_result=False)
                result = scraper.get_markets()

                assert result["status"] == STATUS_SUCCESS
                mock_export.assert_not_called()


class TestMockMarketsMetadata:
    """Test metadata handling."""

    def test_mock_metadata_complete(self) -> None:
        """Test that all metadata fields are present."""
        fixture = _load_fixture("default")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(
                market="america",
                sort_by="market_cap",
                sort_order="desc",
                limit=50,
            )

            metadata = result["metadata"]
            assert "market" in metadata
            assert "sort_by" in metadata
            assert "sort_order" in metadata
            assert "limit" in metadata
            assert "total" in metadata
            assert "total_count" in metadata

    def test_mock_metadata_values(self) -> None:
        """Test metadata values match parameters."""
        fixture = _load_fixture("limit_50")

        with patch.object(Markets, "_request") as mock_request:
            mock_request.return_value = _mock_request_success(fixture)
            scraper = Markets()
            result = scraper.get_markets(
                market="america",
                sort_by="volume",
                sort_order="asc",
                limit=50,
            )

            metadata = result["metadata"]
            assert metadata["market"] == "america"
            assert metadata["sort_by"] == "volume"
            assert metadata["sort_order"] == "asc"
            assert metadata["limit"] == 50
