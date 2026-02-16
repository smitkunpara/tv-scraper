"""DataValidator singleton for validating exchanges, indicators, timeframes, etc."""

import json
import logging
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tv_scraper.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DataValidator:
    """Singleton validator that loads validation data once from JSON files.

    Usage::

        validator = DataValidator()
        validator.validate_exchange("BINANCE")  # True
        validator.validate_exchange("TYPO")     # raises ValidationError
    """

    _instance: Optional["DataValidator"] = None

    def __new__(cls) -> "DataValidator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self) -> None:
        """Load all JSON data files from tv_scraper/data/."""
        self._exchanges: List[str] = self._load_json("exchanges.json").get("exchanges", [])
        self._indicators: List[str] = self._load_json("indicators.json").get("indicators", [])
        self._timeframes: Dict[str, Any] = self._load_json("timeframes.json").get("indicators", {})
        self._languages: Dict[str, str] = self._load_json("languages.json")
        self._areas: Dict[str, str] = self._load_json("areas.json")
        self._news_providers: List[str] = self._load_json("news_providers.json").get("providers", [])

    @staticmethod
    def _load_json(filename: str) -> Dict[str, Any]:
        """Load a JSON file from the data directory.

        Args:
            filename: Name of the JSON file to load.

        Returns:
            Parsed JSON content as a dict.
        """
        path = _DATA_DIR / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("Error loading data file %s: %s", path, e)
            return {}

    def validate_exchange(self, exchange: str) -> bool:
        """Validate exchange exists.

        Args:
            exchange: Exchange name to validate.

        Returns:
            True if exchange is valid.

        Raises:
            ValidationError: If exchange is not found, with suggestions.
        """
        if exchange.upper() in (e.upper() for e in self._exchanges):
            return True
        suggestions = get_close_matches(exchange.upper(), self._exchanges, n=5, cutoff=0.6)
        suggestion_str = f" Did you mean one of: {', '.join(suggestions)}?" if suggestions else ""
        sample = ", ".join(self._exchanges[:10])
        raise ValidationError(
            f"Invalid exchange: '{exchange}'.{suggestion_str} "
            f"Valid exchanges include: {sample}, ..."
        )

    def validate_symbol(self, exchange: str, symbol: str) -> bool:
        """Validate symbol is a non-empty string.

        Args:
            exchange: Exchange name (for context in error messages).
            symbol: Symbol to validate.

        Returns:
            True if symbol is valid.

        Raises:
            ValidationError: If symbol is empty or not a string.
        """
        if not symbol or not isinstance(symbol, str) or not symbol.strip():
            raise ValidationError(
                f"Symbol must be a non-empty string for exchange '{exchange}'."
            )
        return True

    def validate_indicators(self, indicators: List[str]) -> bool:
        """Validate all indicators exist in known list.

        Args:
            indicators: List of indicator names to validate.

        Returns:
            True if all indicators are valid.

        Raises:
            ValidationError: If any indicator is invalid or list is empty.
        """
        if not indicators:
            raise ValidationError("No indicators provided. Provide at least one indicator.")
        for indicator in indicators:
            if indicator not in self._indicators:
                suggestions = get_close_matches(indicator, self._indicators, n=3, cutoff=0.5)
                suggestion_str = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                raise ValidationError(
                    f"Invalid indicator: '{indicator}'.{suggestion_str}"
                )
        return True

    def validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe is supported.

        Args:
            timeframe: Timeframe string to validate (e.g. '1d', '1h').

        Returns:
            True if timeframe is valid.

        Raises:
            ValidationError: If timeframe is not supported.
        """
        if timeframe in self._timeframes:
            return True
        valid = ", ".join(self._timeframes.keys())
        raise ValidationError(
            f"Invalid timeframe: '{timeframe}'. Valid timeframes: {valid}"
        )

    def validate_choice(self, field_name: str, value: str, allowed: Set[str]) -> bool:
        """Generic validator for choice fields.

        Args:
            field_name: Name of the field being validated (for error messages).
            value: Value to check.
            allowed: Set of allowed values.

        Returns:
            True if value is in allowed set.

        Raises:
            ValidationError: If value is not in allowed set.
        """
        if value in allowed:
            return True
        raise ValidationError(
            f"Invalid {field_name}: '{value}'. Allowed values: {', '.join(sorted(allowed))}"
        )

    def validate_fields(self, fields: List[str], allowed: List[str], field_name: str = "fields") -> bool:
        """Validate a list of fields against allowed values.

        Args:
            fields: List of field names to validate.
            allowed: List of allowed field names.
            field_name: Name for error messages (default: "fields").

        Returns:
            True if all fields are valid.

        Raises:
            ValidationError: If any field is not in allowed list.
        """
        allowed_set = set(allowed)
        invalid = [f for f in fields if f not in allowed_set]
        if invalid:
            raise ValidationError(
                f"Invalid {field_name}: {', '.join(invalid)}. "
                f"Allowed {field_name}: {', '.join(sorted(allowed_set))}"
            )
        return True

    def get_exchanges(self) -> List[str]:
        """Return list of all valid exchanges."""
        return list(self._exchanges)

    def get_indicators(self) -> List[str]:
        """Return list of all valid indicators."""
        return list(self._indicators)

    def get_timeframes(self) -> Dict[str, Any]:
        """Return timeframe mappings."""
        return dict(self._timeframes)

    def get_news_providers(self) -> List[str]:
        """Return list of all valid news providers."""
        return list(self._news_providers)

    def get_languages(self) -> Dict[str, str]:
        """Return language name-to-code mappings."""
        return dict(self._languages)

    def get_areas(self) -> Dict[str, str]:
        """Return area name-to-code mappings."""
        return dict(self._areas)

    @classmethod
    def reset(cls) -> None:
        """Reset singleton for testing."""
        cls._instance = None
