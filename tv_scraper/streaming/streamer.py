"""Main Streamer class (DEPRECATED).

.. deprecated:: 1.4.0
    Use :class:`tv_scraper.streaming.CandleStreamer` or
    :class:`tv_scraper.streaming.ForecastStreamer` instead.
"""

import logging
import warnings
from collections.abc import Generator
from typing import Any

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.core.validation_data import (
    EXCHANGE_LITERAL,
    TIMEFRAME_LITERAL,
)
from tv_scraper.streaming.base_streamer import BaseStreamer
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.forecast_streamer import ForecastStreamer
from tv_scraper.streaming.utils import (
    fetch_available_indicators,
)

logger = logging.getLogger(__name__)


class Streamer(BaseStreamer):
    """Stream OHLCV candles, indicators, forecast data, and realtime prices (DEPRECATED).

    .. deprecated:: 1.4.0
        This class is deprecated and will be removed in a future version.
        Please use :class:`CandleStreamer` for OHLCV, indicators, and realtime prices,
        or :class:`ForecastStreamer` for forecast data.

    Args:
        export_result: Whether to export data to file after retrieval.
        export_type: Export format — ``"json"`` or ``"csv"``.
        cookie: TradingView session cookies for session authentication and
            indicator access. If not provided, unauthenticated access is used.
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        cookie: str | None = None,
    ) -> None:
        warnings.warn(
            "Streamer is deprecated and will be removed in a future version. "
            "Use CandleStreamer or ForecastStreamer instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            cookie=cookie,
        )
        self._candle_streamer = CandleStreamer(
            export_result=export_result,
            export_type=export_type,
            cookie=self.cookie,
        )
        self._forecast_streamer = ForecastStreamer(
            export_result=export_result,
            export_type=export_type,
            cookie=self.cookie,
        )

    @catch_errors
    def get_candles(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        timeframe: TIMEFRAME_LITERAL = "1m",
        numb_candles: int = 10,
        indicators: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Fetch OHLCV candle data and optional indicator values.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Symbol name (e.g. ``"BTCUSDT"``).
            timeframe: Candle timeframe (e.g. ``"1m"``, ``"1h"``, ``"1d"``).
            numb_candles: Number of candles to retrieve.
            indicators: Optional list of ``(script_id, script_version)`` tuples.

        Returns:
            Standardized response dict with
            ``{"status", "data": {"ohlcv": [...], "indicators": {...}}, "metadata", "error"}``.
        """
        result = self._candle_streamer.get_candles(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            numb_candles=numb_candles,
            indicators=indicators,
        )
        if self.export_result and result.get("status") == STATUS_SUCCESS:
            self._export(result["data"], symbol, "get_candles")
        return result

    @catch_errors
    def get_forecast(self, exchange: EXCHANGE_LITERAL, symbol: str) -> dict[str, Any]:
        """Capture forecast data via TradingView WebSocket quote stream.

        This method captures qsd packets until all required forecast fields are
        received, then provides a merged snapshot. It mirrors the persistent
        WebSocket approach used by candle/price streaming.

        The method runs until:
        - All required forecast fields are received (success), OR
        - WebSocket connection closes (returns partial data if any).

        Args:
            exchange: Exchange name (e.g. ``"NYSE"``).
            symbol: Symbol name (e.g. ``"A"``).

        Returns:
            Standardized response dict with
            ``{"status", "data", "metadata", "error"}``.
            ``data`` contains ``raw_packets`` and merged ``snapshot``.
        """
        result = self._forecast_streamer.get_forecast(exchange=exchange, symbol=symbol)
        if self.export_result and result.get("status") == STATUS_SUCCESS:
            self._export(result["data"], symbol, "forecast")
        return result

    def stream_realtime_price(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Persistent generator yielding normalized realtime price updates.

        Yields ``qsd`` (quote session data) and ``du`` (data update) packets
        as normalised dicts::

            {"exchange": ..., "symbol": ..., "price": ..., "volume": ...,
             "change": ..., "change_percent": ..., ...}

        Args:
            exchange: Exchange name.
            symbol: Symbol name.

        Yields:
            Normalised price update dicts.
        """
        yield from self._candle_streamer.stream_realtime_price(
            exchange=exchange, symbol=symbol
        )

    @staticmethod
    def get_available_indicators() -> dict[str, Any]:
        """Fetch available built-in indicators with standardized response envelope.

        Use this to find the correct `id` (e.g. ``"STD;RSI"``) and `version`
        to use with :meth:`get_candles`.

        Returns:
            Standardized response dict with
            ``{"status", "data", "metadata", "error"}``.
        """

        return fetch_available_indicators()
