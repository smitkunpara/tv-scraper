"""Technicals scraper for fetching technical analysis indicators."""

import logging
import re
from difflib import get_close_matches
from typing import Any

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import (
    EXCHANGE_LITERAL,
    INDICATOR_LITERAL,
    INDICATORS,
    TIMEFRAME_LITERAL,
    TIMEFRAMES,
)

logger = logging.getLogger(__name__)


class Technicals(ScannerScraper):
    """Scraper for technical analysis indicators from TradingView.

    Fetches indicator values (RSI, MACD, EMA, etc.) for a given symbol
    via the TradingView scanner API.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
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

    def _validate_indicators(self, indicators: list[str]) -> bool:
        if not indicators:
            raise ValidationError(
                "No indicators provided. Provide at least one indicator."
            )
        indicators_set = set(INDICATORS)
        for indicator in indicators:
            if indicator not in indicators_set:
                suggestions = get_close_matches(indicator, INDICATORS, n=3, cutoff=0.5)
                suggestion_str = (
                    f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                )
                raise ValidationError(
                    f"Invalid indicator: '{indicator}'.{suggestion_str}"
                )
        return True

    @catch_errors
    def get_technicals(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        timeframe: TIMEFRAME_LITERAL = "1d",
        technical_indicators: list[INDICATOR_LITERAL] | None = None,
    ) -> dict[str, Any]:
        """Scrape technical indicator values for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Trading symbol slug (e.g. ``"NIFTY"``).
            timeframe: Timeframe string (e.g. ``"1d"``, ``"4h"``, ``"1w"``).
            technical_indicators: Optional list of indicator names to fetch.
                If ``None``, all known indicators are fetched.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """

        # --- Validation ---
        # All local validations first (before any network calls)
        self._validate_timeframe(timeframe)
        if technical_indicators is None:
            indicators = list(INDICATORS)
        else:
            indicators = [str(ind) for ind in technical_indicators]
            self._validate_indicators(indicators)

        # Symbol/exchange verification (includes static and live checks)
        v_exchange, v_symbol = self._verify_symbol_exchange(exchange, symbol)

        # --- Build API request ---
        timeframe_value: str = TIMEFRAMES.get(timeframe, "")

        # Scanner API expects no suffix for daily indicators regardless of timeframe mapping
        if timeframe_value and timeframe_value != "1D":
            api_indicators = [f"{ind}|{timeframe_value}" for ind in indicators]
        else:
            api_indicators = indicators

        # Build query parameters for GET request
        fields_param = ",".join(api_indicators)

        params: dict[str, str] = {
            "symbol": f"{v_exchange}:{v_symbol}",
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
            return self._error_response(error_msg)

        assert json_response is not None

        # --- Parse response ---
        # API returns indicators directly as a dict, not wrapped in "data"
        if not json_response:
            return self._error_response(
                f"Empty response for {exchange}:{symbol} with timeframe {timeframe}. "
                "This may indicate an invalid symbol or no data available for the requested timeframe."
            )

        result: dict[str, Any] = {}
        # Map requested indicators to response values
        for ind in api_indicators:
            result[ind] = json_response.get(ind)

        # Strip timeframe suffix from keys
        result = self._revise_response(result, timeframe_value)

        # --- Export ---
        if self.export_result:
            self._export(
                data=result,
                symbol=f"{v_exchange}_{v_symbol}",
                data_category="technicals",
                timeframe=timeframe,
            )

        return self._success_response(result)

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
