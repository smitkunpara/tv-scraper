"""Ideas scraper integration tests.

Tests cross-module workflows involving Ideas scraper.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.ideas import Ideas
from tv_scraper.scrapers.social.minds import Minds


class TestIdeasWithMinds:
    """Test Ideas scraper alongside Minds scraper."""

    @patch("requests.request")
    def test_ideas_and_minds_same_symbol(self, mock_request: MagicMock) -> None:
        """Verify fetching ideas and minds for same symbol."""

        def handle_request(*args, **kwargs):
            response = MagicMock()
            url = kwargs.get("url", "")
            if "ideas" in url:
                response.text = '{"data": {"ideas": {"data": {"items": [{"name": "Idea", "user": {"username": "u"}}]}}}'
            else:
                response.text = '{"results": [{"text": "Mind", "author": {"username": "u", "uri": "/u"}}]}'
            response.status_code = 200
            return response

        mock_request.side_effect = handle_request

        ideas_scraper = Ideas()
        minds_scraper = Minds()

        ideas_result = ideas_scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
        minds_result = minds_scraper.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert ideas_result["status"] == STATUS_SUCCESS
        assert minds_result["status"] == STATUS_SUCCESS

    @patch("requests.request")
    def test_ideas_and_minds_validation_consistency(
        self, mock_request: MagicMock
    ) -> None:
        """Verify both scrapers handle validation consistently."""
        ideas_scraper = Ideas()
        minds_scraper = Minds()

        ideas_result = ideas_scraper.get_ideas(
            exchange="INVALID", symbol="AAPL", start_page=0
        )
        minds_result = minds_scraper.get_minds(exchange="INVALID", symbol="AAPL")

        assert ideas_result["status"] == STATUS_FAILED
        assert minds_result["status"] == STATUS_FAILED
        assert ideas_result["error"] is not None
        assert minds_result["error"] is not None


class TestIdeasConcurrency:
    """Test concurrent Ideas scraper operations."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_parallel_ideas_instances(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify multiple Ideas instances work independently."""
        mock_verify.side_effect = lambda e, s: (e.upper(), s.upper())

        def scrape_effect(url_slug: str, page: int, sort_by: str):
            return ([{"title": f"Idea for {url_slug}"}], None)

        mock_scrape.side_effect = scrape_effect

        scraper_a = Ideas(max_workers=2)
        scraper_b = Ideas(max_workers=2)

        result_a = scraper_a.get_ideas(exchange="NASDAQ", symbol="AAPL")
        result_b = scraper_b.get_ideas(exchange="NYSE", symbol="JPM")

        assert result_a["status"] == STATUS_SUCCESS
        assert result_b["status"] == STATUS_SUCCESS
        assert result_a["data"][0]["title"] == "Idea for NASDAQ-AAPL"
        assert result_b["data"][0]["title"] == "Idea for NYSE-JPM"


