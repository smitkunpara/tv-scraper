"""Scanner scraper class for tv_scraper."""

import logging
from typing import Any, cast

from tv_scraper.core.base import BaseScraper, catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.validation_data import EXCHANGE_LITERAL
from tv_scraper.core.validators import verify_symbol_exchange

logger = logging.getLogger(__name__)


class ScannerScraper(BaseScraper):
    """Base class for scrapers that utilize the TradingView scanner API."""

    @catch_errors
    def _fetch_symbol_fields(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        fields: list[str],
        data_category: str,
    ) -> dict[str, Any]:
        """Fetch field values for a symbol from the TradingView scanner API.

        This is a shared implementation for scrapers that query the
        ``GET /symbol`` endpoint with a flat field list (e.g.
        Fundamentals).

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            fields: List of field names to retrieve.
            data_category: Category prefix for export filenames.

        Returns:
            Standardized response dict.
        """
        exchange, symbol = verify_symbol_exchange(exchange, symbol)

        url = f"{SCANNER_URL}/symbol"
        params: dict[str, str] = {
            "symbol": f"{exchange}:{symbol}",
            "fields": ",".join(fields),
            "no_404": "true",
        }

        json_response, error_msg = self._request("GET", url, params=params)

        if error_msg:
            return self._error_response(error_msg)

        if not json_response:
            return self._error_response("No data returned from API.")

        error_indicator = (
            json_response.get("error") or json_response.get("s") == "error"
        )
        if error_indicator:
            errmsg = json_response.get("errmsg", "Unknown API error")
            return self._error_response(f"API error: {errmsg}")

        result: dict[str, Any] = {"symbol": f"{exchange}:{symbol}"}
        for field in fields:
            value = json_response.get(field)
            if value is None:
                logger.warning(
                    "Field '%s' not found in response for %s:%s",
                    field,
                    exchange,
                    symbol,
                )
            result[field] = value

        if self.export_result:
            self._export(
                data=result,
                symbol=f"{exchange}_{symbol}",
                data_category=data_category,
            )

        return self._success_response(result)

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
