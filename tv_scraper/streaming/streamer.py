"""Main Streamer class for candle + indicator streaming and realtime price.

Provides ``get_candles()`` for historical OHLCV + indicator data,
``get_forecast()`` for forecast data, and ``stream_realtime_price()``
for continuous quote updates.
"""

import json
import logging
from collections.abc import Generator
from typing import Any

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.streaming.candle_streamer import CandleStreamer
from tv_scraper.streaming.forecast_streamer import ForecastStreamer
from tv_scraper.streaming.stream_handler import StreamHandler
from tv_scraper.streaming.utils import (
    fetch_available_indicators,
)

logger = logging.getLogger(__name__)


class Streamer(BaseScraper):
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
        result = self._forecast_streamer.get_forecast(
            exchange=exchange, symbol=symbol)
        if self.export_result and result.get("status") == STATUS_SUCCESS:
            self._export(result["data"], symbol, "forecast")
        return result

    def stream_realtime_price(
        self,
        exchange: str,
        symbol: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream realtime price updates for a single symbol.

        Convenience wrapper around :meth:`stream_realtime_prices`.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Symbol name (e.g. ``"BTCUSDT"``).

        Yields:
            Normalised price update dicts.
        """
        yield from self.stream_realtime_prices([f"{exchange}:{symbol}"])

    def stream_realtime_prices(
        self,
        symbols: list[str],
    ) -> Generator[dict[str, Any], None, None]:
        """Persistent generator yielding normalized realtime price updates.

        Supports single or multiple symbols. Each symbol must be in
        ``"EXCHANGE:SYMBOL"`` format (e.g. ``"BINANCE:BTCUSDT"``).

        For a single symbol, ``du`` (data update) packets are also yielded
        alongside ``qsd`` packets. For multiple symbols only ``qsd`` packets
        are processed.

        Args:
            symbols: List of symbols in ``"EXCHANGE:SYMBOL"`` format.

        Yields:
            Normalised price update dicts.
        """
        symbol_map = {}
        for s in symbols:
            ex, sym = s.split(":", 1)
            symbol_map[s] = (ex, sym)

        handler = self._get_fresh_handler()
        qs = handler.quote_session
        single = len(symbols) == 1

        self._subscribe_symbols(handler, qs, symbols)

        if single:
            cs = handler.chart_session
            resolve = json.dumps(
                {"adjustment": "splits", "symbol": symbols[0]})
            mapped_tf = DataValidator().get_timeframes().get("1m", "1")
            handler.send_message("resolve_symbol", [
                                 cs, "sds_sym_1", f"={resolve}"])
            handler.send_message(
                "create_series", [cs, "sds_1", "s1",
                                  "sds_sym_1", mapped_tf, 1, ""]
            )

        last_prices: dict[str, float] = {}

        for pkt in handler.receive_packets():
            if pkt.get("m") == "qsd":
                result = self._extract_qsd(pkt, symbol_map)
                if result:
                    key = f"{result['exchange']}:{result['symbol']}"
                    last_prices[key] = result["price"]
                    yield result

            elif single and pkt.get("m") == "du":
                p_data = pkt.get("p", [])
                if len(p_data) <= 1 or not isinstance(p_data[1], dict):
                    continue
                ex, sym = symbol_map[symbols[0]]
                last_price = last_prices.get(symbols[0])
                for entry in p_data[1].get("sds_1", {}).get("s", []):
                    if "v" not in entry or len(entry["v"]) < 5:
                        continue
                    v = entry["v"]
                    close_price = v[4]
                    change = None
                    change_pct = None
                    if last_price is not None and last_price != 0:
                        change = close_price - last_price
                        change_pct = change / last_price * 100
                    last_price = close_price
                    last_prices[symbols[0]] = close_price
                    yield {
                        "exchange": ex,
                        "symbol": sym,
                        "price": close_price,
                        "volume": v[5] if len(v) > 5 else None,
                        "change": change,
                        "change_percent": change_pct,
                        "high": v[2],
                        "low": v[3],
                        "open": v[1],
                        "prev_close": None,
                        "bid": None,
                        "ask": None,
                    }

    def _subscribe_symbols(
        self, handler: StreamHandler, qs: str, symbols: list[str]
    ) -> None:
        first = symbols[0]
        resolve = json.dumps(
            {
                "adjustment": "splits",
                "currency-id": "USD",
                "session": "regular",
                "symbol": first,
            }
        )
        handler.send_message("quote_add_symbols", [qs, f"={resolve}"])
        handler.send_message("quote_fast_symbols", [qs, f"={resolve}"])
        handler.send_message("quote_add_symbols", [qs, *symbols])
        handler.send_message("quote_fast_symbols", [qs, *symbols])

    @staticmethod
    def _extract_qsd(
        pkt: dict[str, Any], symbol_map: dict[str, tuple[str, str]]
    ) -> dict[str, Any] | None:
        p_data = pkt.get("p", [])
        if len(p_data) <= 1 or not isinstance(p_data[1], dict):
            return None
        v = p_data[1].get("v", {})
        price = v.get("lp")
        if price is None:
            return None
        n = p_data[1].get("n", "")
        ex, sym = symbol_map.get(n, ("", ""))
        return {
            "exchange": v.get("exchange", ex),
            "symbol": v.get("short_name", sym),
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

    def _get_fresh_handler(self) -> StreamHandler:
        """Resolve a valid JWT token and return a new connected StreamHandler."""
        from tv_scraper.streaming.auth import get_valid_jwt_token

        websocket_jwt_token = "unauthorized_user_token"
        if self.cookie:
            try:
                websocket_jwt_token = get_valid_jwt_token(self.cookie)
                logger.debug("JWT token resolved successfully.")
            except Exception as exc:
                logger.error(
                    "Failed to resolve JWT token from cookie: %s", exc)
                raise

        return StreamHandler(jwt_token=websocket_jwt_token)

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
