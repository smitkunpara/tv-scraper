"""Main Streamer class for candle + indicator streaming and realtime price.

Provides ``get_candles()`` for historical OHLCV + indicator data and
``stream_realtime_price()`` for continuous quote updates.
"""

import json
import logging
from collections.abc import Generator
from typing import Any

import requests

from tv_scraper.core.constants import EXPORT_TYPES, STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.core.validators import DataValidator
from tv_scraper.streaming.stream_handler import StreamHandler
from tv_scraper.streaming.utils import (
    fetch_available_indicators,
    fetch_indicator_metadata,
)
from tv_scraper.utils.helpers import format_symbol
from tv_scraper.utils.io import generate_export_filepath, save_csv_file, save_json_file

logger = logging.getLogger(__name__)


# Fixed source-key mapping from qsd.v payload -> clean output fields.
_FORECAST_SOURCE_KEY_MAP = {
    "revenue_currency": "fundamental_currency_code",
    "previous_close_price": "regular_close",
    "average_price_target": "price_target_average",
    "highest_price_target": "price_target_high",
    "lowest_price_target": "price_target_low",
    "median_price_target": "price_target_median",
    "yearly_eps_data": "earnings_fy_h",
    "quarterly_eps_data": "earnings_fq_h",
    "yearly_revenue_data": "revenues_fy_h",
    "quarterly_revenue_data": "revenues_fq_h",
}


