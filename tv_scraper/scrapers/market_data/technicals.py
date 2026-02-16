"""Technicals scraper for fetching technical analysis indicators."""

import re
import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)


class Technicals(BaseScraper):
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
        data = scraper.scrape(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["RSI", "Stoch.K"],
        )
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
        )

    def scrape(
        self,
        exchange: str = "BITSTAMP",
        symbol: str = "BTCUSD",
        timeframe: str = "1d",
        technical_indicators: Optional[List[str]] = None,
        all_indicators: bool = False,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Scrape technical indicator values for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``). Can be empty if
                combined symbol is used in the `symbol` parameter.
            symbol: Trading symbol slug (e.g. ``"NIFTY"``) or combined
                ``"EXCHANGE:SYMBOL"`` string (e.g. ``"NSE:NIFTY"``).
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
        # Support combined EXCHANGE:SYMBOL
        if not exchange and ":" in symbol:
            exchange, symbol = symbol.split(":", 1)

        # --- Validation ---
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
            self.validator.validate_timeframe(timeframe)
        except ValidationError as exc:
            return self._error_response(str(exc))

        # Resolve indicator list
        if all_indicators:
            indicators = self.validator.get_indicators()
        elif technical_indicators:
            try:
                self.validator.validate_indicators(technical_indicators)
            except ValidationError as exc:
                return self._error_response(str(exc))
            indicators = list(technical_indicators)
        else:
            return self._error_response(
                "No indicators provided. "
                "Use technical_indicators or set all_indicators=True."
            )

        # --- Build API request ---
        timeframes = self.validator.get_timeframes()
        timeframe_value: str = timeframes.get(timeframe, "")

        if timeframe_value:
            api_indicators = [f"{ind}|{timeframe_value}" for ind in indicators]
        else:
            api_indicators = list(indicators)

        # Build query parameters for GET request
        fields_param = ",".join(api_indicators)

        params: Dict[str, str] = {
            "symbol": f"{exchange}:{symbol}",
            "fields": fields_param,
            "no_404": "true",
        }

        url = f"{SCANNER_URL}/symbol"

        # --- Execute request ---
        try:
            response = self._make_request(url, method="GET", params=params)
            json_response: Dict[str, Any] = response.json()
        except NetworkError as exc:
            return self._error_response(str(exc))
        except (ValueError, KeyError) as exc:
            return self._error_response(f"Failed to parse API response: {exc}")

        # --- Parse response ---
        # API returns indicators directly as a dict, not wrapped in "data"
        if not json_response:
            return self._error_response("No data returned from API.")

        result: Dict[str, Any] = {}
        # Map requested indicators to response values
        for ind in api_indicators:
            result[ind] = json_response.get(ind)

        # Strip timeframe suffix from keys
        result = self._revise_response(result, timeframe_value)

        # Optional field filtering
        if fields:
            result = {k: v for k, v in result.items() if k in fields}

        # --- Export ---
        if self.export_result:
            self._export(
                data=result,
                symbol=symbol,
                data_category="technicals",
                timeframe=timeframe,
            )

        return self._success_response(
            result,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
        )

    def _revise_response(
        self, data: Dict[str, Any], timeframe_value: str
    ) -> Dict[str, Any]:
        """Clean indicator key names by stripping timeframe suffixes.

        Args:
            data: Dict with indicator names as keys.
            timeframe_value: The timeframe suffix that was appended
                (e.g. ``"240"`` for 4h). Empty string for daily.

        Returns:
            Dict with cleaned keys (``|suffix`` removed).
        """
        if not timeframe_value:
            return data
        return {re.sub(r"\|.*", "", k): v for k, v in data.items()}
