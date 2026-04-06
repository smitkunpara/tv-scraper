"""Technicals scraper for fetching technical analysis indicators."""

import logging
import re
from typing import Any

from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper

logger = logging.getLogger(__name__)


class Technicals(ScannerScraper):
    """Scraper for technical analysis indicators from TradingView.

    Fetches indicator values (RSI, MACD, EMA, etc.) for a given symbol
    via the TradingView scanner API.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.market_data import Technicals

        scraper = Technicals()
        data = scraper.get_technicals(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["RSI", "Stoch.K"],
        )
    """

    def get_technicals(
        self,
        exchange: str,
        symbol: str,
        timeframe: str = "1d",
        technical_indicators: list[str] | None = None,
        all_indicators: bool = False,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Scrape technical indicator values for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Trading symbol slug (e.g. ``"NIFTY"``).
            timeframe: Timeframe string (e.g. ``"1d"``, ``"4h"``, ``"1w"``).
            technical_indicators: List of indicator names to fetch.
                Required unless ``all_indicators=True``.
            all_indicators: If ``True``, fetch all known indicators.
            fields: Optional list of indicator names to include in the
                output (post-fetch filtering).

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """

        # --- Validation ---
        try:
            self.validator.verify_symbol_exchange(exchange, symbol)
            self.validator.validate_timeframe(timeframe)
        except ValidationError as exc:
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
            )

        # Resolve indicator list
        if all_indicators:
            indicators = self.validator.get_indicators()
        elif technical_indicators:
            try:
                self.validator.validate_indicators(technical_indicators)
            except ValidationError as exc:
                return self._error_response(
                    str(exc),
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    technical_indicators=technical_indicators,
                )
            indicators = technical_indicators
        else:
            return self._error_response(
                "No indicators provided. "
                "Use technical_indicators or set all_indicators=True.",
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
            )

        # --- Build API request ---
        timeframes = self.validator.get_timeframes()
        timeframe_value: str = timeframes.get(timeframe, "")

        # Scanner API expects no suffix for daily indicators regardless of timeframe mapping
        if timeframe_value and timeframe_value != "1D":
            api_indicators = [f"{ind}|{timeframe_value}" for ind in indicators]
        else:
            api_indicators = indicators

        # Build query parameters for GET request
        fields_param = ",".join(api_indicators)

        params: dict[str, str] = {
            "symbol": f"{exchange}:{symbol}",
            "fields": fields_param,
            "no_404": "true",
        }

        url = f"{SCANNER_URL}/symbol"

        json_response, error_msg = self._request(
            "GET",
            url,
            params=params,
        )

        if error_msg:
            return self._error_response(
                error_msg,
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
            )

        assert json_response is not None

        # --- Parse response ---
        # API returns indicators directly as a dict, not wrapped in "data"
        if not json_response:
            return self._error_response(
                f"Empty response for {exchange}:{symbol} with timeframe {timeframe}. "
                "This may indicate an invalid symbol or no data available for the requested timeframe.",
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
            )

        result: dict[str, Any] = {}
        # Map requested indicators to response values
        for ind in api_indicators:
            result[ind] = json_response.get(ind)

        # Strip timeframe suffix from keys
        result = self._revise_response(result, timeframe_value)

        # Optional field filtering - strip suffixes from fields to match revised keys
        if fields:
            stripped_fields = [re.sub(r"\|.*", "", f) for f in fields]
            result = {k: v for k, v in result.items() if k in stripped_fields}

        # --- Export ---
        if self.export_result:
            self._export(
                data=result,
                symbol=symbol,
                data_category="technicals",
                timeframe=timeframe,
            )

        tech_meta: dict[str, Any] = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "all_indicators": all_indicators,
        }
        if technical_indicators is not None:
            tech_meta["technical_indicators"] = technical_indicators

        return self._success_response(result, **tech_meta)

    def _revise_response(
        self, data: dict[str, Any], timeframe_value: str
    ) -> dict[str, Any]:
        """Clean indicator key names by stripping timeframe suffixes.

        Args:
            data: Dict with indicator names as keys.
            timeframe_value: The timeframe suffix that was appended
                (e.g. ``"240"`` for 4h). Empty string for daily.

        Returns:
            Dict with cleaned keys (``|suffix`` removed).
        """
        if not timeframe_value or timeframe_value == "1D":
            return data
        return {re.sub(r"\|.*", "", k): v for k, v in data.items()}
