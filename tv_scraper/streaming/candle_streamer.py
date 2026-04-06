"""Candle streamer for OHLCV and indicator data streaming."""

import json
import logging
from typing import Any

from tv_scraper.core.validators import DataValidator
from tv_scraper.streaming.base_streamer import BaseStreamer
from tv_scraper.streaming.stream_handler import StreamHandler
from tv_scraper.streaming.utils import fetch_indicator_metadata
from tv_scraper.utils.helpers import format_symbol

logger = logging.getLogger(__name__)


class CandleStreamer(BaseStreamer):
    """Stream OHLCV candle data and optional indicator values from TradingView.

    Inherits from BaseStreamer which provides WebSocket connection management
    and standardized response envelope methods.

    Args:
        export_result: Whether to export data to file after retrieval.
        export_type: Export format — ``"json"`` or ``"csv"``.
        cookie: TradingView session cookies for session authentication.
            If not provided, unauthenticated access is used.
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

    def get_candles(  # noqa: PLR0915
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
            if not isinstance(numb_candles, int) or numb_candles <= 0:
                return self._error_response(
                    f"numb_candles must be a positive integer, got {numb_candles!r}.",
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    numb_candles=numb_candles,
                )
            exchange_symbol = format_symbol(exchange, symbol)
            DataValidator().verify_symbol_exchange(exchange, symbol)
            self.study_id_to_name_map = {}

            ind_flag = bool(indicators)
            handler = self.connect()

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
                received_ohlcv = self._extract_ohlcv_from_stream(pkt)
                if received_ohlcv:
                    ohlcv_data = received_ohlcv

                received_ind = self._extract_indicator_from_stream(pkt)
                if received_ind:
                    indicator_data.update(received_ind)

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

        except RuntimeError as exc:
            logger.error("get_candles runtime error: %s", exc)
            candle_err_meta: dict[str, Any] = {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "numb_candles": numb_candles,
            }
            if indicators is not None:
                candle_err_meta["indicators"] = [list(t) for t in indicators]
            return self._error_response(str(exc), **candle_err_meta)

        except Exception as exc:
            logger.error("get_candles unexpected error: %s", exc)
            candle_err_meta: dict[str, Any] = {
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "numb_candles": numb_candles,
            }
            if indicators is not None:
                candle_err_meta["indicators"] = [list(t) for t in indicators]
            return self._error_response(f"Unexpected error: {exc}", **candle_err_meta)

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
        from tv_scraper.core.constants import STATUS_SUCCESS

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
