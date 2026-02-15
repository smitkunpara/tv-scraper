"""Tests for BaseScraper class."""

import json
from unittest import mock

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import DEFAULT_TIMEOUT, STATUS_FAILED, STATUS_SUCCESS


class TestBaseScraperInit:
    """Tests for BaseScraper initialization."""

    def test_default_export_result_is_false(self) -> None:
        scraper = BaseScraper()
        assert scraper.export_result is False

    def test_default_export_type_is_json(self) -> None:
        scraper = BaseScraper()
        assert scraper.export_type == "json"

    def test_default_timeout(self) -> None:
        scraper = BaseScraper()
        assert scraper.timeout == DEFAULT_TIMEOUT

    def test_custom_init_values(self) -> None:
        scraper = BaseScraper(export_result=True, export_type="csv", timeout=30)
        assert scraper.export_result is True
        assert scraper.export_type == "csv"
        assert scraper.timeout == 30

    def test_has_user_agent_header(self) -> None:
        scraper = BaseScraper()
        assert "User-Agent" in scraper._headers
        assert isinstance(scraper._headers["User-Agent"], str)
        assert len(scraper._headers["User-Agent"]) > 0

    def test_has_validator(self) -> None:
        scraper = BaseScraper()
        from tv_scraper.core.validators import DataValidator
        assert isinstance(scraper.validator, DataValidator)


class TestSuccessResponse:
    """Tests for BaseScraper._success_response()."""

    def test_returns_correct_envelope(self) -> None:
        scraper = BaseScraper()
        response = scraper._success_response(data={"key": "value"}, symbol="AAPL")
        assert response["status"] == STATUS_SUCCESS
        assert response["data"] == {"key": "value"}
        assert response["metadata"] == {"symbol": "AAPL"}
        assert response["error"] is None

    def test_has_exactly_four_keys(self) -> None:
        scraper = BaseScraper()
        response = scraper._success_response(data=[1, 2, 3])
        assert set(response.keys()) == {"status", "data", "metadata", "error"}

    def test_metadata_with_multiple_kwargs(self) -> None:
        scraper = BaseScraper()
        response = scraper._success_response(
            data="test", symbol="AAPL", exchange="NASDAQ", total=10
        )
        assert response["metadata"]["symbol"] == "AAPL"
        assert response["metadata"]["exchange"] == "NASDAQ"
        assert response["metadata"]["total"] == 10

    def test_empty_metadata(self) -> None:
        scraper = BaseScraper()
        response = scraper._success_response(data="test")
        assert response["metadata"] == {}

    def test_response_is_json_serializable(self) -> None:
        scraper = BaseScraper()
        response = scraper._success_response(data={"nested": [1, 2]}, symbol="X")
        serialized = json.dumps(response)
        assert isinstance(serialized, str)


class TestErrorResponse:
    """Tests for BaseScraper._error_response()."""

    def test_returns_correct_envelope(self) -> None:
        scraper = BaseScraper()
        response = scraper._error_response(error="Something went wrong")
        assert response["status"] == STATUS_FAILED
        assert response["data"] is None
        assert response["error"] == "Something went wrong"

    def test_has_exactly_four_keys(self) -> None:
        scraper = BaseScraper()
        response = scraper._error_response(error="fail")
        assert set(response.keys()) == {"status", "data", "metadata", "error"}

    def test_data_is_always_none(self) -> None:
        scraper = BaseScraper()
        response = scraper._error_response(error="err", symbol="AAPL")
        assert response["data"] is None

    def test_metadata_from_kwargs(self) -> None:
        scraper = BaseScraper()
        response = scraper._error_response(error="err", symbol="AAPL", exchange="NYSE")
        assert response["metadata"]["symbol"] == "AAPL"
        assert response["metadata"]["exchange"] == "NYSE"

    def test_response_is_json_serializable(self) -> None:
        scraper = BaseScraper()
        response = scraper._error_response(error="timeout", symbol="X")
        serialized = json.dumps(response)
        assert isinstance(serialized, str)


