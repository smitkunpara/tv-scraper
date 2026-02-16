"""Base scraper class for tv_scraper."""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import requests

from tv_scraper.core.constants import DEFAULT_TIMEOUT, STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.utils.helpers import generate_user_agent
from tv_scraper.utils.http import make_request
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
        self.validator = DataValidator()
        self._headers: Dict[str, str] = {"User-Agent": generate_user_agent()}

    def _success_response(self, data: Any, **metadata: Any) -> Dict[str, Any]:
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

    def _error_response(self, error: str, **metadata: Any) -> Dict[str, Any]:
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

    def _make_request(self, url: str, method: str = "GET", **kwargs: Any) -> "requests.Response":
        """Make an HTTP request with default headers and timeout.

        Args:
            url: The URL to request.
            method: HTTP method.
            **kwargs: Additional keyword arguments passed to ``make_request``.

        Returns:
            The HTTP response.

        Raises:
            NetworkError: If the request fails.
        """
        # Set defaults if not in kwargs
        kwargs.setdefault("headers", self._headers)
        kwargs.setdefault("timeout", self.timeout)

        return make_request(
            url,
            method=method,
            **kwargs,
        )

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
        filepath = generate_export_filepath(symbol, data_category, self.export_type, timeframe)
        if self.export_type == "csv":
            save_csv_file(data, filepath)
        else:
            save_json_file(data, filepath)

    def _map_scanner_rows(self, items: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
        """Map TradingView scanner response rows to field-named dicts.

        Scanner API returns items like ``{"s": "EXCHANGE:SYMBOL", "d": [val1, val2, ...]}``.
        This maps the ``d`` values to their corresponding field names.

        Args:
            items: List of scanner response items.
            fields: List of field names matching the ``d`` array positions.

        Returns:
            List of dicts with ``symbol`` key and field-named values.
        """
        result: List[Dict[str, Any]] = []
        for item in items:
            row: Dict[str, Any] = {"symbol": item.get("s", "")}
            values = item.get("d", [])
            for i, field in enumerate(fields):
                row[field] = values[i] if i < len(values) else None
            result.append(row)
        return result
