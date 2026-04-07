"""Forecast streamer for capturing forecast data from TradingView."""

import json
import logging
from typing import Any, cast

import requests

from tv_scraper.core.base import catch_errors
from tv_scraper.core.constants import DEFAULT_USER_AGENT, SCANNER_URL
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.validation_data import EXCHANGE_LITERAL
from tv_scraper.core.validators import verify_symbol_exchange
from tv_scraper.streaming.base_streamer import BaseStreamer
from tv_scraper.utils.helpers import format_symbol

logger = logging.getLogger(__name__)

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


class ForecastStreamer(BaseStreamer):
    """Stream forecast data from TradingView via WebSocket quote stream.

    Captures qsd packets until all required forecast fields are received,
    then provides a merged snapshot. Only available for stock symbols.
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
    def get_forecast(self, exchange: EXCHANGE_LITERAL, symbol: str) -> dict[str, Any]:  # noqa: PLR0915
        """Capture forecast data via TradingView WebSocket quote stream.

        This method captures qsd packets until all required forecast fields are
        received, then provides a merged snapshot.

        Args:
            exchange: Exchange name (e.g. ``"NYSE"``).
            symbol: Symbol name (e.g. ``"A"``).

        Returns:
            Standardized response dict with
            ``{"status", "data", "metadata", "error"}``.
        """
        exchange, _symbol = verify_symbol_exchange(exchange, symbol)
        exchange_symbol = format_symbol(exchange, _symbol)

        symbol_type = self._get_symbol_type(exchange_symbol)
        if symbol_type != "stock":
            raise ValidationError(
                "forecast is not available for this symbol because it is type: "
                f"{symbol_type}"
            )

        handler = self.connect()

        qs = handler.quote_session
        resolve_symbol = json.dumps(
            {"adjustment": "splits", "symbol": exchange_symbol}
        )

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
            return self._error_response(
                "failed to fetch keys: " + ", ".join(missing_output_keys),
                data=cleaned_data,
                available_output_keys=sorted(available_output_keys),
            )

        if self.export_result:
            self._export(cleaned_data, symbol, "forecast")

        return self._success_response(
            cleaned_data,
            available_output_keys=sorted(available_output_keys),
        )

    def _get_symbol_type(self, exchange_symbol: str) -> str | None:
        """Fetch the symbol type (e.g. 'stock', 'crypto', 'spot') from TradingView scanner."""
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