class TestMapScannerRows:
    """Tests for BaseScraper._map_scanner_rows()."""

    def test_maps_items_to_field_named_dicts(self) -> None:
        scraper = BaseScraper()
        items = [
            {"s": "NASDAQ:AAPL", "d": [150.0, 1.5, 1000000]},
            {"s": "NYSE:MSFT", "d": [300.0, -0.5, 2000000]},
        ]
        fields = ["close", "change", "volume"]
        result = scraper._map_scanner_rows(items, fields)

        assert len(result) == 2
        assert result[0]["symbol"] == "NASDAQ:AAPL"
        assert result[0]["close"] == 150.0
        assert result[0]["change"] == 1.5
        assert result[0]["volume"] == 1000000
        assert result[1]["symbol"] == "NYSE:MSFT"

    def test_handles_missing_values(self) -> None:
        scraper = BaseScraper()
        items = [{"s": "NASDAQ:AAPL", "d": [150.0]}]
        fields = ["close", "change", "volume"]
        result = scraper._map_scanner_rows(items, fields)

        assert result[0]["close"] == 150.0
        assert result[0]["change"] is None
        assert result[0]["volume"] is None

    def test_handles_empty_items(self) -> None:
        scraper = BaseScraper()
        result = scraper._map_scanner_rows([], ["close"])
        assert result == []

    def test_handles_missing_s_key(self) -> None:
        scraper = BaseScraper()
        items = [{"d": [100.0]}]
        fields = ["close"]
        result = scraper._map_scanner_rows(items, fields)
        assert result[0]["symbol"] == ""


class TestExport:
    """Tests for BaseScraper._export()."""

    def test_does_nothing_when_export_result_false(self) -> None:
        scraper = BaseScraper(export_result=False)
        with mock.patch("tv_scraper.core.base.save_json_file") as mock_save:
            scraper._export({"key": "val"}, symbol="AAPL", data_category="test")
            mock_save.assert_not_called()

    def test_calls_save_json_file_when_json(self) -> None:
        scraper = BaseScraper(export_result=True, export_type="json")
        with mock.patch("tv_scraper.core.base.save_json_file") as mock_save, \
             mock.patch("tv_scraper.core.base.generate_export_filepath", return_value="/tmp/test.json"):
            scraper._export({"key": "val"}, symbol="AAPL", data_category="test")
            mock_save.assert_called_once_with({"key": "val"}, "/tmp/test.json")

    def test_calls_save_csv_file_when_csv(self) -> None:
        scraper = BaseScraper(export_result=True, export_type="csv")
        with mock.patch("tv_scraper.core.base.save_csv_file") as mock_save, \
             mock.patch("tv_scraper.core.base.generate_export_filepath", return_value="/tmp/test.csv"):
            scraper._export({"key": "val"}, symbol="AAPL", data_category="test")
            mock_save.assert_called_once_with({"key": "val"}, "/tmp/test.csv")


class TestMakeRequest:
    """Tests for BaseScraper._make_request()."""

    def test_passes_headers_and_timeout(self) -> None:
        scraper = BaseScraper(timeout=15)
        with mock.patch("tv_scraper.core.base.make_request") as mock_req:
            mock_req.return_value = mock.MagicMock()
            scraper._make_request("https://example.com")
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args
            assert call_kwargs[1]["headers"]["User-Agent"] == scraper._headers["User-Agent"]
            assert call_kwargs[1]["timeout"] == 15

    def test_passes_method(self) -> None:
        scraper = BaseScraper()
        with mock.patch("tv_scraper.core.base.make_request") as mock_req:
            mock_req.return_value = mock.MagicMock()
            scraper._make_request("https://example.com", method="POST")
            call_args = mock_req.call_args
            assert call_args[0][0] == "https://example.com"
            assert call_args[1]["method"] == "POST"
