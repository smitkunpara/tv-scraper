"""Tests for DataValidator singleton."""

from typing import Iterator

import pytest

from tv_scraper.core.validators import DataValidator
from tv_scraper.core.exceptions import ValidationError


@pytest.fixture(autouse=True)
def reset_validator() -> Iterator[None]:
    """Reset DataValidator singleton before each test."""
    DataValidator.reset()
    yield
    DataValidator.reset()


class TestSingleton:
    """Tests for singleton behavior."""

    def test_same_instance_returned(self) -> None:
        v1 = DataValidator()
        v2 = DataValidator()
        assert v1 is v2

    def test_reset_creates_fresh_instance(self) -> None:
        v1 = DataValidator()
        DataValidator.reset()
        v2 = DataValidator()
        assert v1 is not v2


class TestValidateExchange:
    """Tests for validate_exchange()."""

    def test_valid_exchange_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_exchange("BINANCE") is True

    def test_valid_exchange_case_insensitive(self) -> None:
        validator = DataValidator()
        assert validator.validate_exchange("binance") is True

    def test_invalid_exchange_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="Invalid exchange"):
            validator.validate_exchange("BINANCEE")

    def test_invalid_exchange_suggests_similar(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="BINANCE"):
            validator.validate_exchange("BINANCEE")


class TestValidateSymbol:
    """Tests for validate_symbol()."""

    def test_valid_symbol_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_symbol("NASDAQ", "AAPL") is True

    def test_empty_symbol_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="Symbol"):
            validator.validate_symbol("NASDAQ", "")

    def test_none_symbol_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError):
            validator.validate_symbol("NASDAQ", None)  # type: ignore[arg-type]

    def test_whitespace_only_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError):
            validator.validate_symbol("NASDAQ", "   ")


class TestValidateIndicators:
    """Tests for validate_indicators()."""

    def test_valid_indicators_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_indicators(["RSI", "MACD.macd"]) is True

    def test_invalid_indicator_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="Invalid indicator"):
            validator.validate_indicators(["RSI", "FAKE_INDICATOR_XYZ"])

    def test_empty_list_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="[Ee]mpty|[Nn]o indicators"):
            validator.validate_indicators([])


class TestValidateTimeframe:
    """Tests for validate_timeframe()."""

    def test_valid_timeframe_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_timeframe("1d") is True

    def test_another_valid_timeframe(self) -> None:
        validator = DataValidator()
        assert validator.validate_timeframe("1h") is True

    def test_invalid_timeframe_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="Invalid timeframe"):
            validator.validate_timeframe("99x")


class TestValidateChoice:
    """Tests for validate_choice()."""

    def test_valid_choice_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_choice("color", "red", {"red", "blue", "green"}) is True

    def test_invalid_choice_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="color"):
            validator.validate_choice("color", "yellow", {"red", "blue", "green"})


class TestValidateFields:
    """Tests for validate_fields()."""

    def test_valid_fields_returns_true(self) -> None:
        validator = DataValidator()
        assert validator.validate_fields(["a", "b"], ["a", "b", "c"]) is True

    def test_invalid_field_raises_validation_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="Invalid"):
            validator.validate_fields(["a", "z"], ["a", "b", "c"])

    def test_custom_field_name_in_error(self) -> None:
        validator = DataValidator()
        with pytest.raises(ValidationError, match="columns"):
            validator.validate_fields(["x"], ["a", "b"], field_name="columns")


class TestGetters:
    """Tests for getter methods."""

    def test_get_exchanges_returns_non_empty_list(self) -> None:
        validator = DataValidator()
        exchanges = validator.get_exchanges()
        assert isinstance(exchanges, list)
        assert len(exchanges) > 0

    def test_get_indicators_returns_non_empty_list(self) -> None:
        validator = DataValidator()
        indicators = validator.get_indicators()
        assert isinstance(indicators, list)
        assert len(indicators) > 0

    def test_get_timeframes_returns_non_empty_dict(self) -> None:
        validator = DataValidator()
        timeframes = validator.get_timeframes()
        assert isinstance(timeframes, dict)
        assert len(timeframes) > 0

    def test_exchanges_contains_known_exchange(self) -> None:
        validator = DataValidator()
        exchanges = validator.get_exchanges()
        assert "BINANCE" in exchanges

    def test_indicators_contains_known_indicator(self) -> None:
        validator = DataValidator()
        indicators = validator.get_indicators()
        assert "RSI" in indicators
