"""Unit tests for core validators."""

import re

import pytest

from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validators import (
    validate_choice,
    validate_list,
    validate_range,
    validate_yyyymmdd_date,
)


class TestValidateYyyymmddDate:
    """Tests for validate_yyyymmdd_date."""

    def test_valid_yyyymmdd_date(self) -> None:
        """Verify valid YYYYMMDD dates pass validation."""
        assert validate_yyyymmdd_date(20260419) is True

    def test_invalid_type_raises(self) -> None:
        """Verify non-integer values fail validation."""
        with pytest.raises(ValidationError, match="Must be int in YYYYMMDD format"):
            validate_yyyymmdd_date("20260419")  # type: ignore[arg-type]

    def test_invalid_length_raises(self) -> None:
        """Verify non-8-digit values fail validation."""
        with pytest.raises(ValidationError, match="Must be in YYYYMMDD format"):
            validate_yyyymmdd_date(202604)

    def test_invalid_month_raises(self) -> None:
        """Verify month range validation is enforced."""
        with pytest.raises(ValidationError, match="0 < MM <= 12"):
            validate_yyyymmdd_date(20261319)

    def test_invalid_day_raises(self) -> None:
        """Verify day range validation is enforced."""
        with pytest.raises(ValidationError, match="0 < DD <= 31"):
            validate_yyyymmdd_date(20260400)

    def test_invalid_calendar_date_raises(self) -> None:
        """Verify impossible dates fail calendar validation."""
        with pytest.raises(ValidationError, match="day is out of range"):
            validate_yyyymmdd_date(20260231)

    def test_none_passes(self) -> None:
        """Verify None passes validation."""
        assert validate_yyyymmdd_date(None) is True


class TestValidateList:
    """Tests for validate_list."""

    def test_all_valid(self) -> None:
        """Verify valid lists pass validation."""
        assert validate_list(["DIV", "SPLIT"], {"DIV", "SPLIT", "MERGER"}) is True

    def test_single_invalid(self) -> None:
        """Verify invalid item fails validation."""
        with pytest.raises(ValidationError, match="'INVALID'"):
            validate_list(["DIV", "INVALID"], ["DIV", "SPLIT"])

    def test_multiple_invalid(self) -> None:
        """Verify multiple invalid items fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_list(["FOO", "BAR", "DIV"], {"DIV", "SPLIT"})

        err_msg = str(exc_info.value)
        assert "'BAR'" in err_msg
        assert "'FOO'" in err_msg
        # In the new generic message, the values are listed after "Invalid values: "
        assert "DIV" not in err_msg.split("Invalid values:")[1].split("Allowed")[0]

    def test_empty_list_passes(self) -> None:
        """Verify empty lists pass validation."""
        assert validate_list([], {"DIV"}) is True

    def test_none_passes(self) -> None:
        """Verify None passes validation."""
        assert validate_list(None, {"DIV"}) is True

    def test_allowed_types(self) -> None:
        """Verify different allowed types (list, set, frozenset) are supported."""
        assert validate_list(["DIV"], frozenset(["DIV"])) is True
        assert validate_list(["DIV"], ["DIV", "SPLIT"]) is True


class TestValidateChoice:
    """Tests for validate_choice."""

    def test_valid_choice(self) -> None:
        """Verify valid choice passes."""
        assert validate_choice("A", {"A", "B"}) is True

    def test_invalid_choice_with_suggestions(self) -> None:
        """Verify invalid choice fails with suggestions."""
        with pytest.raises(ValidationError, match=re.escape("Did you mean: apple?")):
            validate_choice("apl", ["apple", "banana", "cherry"])

    def test_none_passes(self) -> None:
        """Verify None passes."""
        assert validate_choice(None, {"A"}) is True


class TestValidateRange:
    """Tests for validate_range."""

    def test_valid_range(self) -> None:
        """Verify valid range passes."""
        assert validate_range(5, 1, 10) is True

    def test_invalid_range_raises(self) -> None:
        """Verify values outside range fail."""
        with pytest.raises(ValidationError, match="Must be between 1 and 10"):
            validate_range(0, 1, 10)

    def test_none_passes(self) -> None:
        """Verify None passes."""
        assert validate_range(None, 1, 10) is True
