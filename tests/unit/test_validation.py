import re

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.scrapers.market_data.options import Options


@pytest.fixture
def base_scraper():
    return BaseScraper()


@pytest.fixture
def options_scraper():
    return Options()


class TestValidateYyyymmddDate:
    def test_valid_yyyymmdd_date(self, options_scraper) -> None:
        assert options_scraper._validate_yyyymmdd_date(20260419) is True

    def test_invalid_type_raises(self, options_scraper) -> None:
        with pytest.raises(ValidationError, match="Must be int in YYYYMMDD format"):
            options_scraper._validate_yyyymmdd_date("20260419")

    def test_invalid_length_raises(self, options_scraper) -> None:
        with pytest.raises(ValidationError, match="Must be in YYYYMMDD format"):
            options_scraper._validate_yyyymmdd_date(202604)

    def test_invalid_month_raises(self, options_scraper) -> None:
        with pytest.raises(ValidationError, match="0 < MM <= 12"):
            options_scraper._validate_yyyymmdd_date(20261319)

    def test_invalid_day_raises(self, options_scraper) -> None:
        with pytest.raises(ValidationError, match="0 < DD <= 31"):
            options_scraper._validate_yyyymmdd_date(20260400)

    def test_invalid_calendar_date_raises(self, options_scraper) -> None:
        with pytest.raises(ValidationError, match="(?i)invalid date value"):
            options_scraper._validate_yyyymmdd_date(20260231)

    def test_none_passes(self, options_scraper) -> None:
        assert options_scraper._validate_yyyymmdd_date(None) is True


class TestValidateList:
    def test_all_valid(self, base_scraper) -> None:
        assert (
            base_scraper._validate_list(["DIV", "SPLIT"], {"DIV", "SPLIT", "MERGER"})
            is True
        )

    def test_single_invalid(self, base_scraper) -> None:
        with pytest.raises(ValidationError, match="'INVALID'"):
            base_scraper._validate_list(["DIV", "INVALID"], ["DIV", "SPLIT"])

    def test_multiple_invalid(self, base_scraper) -> None:
        with pytest.raises(ValidationError) as exc_info:
            base_scraper._validate_list(["FOO", "BAR", "DIV"], {"DIV", "SPLIT"})

        err_msg = str(exc_info.value)
        assert "'BAR'" in err_msg
        assert "'FOO'" in err_msg
        assert (
            "DIV"
            not in err_msg.split("Invalid values:")[1].split("Allowed", maxsplit=1)[0]
        )

    def test_empty_list_passes(self, base_scraper) -> None:
        assert base_scraper._validate_list([], {"DIV"}) is True

    def test_none_passes(self, base_scraper) -> None:
        assert base_scraper._validate_list(None, {"DIV"}) is True

    def test_allowed_types(self, base_scraper) -> None:
        assert base_scraper._validate_list(["DIV"], frozenset(["DIV"])) is True
        assert base_scraper._validate_list(["DIV"], ["DIV", "SPLIT"]) is True


class TestValidateChoice:
    def test_valid_choice(self, base_scraper) -> None:
        assert base_scraper._validate_choice("A", {"A", "B"}) is True

    def test_invalid_choice_with_suggestions(self, base_scraper) -> None:
        with pytest.raises(ValidationError, match=re.escape("Did you mean: apple?")):
            base_scraper._validate_choice("apl", ["apple", "banana", "cherry"])

    def test_none_passes(self, base_scraper) -> None:
        assert base_scraper._validate_choice(None, {"A"}) is True


class TestValidateRange:
    def test_valid_range(self, base_scraper) -> None:
        assert base_scraper._validate_range(5, 1, 10) is True

    def test_invalid_range_raises(self, base_scraper) -> None:
        with pytest.raises(ValidationError, match="Must be between 1 and 10"):
            base_scraper._validate_range(0, 1, 10)

    def test_none_passes(self, base_scraper) -> None:
        assert base_scraper._validate_range(None, 1, 10) is True
