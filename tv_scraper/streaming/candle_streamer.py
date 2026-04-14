"""Candle streamer for OHLCV and indicator data streaming."""

import logging
from collections.abc import Generator
from typing import Any

from tv_scraper.core import validators
from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import STATUS_SUCCESS
from tv_scraper.core.validation_data import (
    EXCHANGE_LITERAL,
    TIMEFRAME_LITERAL,
)
from tv_scraper.scrapers.scripts.pine import Pine
from tv_scraper.streaming.base_streamer import BaseStreamer
from tv_scraper.streaming.utils import (
    fetch_available_indicators,
    fetch_indicator_metadata,
)
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
        # --- Validation ---
        exchange, _symbol = validators.verify_symbol_exchange(exchange, symbol)
        validators.validate_timeframe(timeframe)
        validators.validate_range("numb_candles", numb_candles, 1, 5000)
        exchange_symbol = format_symbol(exchange, _symbol)
        self.study_id_to_name_map = {}

        ind_flag = bool(indicators)
        self.connect()

        self._subscribe_chart(exchange_symbol, timeframe, numb_candles)
        self._subscribe_quote(exchange_symbol)

        if ind_flag and indicators:
            self._add_indicators(indicators)

        ohlcv_data: list[dict[str, Any]] = []
        indicator_data: dict[str, Any] = {}
        expected_ind_count = len(indicators) if ind_flag and indicators else 0

        for i, pkt in enumerate(self.receive_packets()):
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
            return self._error_response("No OHLCV data received from stream.")

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
                    + ", ".join(missing_indicators)
                )

        result_data = {"ohlcv": ohlcv_data, "indicators": indicator_data}

        if self.export_result:
            self._export(result_data, symbol, "get_candles")

        return self._success_response(result_data)

    def stream_realtime_price(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Persistent generator yielding normalized realtime price updates."""
        # --- Validation ---
        exchange, _symbol = validators.verify_symbol_exchange(exchange, symbol)
        exchange_symbol = format_symbol(exchange, _symbol)

        self.connect()
        self._subscribe_quote(exchange_symbol)
        self._subscribe_chart(exchange_symbol, "1m", 1)

        last_price = None

        for pkt in self.receive_packets():
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
        """Fetch available built-in indicators with standardized response envelope."""
        return fetch_available_indicators()

    @staticmethod
    def _is_standard_indicator(script_id: str) -> bool:
        """Return True if the indicator is a TradingView standard built-in script."""
        return script_id.startswith("STD;")

    @staticmethod
    def _format_pine_error_details(errors: Any) -> str:
        """Format Pine validation errors into a concise readable message."""
        if not isinstance(errors, list) or not errors:
            return "unknown validation error"

        details: list[str] = []
        for error_item in errors:
            if isinstance(error_item, dict):
                msg = (
                    error_item.get("message")
                    or error_item.get("text")
                    or error_item.get("error")
                )
                details.append(str(msg) if msg else str(error_item))
            else:
                details.append(str(error_item))

        return "; ".join(details)

    def _validate_custom_indicator_script(
        self,
        script_id: str,
        script_version: str,
    ) -> None:
        """Validate custom Pine script before creating a chart study.

        For built-in indicators (``STD;...``), no additional validation is needed.
        For custom scripts, we fetch the source and run Pine validation so
        compile/runtime script issues are surfaced clearly in streamer responses.
        """
        if self._is_standard_indicator(script_id):
            return

        pine = Pine(cookie=self.cookie)

        script_response = pine.get_script(script_id, script_version)
        if script_response.get("status") != STATUS_SUCCESS:
            error_text = script_response.get("error") or "unknown error"
            raise RuntimeError(
                f"Failed to fetch custom Pine script {script_id} v{script_version}: {error_text}"
            )

        script_payload = script_response.get("data")
        source = (
            script_payload.get("source") if isinstance(script_payload, dict) else None
        )
        if not isinstance(source, str) or not source.strip():
            raise RuntimeError(
                f"Custom Pine script {script_id} v{script_version} returned empty source."
            )

        validation = pine.validate_script(source)
        if validation.get("status") != STATUS_SUCCESS:
            validation_meta = validation.get("metadata")
            error_list = (
                validation_meta.get("errors")
                if isinstance(validation_meta, dict)
                else None
            )
            formatted_errors = self._format_pine_error_details(error_list)
            raise RuntimeError(
                f"Custom Pine script {script_id} v{script_version} has validation errors: {formatted_errors}"
            )

    def _add_indicators(self, indicators: list[tuple[str, str]]) -> None:
        """Add one or more indicator studies to the chart session."""
        for idx, (script_id, script_version) in enumerate(indicators):
            logger.info(
                "Processing indicator %d/%d: %s v%s",
                idx + 1,
                len(indicators),
                script_id,
                script_version,
            )

            self._validate_custom_indicator_script(script_id, script_version)

            res = fetch_indicator_metadata(
                script_id=script_id,
                script_version=script_version,
                chart_session=self.chart_session,
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
                self._send_msg("create_study", ind_study["p"])
                self._send_msg("quote_hibernate_all", [self.quote_session])
            except Exception as exc:
                logger.error("Failed to add indicator %s: %s", script_id, exc)
                raise RuntimeError(
                    f"Failed to add indicator {script_id} v{script_version}: {exc}"
                ) from exc

    def _serialize_ohlcv(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract OHLCV entries from a timescale_update packet."""
        p_data = raw_data.get("p", [])
        if len(p_data) < 2 or not isinstance(p_data[1], dict):
            return []

        ohlcv_entries = p_data[1].get("sds_1", {}).get("s", [])
        result = []
        for entry in ohlcv_entries:
            if "i" not in entry or "v" not in entry or len(entry["v"]) < 5:
                continue
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
        if len(p_data) < 2 or not isinstance(p_data[1], dict):
            return indicator_data

        for key, val in p_data[1].items():
            if key.startswith("st") and key in self.study_id_to_name_map:
                if val.get("st"):
                    indicator_name = self.study_id_to_name_map[key]
                    json_data = []
                    for item in val["st"]:
                        if "i" not in item or "v" not in item or not item["v"]:
                            continue
                        tmp = {"index": item["i"], "timestamp": item["v"][0]}
                        tmp.update({str(i): v for i, v in enumerate(item["v"][1:])})
                        json_data.append(tmp)
                    indicator_data[indicator_name] = json_data

        return indicator_data