class Streamer:
    """Stream OHLCV candles, indicators, and realtime prices from TradingView.

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
        if export_type not in EXPORT_TYPES:
            raise ValueError(
                f"Invalid export_type: '{export_type}'. "
                f"Supported types: {', '.join(sorted(EXPORT_TYPES))}"
            )
        self.export_result = export_result
        self.export_type = export_type
        self.cookie = cookie
        self.study_id_to_name_map: dict[str, str] = {}

    def _get_fresh_handler(self) -> StreamHandler:
        """Resolve a valid JWT token and return a new connected StreamHandler."""
        websocket_jwt_token = "unauthorized_user_token"
        if self.cookie:
            from tv_scraper.streaming.auth import get_valid_jwt_token

            try:
                websocket_jwt_token = get_valid_jwt_token(self.cookie)
                logger.debug("JWT token resolved successfully.")
            except Exception as exc:
                logger.error("Failed to resolve JWT token from cookie: %s", exc)
                raise

        return StreamHandler(jwt_token=websocket_jwt_token)

    # ------------------------------------------------------------------
    # Response helpers (mirrors BaseScraper contract)
    # ------------------------------------------------------------------

    @staticmethod
    def _success_response(data: Any, **metadata: Any) -> dict[str, Any]:
        """Build a standardized success response.

        Args:
            data: The response payload.
            **metadata: Arbitrary metadata key-value pairs.

        Returns:
            Response dict with status, data, metadata (``dict[str, Any]``),
            and error fields.
        """
        return {
            "status": STATUS_SUCCESS,
            "data": data,
            "metadata": dict(metadata),
            "error": None,
        }

    @staticmethod
    def _error_response(error: str, **metadata: Any) -> dict[str, Any]:
        """Build a standardized error response.

        Args:
            error: Error message string.
            **metadata: Arbitrary metadata key-value pairs.

        Returns:
            Response dict with status="failed", data=None,
            metadata (``dict[str, Any]``), and error message.
        """
        return {
            "status": STATUS_FAILED,
            "data": None,
            "metadata": dict(metadata),
            "error": error,
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
        try:
            exchange_symbol = format_symbol(exchange, symbol)
            DataValidator().verify_symbol_exchange(exchange, symbol)
            self.study_id_to_name_map = {}

            ind_flag = bool(indicators)
            handler = self._get_fresh_handler()

            self._add_symbol_to_sessions(
                handler,
                handler.quote_session,
                handler.chart_session,
                exchange_symbol,
                timeframe,
                numb_candles,
            )

            if ind_flag and indicators:
                self._add_indicators(handler, indicators)

            ohlcv_data: list[dict[str, Any]] = []
            indicator_data: dict[str, Any] = {}
            expected_ind_count = len(indicators) if ind_flag and indicators else 0

            for i, pkt in enumerate(handler.receive_packets()):
                # OHLCV extraction
                received_ohlcv = self._extract_ohlcv_from_stream(pkt)
                if received_ohlcv:
                    ohlcv_data = received_ohlcv

                # Indicator extraction
                received_ind = self._extract_indicator_from_stream(pkt)
                if received_ind:
                    indicator_data.update(received_ind)

                # Stop conditions
                ohlcv_ready = len(ohlcv_data) >= numb_candles
                ind_ready = not ind_flag or len(indicator_data) >= expected_ind_count
                if ohlcv_ready and ind_ready:
                    break
                if i > 15:
                    logger.warning(
                        "Timeout after %d packets. OHLCV=%d, Indicators=%d",
                        i,
                        len(ohlcv_data),
                        len(indicator_data),
                    )
                    break

            # Final data slicing to exactly numb_candles
            ohlcv_data = sorted(ohlcv_data, key=lambda x: x["index"])[-numb_candles:]
            for name in indicator_data:
                indicator_data[name] = sorted(
                    indicator_data[name], key=lambda x: x["index"]
                )[-numb_candles:]

            if not ohlcv_data:
                return self._error_response(
                    "No OHLCV data received from stream.",
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    numb_candles=numb_candles,
                )

            if ind_flag and indicators:
                requested_ids = [script_id for script_id, _ in indicators]
                missing_indicators = [
                    script_id
                    for script_id in requested_ids
                    if script_id not in indicator_data
                ]
                if missing_indicators:
                    return self._error_response(
                        "Failed to fetch indicator data for: "
                        + ", ".join(missing_indicators),
                        exchange=exchange,
                        symbol=symbol,
                        timeframe=timeframe,
                        numb_candles=numb_candles,
                        indicators=[list(t) for t in indicators],
                    )

            result_data = {"ohlcv": ohlcv_data, "indicators": indicator_data}

            if self.export_result:
                self._export(result_data, symbol, "get_candles")

            candle_meta: dict[str, Any] = {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "numb_candles": numb_candles,
            }
            if indicators is not None:
                candle_meta["indicators"] = [list(t) for t in indicators]
            return self._success_response(result_data, **candle_meta)

        except Exception as exc:
            logger.error("get_candles error: %s", exc)
            candle_err_meta: dict[str, Any] = {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "numb_candles": numb_candles,
            }
            if indicators is not None:
                candle_err_meta["indicators"] = [list(t) for t in indicators]
            return self._error_response(str(exc), **candle_err_meta)

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

        handler = self._get_fresh_handler()

        # Add symbol to both quote and chart sessions for maximum update frequency
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        qs = handler.quote_session
        cs = handler.chart_session

        # Subscribe to quote session for price updates
        handler.send_message("quote_add_symbols", [qs, f"={resolve_symbol}"])
        handler.send_message("quote_fast_symbols", [qs, exchange_symbol])

        # Subscribe to chart session for real-time OHLCV updates
        mapped_tf = DataValidator().get_timeframes().get("1m", "1")
        handler.send_message("resolve_symbol", [cs, "sds_sym_1", f"={resolve_symbol}"])
        handler.send_message(
            "create_series", [cs, "sds_1", "s1", "sds_sym_1", mapped_tf, 1, ""]
        )

        last_price = None

        for pkt in handler.receive_packets():
            # Handle quote session data (qsd)
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

            # Handle chart session data updates (du) for faster OHLCV updates
            elif pkt.get("m") == "du":
                p_data = pkt.get("p", [])
                if len(p_data) > 1 and isinstance(p_data[1], dict):
                    # Check for series data
                    sds_data = p_data[1].get("sds_1", {})
                    series = sds_data.get("s", [])

                    for entry in series:
                        if "v" in entry and len(entry["v"]) >= 5:
                            # OHLCV: [timestamp, open, high, low, close, volume]
                            close_price = entry["v"][4]
                            volume = entry["v"][5] if len(entry["v"]) > 5 else None

                            # Calculate change if we have last price
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

    def get_forecast(
        self,
        exchange: str,
        symbol: str,
    ) -> dict[str, Any]:
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
        try:
            exchange_symbol = format_symbol(exchange, symbol)
            DataValidator().verify_symbol_exchange(exchange, symbol)

            symbol_type = self._get_symbol_type(exchange_symbol)
            if symbol_type != "stock":
                return self._error_response(
                    "forecast is not available for this symbol because it is type: "
                    f"{symbol_type}",
                    exchange=exchange,
                    symbol=symbol,
                )

            handler = self._get_fresh_handler()

            qs = handler.quote_session
            resolve_symbol = json.dumps(
                {"adjustment": "splits", "symbol": exchange_symbol}
            )

            # Keep same connection lifecycle as candle streaming and only update
            # quote session subscriptions/fields for this symbol.
            capture_fields = sorted(set(_FORECAST_SOURCE_KEY_MAP.values()))
            handler.send_message("set_data_quality", ["low"])
            handler.send_message("quote_set_fields", [qs, *capture_fields])
            handler.send_message("quote_hibernate_all", [qs])
            handler.send_message("quote_add_symbols", [qs, f"={resolve_symbol}"])
            handler.send_message("quote_fast_symbols", [qs, exchange_symbol])

            raw_packets: list[dict[str, Any]] = []
            snapshot: dict[str, Any] = {}
            required_output_keys = set(_FORECAST_SOURCE_KEY_MAP.keys())
            found_output_keys: set[str] = set()
            packet_count = 0

            for pkt in handler.receive_packets():
                packet_count += 1
                raw_packets.append(pkt)

                if pkt.get("m") != "qsd":
                    continue

                p_data = pkt.get("p", [])
                if len(p_data) < 2 or not isinstance(p_data[1], dict):
                    continue

                block = p_data[1]
                values = block.get("v", {})
                if not isinstance(values, dict):
                    continue

                # Merge incremental qsd updates into one final snapshot.
                snapshot.update(values)
                for out_key, src_key in _FORECAST_SOURCE_KEY_MAP.items():
                    if src_key in snapshot and snapshot[src_key] is not None:
                        found_output_keys.add(out_key)

                if required_output_keys.issubset(found_output_keys):
                    break
                if packet_count > 15:
                    logger.warning(
                        "get_forecast timeout after %d packets. Found keys: %s",
                        packet_count,
                        sorted(found_output_keys),
                    )
                    break

            cleaned_data = {
                out_key: snapshot.get(src_key)
                for out_key, src_key in _FORECAST_SOURCE_KEY_MAP.items()
            }
            available_output_keys = [
                k for k, v in cleaned_data.items() if v is not None
            ]

            missing_output_keys = sorted(
                required_output_keys.difference(available_output_keys)
            )

            if missing_output_keys:
                return {
                    "status": STATUS_FAILED,
                    "data": cleaned_data,
                    "metadata": {
                        "exchange": exchange,
                        "symbol": symbol,
                        "available_output_keys": sorted(available_output_keys),
                    },
                    "error": "failed to fetch keys: " + ", ".join(missing_output_keys),
                }

            if self.export_result:
                self._export(cleaned_data, symbol, "forecast")

            return self._success_response(
                cleaned_data,
                exchange=exchange,
                symbol=symbol,
                available_output_keys=sorted(available_output_keys),
            )

        except Exception as exc:
            logger.error("get_forecast error: %s", exc)
            return self._error_response(
                str(exc),
                exchange=exchange,
                symbol=symbol,
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_symbol_to_sessions(
        self,
        handler: StreamHandler,
        quote_session: str,
        chart_session: str,
        exchange_symbol: str,
        timeframe: str = "1m",
        numb_candles: int = 10,
    ) -> None:
        """Register symbol in both quote and chart sessions."""
        timeframes = DataValidator().get_timeframes()
        mapped_tf = timeframes.get(timeframe, "1")
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        handler.send_message(
            "resolve_symbol", [chart_session, "sds_sym_1", f"={resolve_symbol}"]
        )
        handler.send_message(
            "create_series",
            [chart_session, "sds_1", "s1", "sds_sym_1", mapped_tf, numb_candles, ""],
        )
        handler.send_message("quote_fast_symbols", [quote_session, exchange_symbol])

    def _add_indicators(
        self, handler: StreamHandler, indicators: list[tuple[str, str]]
    ) -> None:
        """Add one or more indicator studies to the chart session."""
        for idx, (script_id, script_version) in enumerate(indicators):
            logger.info(
                "Processing indicator %d/%d: %s v%s",
                idx + 1,
                len(indicators),
                script_id,
                script_version,
            )

            res = fetch_indicator_metadata(
                script_id=script_id,
                script_version=script_version,
                chart_session=handler.chart_session,
                cookie=self.cookie,
            )
            if res["status"] != STATUS_SUCCESS or not res["data"]:
                error_text = res.get("error") or "unknown error"
                logger.error(
                    "Failed to fetch metadata for %s v%s: %s",
                    script_id,
                    script_version,
                    error_text,
                )
                raise RuntimeError(
                    f"Failed to fetch metadata for indicator {script_id} v{script_version}: "
                    f"{error_text}. Check if the script ID and version are correct, or for custom/private indicators, ensure your cookie has access."
                )

            ind_study = res["data"]
            study_id = f"st{9 + idx}"
            ind_study["p"][1] = study_id
            self.study_id_to_name_map[study_id] = script_id

            try:
                handler.send_message("create_study", ind_study["p"])
                handler.send_message("quote_hibernate_all", [handler.quote_session])
            except Exception as exc:
                logger.error("Failed to add indicator %s: %s", script_id, exc)
                raise RuntimeError(
                    f"Failed to add indicator {script_id} v{script_version}: {exc}"
                ) from exc

    def _serialize_ohlcv(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract OHLCV entries from a timescale_update packet."""
        ohlcv_entries = raw_data.get("p", [{}, {}])[1].get("sds_1", {}).get("s", [])
        result = []
        for entry in ohlcv_entries:
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

    def _extract_ohlcv_from_stream(self, pkt: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract OHLCV from a packet if it's a timescale_update."""
        if pkt.get("m") == "timescale_update":
            return self._serialize_ohlcv(pkt)
        return []

    def _extract_indicator_from_stream(self, pkt: dict[str, Any]) -> dict[str, Any]:
        """Extract indicator data from a ``du`` packet."""
        indicator_data: dict[str, Any] = {}
        if pkt.get("m") != "du":
            return indicator_data

        p_data = pkt.get("p", [])
        if len(p_data) <= 1 or not isinstance(p_data[1], dict):
            return indicator_data

        for key, val in p_data[1].items():
            if key.startswith("st") and key in self.study_id_to_name_map:
                if val.get("st"):
                    indicator_name = self.study_id_to_name_map[key]
                    json_data = []
                    for item in val["st"]:
                        tmp = {"index": item["i"], "timestamp": item["v"][0]}
                        tmp.update({str(i): v for i, v in enumerate(item["v"][1:])})
                        json_data.append(tmp)
                    indicator_data[indicator_name] = json_data

        return indicator_data

    def _export(self, data: Any, symbol: str, data_category: str) -> None:
        """Export data to file."""
        filepath = generate_export_filepath(symbol, data_category, self.export_type)
        if self.export_type == "csv":
            save_csv_file(data, filepath)
        else:
            save_json_file(data, filepath)

    def _get_symbol_type(self, exchange_symbol: str) -> str | None:
        """Fetch the symbol type (e.g. 'stock', 'crypto', 'spot') from TradingView scanner."""
        from tv_scraper.core.constants import DEFAULT_USER_AGENT, SCANNER_URL

        try:
            resp = requests.get(
                url=f"{SCANNER_URL}/symbol",
                params={"symbol": exchange_symbol, "fields": "type", "no_404": "false"},
                headers={"User-Agent": DEFAULT_USER_AGENT},
                timeout=10,
            )
            resp.raise_for_status()
            return str(resp.json().get("type"))
        except Exception as exc:
            raise RuntimeError(
                f"Failed to resolve symbol type for {exchange_symbol}: {exc}"
            ) from exc
