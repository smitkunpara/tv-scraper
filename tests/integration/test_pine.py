"""Integration tests for Pine scripts cross-module workflows.

Tests interactions between Pine scraper and other modules.
"""

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.scripts.pine import Pine


class TestPineWithValidator:
    """Test Pine integration with DataValidator."""

    def test_pine_inherits_base_scraper(self) -> None:
        """Verify Pine extends BaseScraper."""
        scraper = Pine(cookie="test")
        assert hasattr(scraper, "_request")
        assert hasattr(scraper, "_success_response")
        assert hasattr(scraper, "_error_response")

    def test_pine_has_validator(self) -> None:
        """Verify Pine has access to validator."""
        scraper = Pine(cookie="test")
        assert scraper.validator is not None

    def test_pine_has_cookie_validation(self) -> None:
        """Verify Pine has cookie validation method."""
        scraper = Pine(cookie="test")
        assert hasattr(scraper, "_validate_cookie_required")
        result = scraper._validate_cookie_required()
        assert result is None

    def test_pine_without_cookie_fails_validation(self) -> None:
        """Verify missing cookie fails validation."""
        scraper = Pine(cookie=None)
        result = scraper._validate_cookie_required()
        assert result is not None
        assert result["status"] == STATUS_FAILED


class TestPineResponseEnvelope:
    """Test standardized response envelope consistency."""

    def test_success_response_structure(self) -> None:
        """Verify success response has all required fields."""
        scraper = Pine(cookie="test")
        result = scraper._success_response(data={"test": "data"}, name="TestScript")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == {"test": "data"}
        assert result["error"] is None

    def test_error_response_structure(self) -> None:
        """Verify error response has all required fields."""
        scraper = Pine(cookie="test")
        result = scraper._error_response(error="Test error", name="TestScript")

        assert "status" in result
        assert "data" in result
        assert "metadata" in result
        assert "error" in result
        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] == "Test error"

    def test_metadata_preserved_on_error(self) -> None:
        """Verify metadata preserved on error response."""
        scraper = Pine(cookie="test")
        result = scraper._error_response(
            error="Test error", name="TestScript", source="//@version=6"
        )

        assert result["metadata"]["name"] == "TestScript"
        assert result["metadata"]["source"] == "//@version=6"


class TestPineExport:
    """Test Pine export functionality."""

    def test_export_result_false_by_default(self) -> None:
        """Verify export disabled by default."""
        scraper = Pine()
        assert scraper.export_result is False

    def test_export_result_can_be_enabled(self) -> None:
        """Verify export can be enabled."""
        scraper = Pine(export_result=True)
        assert scraper.export_result is True

    def test_export_type_json_by_default(self) -> None:
        """Verify JSON export type by default."""
        scraper = Pine()
        assert scraper.export_type == "json"

    def test_export_type_csv(self) -> None:
        """Verify CSV export type."""
        scraper = Pine(export_type="csv")
        assert scraper.export_type == "csv"


class TestPineTimeout:
    """Test Pine timeout configuration."""

    def test_default_timeout(self) -> None:
        """Verify default timeout is 10 seconds."""
        scraper = Pine()
        assert scraper.timeout == 10

    def test_custom_timeout(self) -> None:
        """Verify custom timeout accepted."""
        scraper = Pine(timeout=30)
        assert scraper.timeout == 30

    def test_timeout_passed_to_base(self) -> None:
        """Verify timeout passed to base scraper."""
        scraper = Pine(timeout=45)
        assert scraper.timeout == 45


class TestPineCookieHandling:
    """Test cookie handling integration."""

    def test_cookie_stored(self) -> None:
        """Verify cookie is stored."""
        scraper = Pine(cookie="my_cookie")
        assert scraper.cookie == "my_cookie"

    def test_cookie_none_when_not_provided(self) -> None:
        """Verify cookie is None when not provided."""
        scraper = Pine()
        assert scraper.cookie is None

    def test_cookie_used_in_headers(self) -> None:
        """Verify cookie used in built headers."""
        scraper = Pine(cookie="header_cookie")
        headers = scraper._build_pine_headers()
        assert headers["cookie"] == "header_cookie"


