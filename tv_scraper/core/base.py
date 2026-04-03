"""Base scraper class for tv_scraper."""

import logging
from typing import Any

import requests

from tv_scraper.core.constants import DEFAULT_TIMEOUT, STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.utils.helpers import generate_user_agent
from tv_scraper.utils.io import generate_export_filepath, save_csv_file, save_json_file

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers providing common functionality.

    Provides standardized response envelopes, HTTP request handling,
    data export, and access to the shared DataValidator.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = DEFAULT_TIMEOUT,
        cookie: str | None = None,
    ) -> None:
        from tv_scraper.core.constants import EXPORT_TYPES

        if export_type not in EXPORT_TYPES:
            raise ValueError(
                f"Invalid export_type: '{export_type}'. "
                f"Supported types: {', '.join(sorted(EXPORT_TYPES))}"
            )
        self.export_result = export_result
        self.export_type = export_type
        self.timeout = timeout
        import os

        self.cookie = cookie or os.environ.get("TRADINGVIEW_COOKIE")
        self.validator = DataValidator()
        self._headers: dict[str, str] = {"User-Agent": generate_user_agent()}
        if self.cookie:
            self._headers["cookie"] = self.cookie

    def _success_response(self, data: Any, **metadata: Any) -> dict[str, Any]:
        """Build a standardized success response.

        Args:
            data: The response payload.
            **metadata: Arbitrary metadata key-value pairs.

        Returns:
            Response dict with status, data, metadata, and error fields.
        """
        return {
            "status": STATUS_SUCCESS,
            "data": data,
            "metadata": metadata,
            "error": None,
        }

    def _error_response(self, error: str, **metadata: Any) -> dict[str, Any]:
        """Build a standardized error response.

        Args:
            error: Error message string.
            **metadata: Arbitrary metadata key-value pairs.

        Returns:
            Response dict with status="failed", data=None, and error message.
        """
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": metadata,
            "error": error,
        }

    def _export(
        self,
        data: Any,
        symbol: str,
        data_category: str,
        timeframe: str | None = None,
    ) -> None:
        """Export data if export_result is True.

        Args:
            data: Data to export.
            symbol: Symbol name for the filename.
            data_category: Category prefix for the filename.
            timeframe: Optional timeframe suffix.
        """
        if not self.export_result:
            return
        filepath = generate_export_filepath(
            symbol, data_category, self.export_type, timeframe
        )
        if self.export_type == "csv":
            save_csv_file(data, filepath)
        else:
            save_json_file(data, filepath)

    def _fetch_symbol_fields(
        self,
        exchange: str,
        symbol: str,
        fields: list[str],
        data_category: str,
    ) -> dict[str, Any]:
        """Fetch field values for a symbol from the TradingView scanner API.

        This is a shared implementation for scrapers that query the
        ``GET /symbol`` endpoint with a flat field list (e.g. Overview,
        Fundamentals).

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            fields: List of field names to retrieve.
            data_category: Category prefix for export filenames.

        Returns:
            Standardized response dict.
        """
        from tv_scraper.core.constants import SCANNER_URL
        from tv_scraper.core.exceptions import ValidationError

        try:
            self.validator.verify_symbol_exchange(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(str(exc))

        url = f"{SCANNER_URL}/symbol"
        params: dict[str, str] = {
            "symbol": f"{exchange}:{symbol}",
            "fields": ",".join(fields),
            "no_404": "true",
        }

        try:
            response = requests.get(
                url, headers=self._headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            json_response: dict[str, Any] = response.json()
        except requests.RequestException as exc:
            return self._error_response(f"Network error: {exc}")
        except (ValueError, KeyError) as exc:
            return self._error_response(f"Failed to parse API response: {exc}")

        if not json_response:
            return self._error_response("No data returned from API.")

        result: dict[str, Any] = {"symbol": f"{exchange}:{symbol}"}
        for field in fields:
            result[field] = json_response.get(field)

        if self.export_result:
            self._export(
                data=result,
                symbol=f"{exchange}_{symbol}",
                data_category=data_category,
            )

        return self._success_response(
            result,
            exchange=exchange,
            symbol=symbol,
        )

    def _map_scanner_rows(
        self, items: list[dict[str, Any]], fields: list[str]
    ) -> list[dict[str, Any]]:
        """Map TradingView scanner response rows to field-named dicts.

        Scanner API returns items like ``{"s": "EXCHANGE:SYMBOL", "d": [val1, val2, ...]}``.
        This maps the ``d`` values to their corresponding field names.

        Args:
            items: List of scanner response items.
            fields: List of field names matching the ``d`` array positions.

        Returns:
            List of dicts with ``symbol`` key and field-named values.
        """
        result: list[dict[str, Any]] = []
        for item in items:
            row: dict[str, Any] = {"symbol": item.get("s", "")}
            values = item.get("d", [])
            for i, field in enumerate(fields):
                row[field] = values[i] if i < len(values) else None
            result.append(row)
        return result
