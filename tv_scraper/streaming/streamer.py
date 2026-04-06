"""Main Streamer class for candle + indicator streaming and realtime price.

Provides ``get_candles()`` for historical OHLCV + indicator data,
``get_forecast()`` for forecast data, and ``stream_realtime_price()``
for continuous quote updates.
"""

import json
import logging
from collections.abc import Generator
from typing import Any

from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.streaming.base_streamer import BaseStreamer
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.forecast_streamer import ForecastStreamer
from tv_scraper.streaming.utils import (
    fetch_available_indicators,
)
from tv_scraper.utils.helpers import format_symbol

logger = logging.getLogger(__name__)


class Streamer(BaseStreamer):
    """Stream OHLCV candles, indicators, forecast data, and realtime prices from TradingView.

    This class combines all streaming functionality in a single convenient interface.
    For more granular control, use ``CandleStreamer`` or ``ForecastStreamer`` directly.

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

    def get_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: str = "1m",
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

    def get_forecast(self, exchange: str, symbol: str) -> dict[str, Any]:
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
        exchange: str,
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
        exchange_symbol = format_symbol(exchange, symbol)
        DataValidator().verify_symbol_exchange(exchange, symbol)

        handler = self.connect()

        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        qs = handler.quote_session
        cs = handler.chart_session

        handler.send_message("quote_add_symbols", [qs, f"={resolve_symbol}"])
        handler.send_message("quote_fast_symbols", [qs, exchange_symbol])

        mapped_tf = DataValidator().get_timeframes().get("1m", "1")
        handler.send_message("resolve_symbol", [cs, "sds_sym_1", f"={resolve_symbol}"])
        handler.send_message(
            "create_series", [cs, "sds_1", "s1", "sds_sym_1", mapped_tf, 1, ""]
        )

        last_price = None

        for pkt in handler.receive_packets():
            if pkt.get("m") == "qsd":
                p_data = pkt.get("p", [])
                if len(p_data) > 1 and isinstance(p_data[1], dict):
                    v = p_data[1].get("v", {})
                    price = v.get("lp")
                    if price is not None:
                        last_price = price
                        yield {
                            "exchange": v.get("exchange", exchange),
                            "symbol": v.get("short_name", symbol),
                            "price": price,
                            "volume": v.get("volume"),
                            "change": v.get("ch"),
                            "change_percent": v.get("chp"),
                            "high": v.get("high_price"),
                            "low": v.get("low_price"),
                            "open": v.get("open_price"),
                            "prev_close": v.get("prev_close_price"),
                            "bid": v.get("bid"),
                            "ask": v.get("ask"),
                        }

            elif pkt.get("m") == "du":
                p_data = pkt.get("p", [])
                if len(p_data) > 1 and isinstance(p_data[1], dict):
                    sds_data = p_data[1].get("sds_1", {})
                    series = sds_data.get("s", [])

                    for entry in series:
                        if "v" in entry and len(entry["v"]) >= 5:
                            close_price = entry["v"][4]
                            volume = entry["v"][5] if len(entry["v"]) > 5 else None

                            change = None
                            change_percent = None
                            if last_price is not None:
                                change = close_price - last_price
                                change_percent = (
                                    (change / last_price * 100)
                                    if last_price != 0
                                    else 0
                                )

                            last_price = close_price

                            yield {
                                "exchange": exchange,
                                "symbol": symbol,
                                "price": close_price,
                                "volume": volume,
                                "change": change,
                                "change_percent": change_percent,
                                "high": entry["v"][2],
                                "low": entry["v"][3],
                                "open": entry["v"][1],
                                "prev_close": None,
                                "bid": None,
                                "ask": None,
                            }

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
