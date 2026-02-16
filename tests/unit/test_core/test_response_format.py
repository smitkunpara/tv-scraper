"""Tests for response format consistency."""

import json

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS


@pytest.fixture
def scraper() -> BaseScraper:
    """Create a BaseScraper instance for testing."""
    return BaseScraper()


class TestSuccessResponseFormat:
    """Tests for success response format."""

    def test_has_exactly_required_keys(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(data="test")
        assert set(response.keys()) == {"status", "data", "metadata", "error"}

    def test_status_is_always_success(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(data=None)
        assert response["status"] == STATUS_SUCCESS
        assert response["status"] == "success"

    def test_metadata_is_dict(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(data="test", key1="v1", key2="v2")
        assert isinstance(response["metadata"], dict)

    def test_metadata_has_arbitrary_keys(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(data="test", foo="bar", baz=42)
        assert response["metadata"]["foo"] == "bar"
        assert response["metadata"]["baz"] == 42

    def test_error_is_none(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(data="test")
        assert response["error"] is None

    def test_is_json_serializable(self, scraper: BaseScraper) -> None:
        response = scraper._success_response(
            data={"nested": [1, 2, {"deep": True}]},
            symbol="AAPL",
            total=100,
        )
        serialized = json.dumps(response)
        deserialized = json.loads(serialized)
        assert deserialized == response


class TestErrorResponseFormat:
    """Tests for error response format."""

    def test_has_exactly_required_keys(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="fail")
        assert set(response.keys()) == {"status", "data", "metadata", "error"}

    def test_status_is_always_failed(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="fail")
        assert response["status"] == STATUS_FAILED
        assert response["status"] == "failed"

    def test_data_is_always_none(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="err")
        assert response["data"] is None

    def test_error_contains_message(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="Something broke")
        assert response["error"] == "Something broke"

    def test_metadata_is_dict(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="err", key1="v1")
        assert isinstance(response["metadata"], dict)

    def test_is_json_serializable(self, scraper: BaseScraper) -> None:
        response = scraper._error_response(error="timeout", symbol="AAPL")
        serialized = json.dumps(response)
        deserialized = json.loads(serialized)
        assert deserialized == response
