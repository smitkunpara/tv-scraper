"""Main Streamer class for candle + indicator streaming and realtime price.

Provides ``get_candles()`` for historical OHLC + indicator data and
``stream_realtime_price()`` for continuous quote updates.
"""

import json
import logging
import re
from typing import Generator, List, Optional, Tuple

from websocket import WebSocketConnectionClosedException

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS, EXPORT_TYPES
from tv_scraper.streaming.stream_handler import StreamHandler
from tv_scraper.streaming.utils import fetch_indicator_metadata, validate_symbols
from tv_scraper.utils.helpers import format_symbol
from tv_scraper.utils.io import generate_export_filepath, save_csv_file, save_json_file

logger = logging.getLogger(__name__)

# Timeframe mapping: user-friendly → TradingView protocol value
_TIMEFRAME_MAP = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "1d": "1D",
    "1w": "1W",
    "1M": "1M",
}


def _success_response(data, **metadata):
    """Build a standardized success response."""
    return {
        "status": STATUS_SUCCESS,
        "data": data,
        "metadata": metadata,
        "error": None,
    }


def _error_response(error: str, **metadata):
    """Build a standardized error response."""
    return {
        "status": STATUS_FAILED,
        "data": None,
        "metadata": metadata,
        "error": error,
    }


class Streamer:
    """Stream OHLC candles, indicators, and realtime prices from TradingView.

    Args:
        export_result: Whether to export data to file after retrieval.
        export_type: Export format — ``"json"`` or ``"csv"``.
        websocket_jwt_token: JWT token for authenticated indicator access.
    """

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        websocket_jwt_token: str = "unauthorized_user_token",
    ) -> None:
        if export_type not in EXPORT_TYPES:
            raise ValueError(
                f"Invalid export_type: '{export_type}'. "
                f"Supported types: {', '.join(sorted(EXPORT_TYPES))}"
            )
        self.export_result = export_result
        self.export_type = export_type
        self.study_id_to_name_map: dict = {}
        self._handler = StreamHandler(jwt_token=websocket_jwt_token)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: str = "1m",
        numb_candles: int = 10,
        indicators: Optional[List[Tuple[str, str]]] = None,
    ) -> dict:
        """Fetch OHLC candle data and optional indicator values.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Symbol name (e.g. ``"BTCUSDT"``).
            timeframe: Candle timeframe (e.g. ``"1m"``, ``"1h"``, ``"1d"``).
            numb_candles: Number of candles to retrieve.
            indicators: Optional list of ``(script_id, script_version)`` tuples.

        Returns:
            Standardized response dict with
            ``{"status", "data": {"ohlc": [...], "indicators": {...}}, "metadata", "error"}``.
        """
        try:
            exchange_symbol = format_symbol(exchange, symbol)
            validate_symbols(exchange, symbol)

            ind_flag = bool(indicators)

            self._add_symbol_to_sessions(
                self._handler.quote_session,
                self._handler.chart_session,
                exchange_symbol,
                timeframe,
                numb_candles,
            )

            if ind_flag and indicators:
                self._add_indicators(indicators)

            ohlc_data: list = []
            indicator_data: dict = {}
            expected_ind_count = len(indicators) if ind_flag and indicators else 0

            for i, pkt in enumerate(self._get_data()):
                # OHLC extraction
                received_ohlc = self._extract_ohlc_from_stream(pkt)
                if received_ohlc:
                    ohlc_data = received_ohlc

                # Indicator extraction
                received_ind = self._extract_indicator_from_stream(pkt)
                if received_ind:
                    indicator_data.update(received_ind)

                # Stop conditions
                ohlc_ready = len(ohlc_data) >= numb_candles
                ind_ready = not ind_flag or len(indicator_data) >= expected_ind_count
                if ohlc_ready and ind_ready:
                    break
                if i > 15:
                    logger.warning(
                        "Timeout after %d packets. OHLC=%d, Indicators=%d",
                        i, len(ohlc_data), len(indicator_data),
                    )
                    break

            result_data = {"ohlc": ohlc_data, "indicators": indicator_data}

            if self.export_result:
                self._export(ohlc_data, symbol, "ohlc")
                if ind_flag:
                    self._export(indicator_data, symbol, "indicator")

            return _success_response(
                result_data,
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                numb_candles=numb_candles,
            )

        except Exception as exc:
            logger.error("get_candles error: %s", exc)
            return _error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
            )

    def stream(
        self,
        exchange: str,
        symbol: str,
        timeframe: str = "1m",
        numb_candles: int = 10,
        indicators: Optional[List[Tuple[str, str]]] = None,
    ) -> dict:
        """Compatibility alias for :meth:`get_candles`."""
        return self.get_candles(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            numb_candles=numb_candles,
            indicators=indicators,
        )

    def stream_realtime_price(
        self,
        exchange: str,
        symbol: str,
    ) -> Generator[dict, None, None]:
        """Persistent generator yielding normalized realtime price updates.

        Yields ``qsd`` (quote session data) packets as normalised dicts::

            {"exchange": ..., "symbol": ..., "price": ..., "volume": ...,
             "change": ..., "change_percent": ..., ...}

        Args:
            exchange: Exchange name.
            symbol: Symbol name.

        Yields:
            Normalised price update dicts.
        """
        exchange_symbol = format_symbol(exchange, symbol)
        validate_symbols(exchange, symbol)

        # Add symbol to quote session for realtime updates
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        qs = self._handler.quote_session
        self._handler.send_message("quote_add_symbols", [qs, f"={resolve_symbol}"])
        self._handler.send_message("quote_fast_symbols", [qs, exchange_symbol])

        for pkt in self._get_data():
            if pkt.get("m") == "qsd":
                p_data = pkt.get("p", [])
                if len(p_data) > 1 and isinstance(p_data[1], dict):
                    v = p_data[1].get("v", {})
                    yield {
                        "exchange": v.get("exchange", exchange),
                        "symbol": v.get("short_name", symbol),
                        "price": v.get("lp"),
                        "volume": v.get("volume"),
                        "change": v.get("ch"),
                        "change_percent": v.get("chp"),
                    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_data(self) -> Generator[dict, None, None]:
        """Receive and parse WebSocket data, handling heartbeats.

        Yields:
            Parsed JSON packets from the TradingView stream.
        """
        try:
            while True:
                try:
                    raw_result = self._handler.ws.recv()
                    if isinstance(raw_result, bytes):
                        result = raw_result.decode("utf-8")
                    else:
                        result = str(raw_result)

                    # Heartbeat echo
                    if re.match(r"~m~\d+~m~~h~\d+$", result):
                        logger.debug("Heartbeat: %s", result)
                        self._handler.ws.send(result)
                        continue

                    # Split multiplexed messages
                    parts = [x for x in re.split(r"~m~\d+~m~", result) if x]
                    for part in parts:
                        try:
                            yield json.loads(part)
                        except (json.JSONDecodeError, ValueError):
                            logger.debug("Non-JSON fragment skipped: %s", part[:80])

                except WebSocketConnectionClosedException:
                    logger.error("WebSocket connection closed.")
                    break
                except (ConnectionError, TimeoutError, OSError) as exc:
                    logger.error("WebSocket error: %s", exc)
                    break
        finally:
            try:
                self._handler.ws.close()
            except Exception:
                pass

    def _add_symbol_to_sessions(
        self,
        quote_session: str,
        chart_session: str,
        exchange_symbol: str,
        timeframe: str = "1m",
        numb_candles: int = 10,
    ) -> None:
        """Register symbol in both quote and chart sessions."""
        mapped_tf = _TIMEFRAME_MAP.get(timeframe, "1")
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        self._handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        self._handler.send_message(
            "resolve_symbol", [chart_session, "sds_sym_1", f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "create_series",
            [chart_session, "sds_1", "s1", "sds_sym_1", mapped_tf, numb_candles, ""],
        )
        self._handler.send_message("quote_fast_symbols", [quote_session, exchange_symbol])

    def _add_indicators(self, indicators: List[Tuple[str, str]]) -> None:
        """Add one or more indicator studies to the chart session."""
        for idx, (script_id, script_version) in enumerate(indicators):
            logger.info("Processing indicator %d/%d: %s v%s", idx + 1, len(indicators), script_id, script_version)

            ind_study = fetch_indicator_metadata(
                script_id=script_id,
                script_version=script_version,
                chart_session=self._handler.chart_session,
            )
            if not ind_study or "p" not in ind_study:
                logger.error("Failed to fetch metadata for %s v%s", script_id, script_version)
                continue

            study_id = f"st{9 + idx}"
            ind_study["p"][1] = study_id
            self.study_id_to_name_map[study_id] = script_id

            try:
                self._handler.send_message("create_study", ind_study["p"])
                self._handler.send_message("quote_hibernate_all", [self._handler.quote_session])
            except Exception as exc:
                logger.error("Failed to add indicator %s: %s", script_id, exc)

    def _serialize_ohlc(self, raw_data: dict) -> list:
        """Extract OHLC entries from a timescale_update packet."""
        ohlc_entries = raw_data.get("p", [{}, {}])[1].get("sds_1", {}).get("s", [])
        result = []
        for entry in ohlc_entries:
            rec = {
                "index": entry["i"],
                "timestamp": entry["v"][0],
                "open": entry["v"][1],
                "high": entry["v"][2],
                "low": entry["v"][3],
                "close": entry["v"][4],
            }
            if len(entry["v"]) > 5:
                rec["volume"] = entry["v"][5]
            result.append(rec)
        return result

    def _extract_ohlc_from_stream(self, pkt: dict) -> list:
        """Extract OHLC from a packet if it's a timescale_update."""
        if pkt.get("m") == "timescale_update":
            return self._serialize_ohlc(pkt)
        return []

    def _extract_indicator_from_stream(self, pkt: dict) -> dict:
        """Extract indicator data from a ``du`` packet."""
        indicator_data: dict = {}
        if pkt.get("m") != "du":
            return indicator_data

        p_data = pkt.get("p", [])
        if len(p_data) <= 1 or not isinstance(p_data[1], dict):
            return indicator_data

        for key, val in p_data[1].items():
            if key.startswith("st") and key in self.study_id_to_name_map:
                if "st" in val and len(val["st"]) > 10:
                    indicator_name = self.study_id_to_name_map[key]
                    json_data = []
                    for item in val["st"]:
                        tmp = {"index": item["i"], "timestamp": item["v"][0]}
                        tmp.update({str(i): v for i, v in enumerate(item["v"][1:])})
                        json_data.append(tmp)
                    indicator_data[indicator_name] = json_data

        return indicator_data

    def _export(self, data, symbol: str, data_category: str) -> None:
        """Export data to file."""
        filepath = generate_export_filepath(symbol, data_category, self.export_type)
        if self.export_type == "csv":
            save_csv_file(data, filepath)
        else:
            save_json_file(data, filepath)
