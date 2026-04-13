"""Unit tests for core validators."""

import pytest

from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validators import validate_yyyymmdd_date


class TestValidateYyyymmddDate:
    """Tests for validate_yyyymmdd_date."""

    def test_valid_yyyymmdd_date(self) -> None:
        """Verify valid YYYYMMDD dates pass validation."""
        assert validate_yyyymmdd_date("expiration", 20260419) is True

    def test_invalid_type_raises(self) -> None:
        """Verify non-integer values fail validation."""
        with pytest.raises(ValidationError, match="Must be int in YYYYMMDD format"):
            validate_yyyymmdd_date("expiration", "20260419")  # type: ignore[arg-type]

    def test_invalid_length_raises(self) -> None:
        """Verify non-8-digit values fail validation."""
        with pytest.raises(ValidationError, match="Must be in YYYYMMDD format"):
            validate_yyyymmdd_date("expiration", 202604)

    def test_invalid_month_raises(self) -> None:
        """Verify month range validation is enforced."""
        with pytest.raises(ValidationError, match="0 < MM <= 12"):
            validate_yyyymmdd_date("expiration", 20261319)

    def test_invalid_day_raises(self) -> None:
        """Verify day range validation is enforced."""
        with pytest.raises(ValidationError, match="0 < DD <= 31"):
            validate_yyyymmdd_date("expiration", 20260400)

    def test_invalid_calendar_date_raises(self) -> None:
        """Verify impossible dates fail calendar validation."""
        with pytest.raises(ValidationError, match="day is out of range"):
            validate_yyyymmdd_date("expiration", 20260231)