class TestPineWithDataValidator:
    """Test Pine with DataValidator singleton."""

    def test_validator_is_singleton(self) -> None:
        """Verify validator is singleton."""
        scraper1 = Pine(cookie="test")
        scraper2 = Pine(cookie="test")
        assert scraper1.validator is scraper2.validator

    def test_validator_provides_exchanges(self) -> None:
        """Verify validator provides exchange data."""
        scraper = Pine(cookie="test")
        exchanges = scraper.validator.get_exchanges()
        assert isinstance(exchanges, list)

    def test_validator_provides_indicators(self) -> None:
        """Verify validator provides indicator data."""
        scraper = Pine(cookie="test")
        indicators = scraper.validator.get_indicators()
        assert isinstance(indicators, list)


class TestPineFullWorkflow:
    """Test full Pine workflow without network calls."""

    def test_validation_and_create_workflow(self) -> None:
        """Test validation preceding create workflow."""
        source = "//@version=6\nplot(close)"
        empty_validation = Pine._validate_non_empty(source, "Source code")
        assert empty_validation is None

        script_name = "TestScript"
        empty_name = Pine._validate_non_empty(script_name, "Script name")
        assert empty_name is None

    def test_edit_workflow_validation(self) -> None:
        """Test edit workflow validation steps."""
        empty_id = Pine._validate_non_empty("USER;abc", "Pine ID")
        assert empty_id is None

        empty_id_error = Pine._validate_non_empty("", "Pine ID")
        assert empty_id_error is not None

    def test_delete_workflow_validation(self) -> None:
        """Test delete workflow validation."""
        empty_id = Pine._validate_non_empty("USER;abc", "Pine ID")
        assert empty_id is None

    def test_script_item_mapping_consistency(self) -> None:
        """Verify script item mapping works for all methods."""
        item = {
            "scriptIdPart": "USER;test123",
            "scriptName": "Test Script",
            "version": "4",
            "modified": 1700000000,
        }
        mapped = Pine._map_script_item(item)

        assert mapped["id"] == "USER;test123"
        assert mapped["name"] == "Test Script"
        assert mapped["version"] == "4"
        assert mapped["modified"] == 1700000000

    def test_save_result_extraction_consistency(self) -> None:
        """Verify save result extraction works."""
        payload = {
            "result": {
                "metaInfo": {"scriptIdPart": "USER;new_script"},
                "shortDescription": "New Script",
            }
        }
        extracted = Pine._extract_save_result(payload)

        assert extracted is not None
        assert extracted["scriptIdPart"] == "USER;new_script"


class TestPineCrossModuleIntegration:
    """Test Pine integration with other scraper modules."""

    def test_pine_uses_same_base_scraper_as_others(self) -> None:
        """Verify Pine uses same base as other scrapers."""
        from tv_scraper.scrapers.social.minds import Minds

        pine = Pine(cookie="test")
        minds = Minds()

        assert type(pine).__bases__[0] == type(minds).__bases__[0]

    def test_pine_has_same_response_methods(self) -> None:
        """Verify Pine has same response methods as BaseScraper."""
        pine = Pine(cookie="test")

        assert hasattr(pine, "_success_response")
        assert hasattr(pine, "_error_response")

        success = pine._success_response(data={"test": True})
        assert success["status"] == STATUS_SUCCESS

        error = pine._error_response(error="Test error")
        assert error["status"] == STATUS_FAILED

    def test_pine_inherits_request_method(self) -> None:
        """Verify Pine inherits request method from BaseScraper."""
        pine = Pine(cookie="test")
        assert hasattr(pine, "_request")
        assert callable(pine._request)