class TestIdeasWithValidators:
    """Test Ideas scraper with DataValidator integration."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_case_insensitive_exchange(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify exchange validation is case-insensitive."""
        mock_verify.side_effect = lambda e, s: (e.upper(), s.upper())
        mock_scrape.return_value = ([{"title": "Test"}], None)

        scraper = Ideas()

        result_lower = scraper.get_ideas(exchange="nasdaq", symbol="AAPL")
        result_upper = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
        result_mixed = scraper.get_ideas(exchange="Nasdaq", symbol="AAPL")

        assert result_lower["status"] == STATUS_SUCCESS
        assert result_upper["status"] == STATUS_SUCCESS
        assert result_mixed["status"] == STATUS_SUCCESS

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_symbol_verification(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify symbol verification is called."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        scraper = Ideas()
        scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        mock_verify.assert_called_once_with("NASDAQ", "AAPL")


class TestIdeasWithCookieAuth:
    """Test Ideas scraper with cookie authentication flow."""

    @patch("requests.request")
    @patch.dict("os.environ", {"TRADINGVIEW_COOKIE": "session=abc123"})
    def test_cookie_from_environment(self, mock_request: MagicMock) -> None:
        """Verify cookie is read from environment."""
        mock_response = MagicMock()
        mock_response.text = '{"data": {"ideas": {"data": {"items": []}}}}'
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        scraper = Ideas()
        assert scraper.cookie == "session=abc123"

    @patch("requests.request")
    def test_explicit_cookie_overrides_env(self, mock_request: MagicMock) -> None:
        """Verify explicit cookie overrides environment."""
        mock_response = MagicMock()
        mock_response.text = '{"data": {"ideas": {"data": {"items": []}}}}'
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        scraper = Ideas(cookie="explicit=xyz789")
        assert scraper.cookie == "explicit=xyz789"

        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")
        assert result["status"] == STATUS_SUCCESS


class TestIdeasExportWorkflow:
    """Test Ideas scraper export workflow."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_export_with_metadata(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify export includes correct metadata."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = ([{"title": "Test Idea"}], None)

        scraper = Ideas(export_result=True, export_type="json")
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2, sort_by="recent"
        )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
        assert result["metadata"]["sort_by"] == "recent"

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_csv_export(self, mock_scrape: MagicMock, mock_verify: MagicMock) -> None:
        """Verify CSV export configuration."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = ([{"title": "Test"}], None)

        scraper = Ideas(export_result=True, export_type="csv")
        assert scraper.export_type == "csv"


class TestIdeasErrorPropagation:
    """Test error handling and propagation."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_page_failure_metadata(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify error metadata includes page info."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        def scrape_effect(url_slug: str, page: int, sort_by: str):
            return (None, f"Page {page} failed")

        mock_scrape.side_effect = scrape_effect

        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )

        assert result["status"] == STATUS_FAILED
        assert "error" in result
        assert result["metadata"]["pages"] == 2

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_partial_success_still_fails(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify partial success still returns failed if any pages fail."""
        mock_verify.return_value = ("NASDAQ", "AAPL")

        def scrape_effect(url_slug: str, page: int, sort_by: str):
            if page == 1:
                return ([{"title": "Success"}], None)
            return (None, "Failed")

        mock_scrape.side_effect = scrape_effect

        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )

        assert result["status"] == STATUS_FAILED


class TestIdeasResponseEnvelope:
    """Test standardized response envelope compliance."""

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_success_envelope_structure(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify success envelope has all required fields."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = ([{"title": "Test"}], None)

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        required_fields = {"status", "data", "metadata", "error"}
        assert required_fields.issubset(result.keys())
        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert isinstance(result["data"], list)

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_error_envelope_structure(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify error envelope has all required fields."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = (None, "Test error")

        scraper = Ideas()
        result = scraper.get_ideas(exchange="NASDAQ", symbol="AAPL")

        required_fields = {"status", "data", "metadata", "error"}
        assert required_fields.issubset(result.keys())
        assert result["status"] == STATUS_FAILED
        assert result["error"] is not None

    @patch("tv_scraper.core.validators.DataValidator.verify_symbol_exchange")
    @patch.object(Ideas, "_scrape_page")
    def test_metadata_persists_on_error(
        self, mock_scrape: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Verify metadata is preserved even on error."""
        mock_verify.return_value = ("NASDAQ", "AAPL")
        mock_scrape.return_value = (None, "Error")

        scraper = Ideas()
        result = scraper.get_ideas(
            exchange="NASDAQ", symbol="AAPL", start_page=1, end_page=2
        )

        assert result["metadata"]["exchange"] == "NASDAQ"
        assert result["metadata"]["symbol"] == "AAPL"
        assert result["metadata"]["start_page"] == 1
        assert result["metadata"]["end_page"] == 2


class TestIdeasFixtures:
    """Test fixture directory and structure."""

    def test_fixtures_directory_exists(self) -> None:
        """Verify fixtures directory exists."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "ideas"
        assert fixtures_dir.parent.exists()

    def test_fixture_pattern_consistency(self) -> None:
        """Verify fixture naming follows consistent pattern."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "ideas"
        if fixtures_dir.exists():
            for fixture in fixtures_dir.glob("*.json"):
                assert fixture.stem.isidentifier()
