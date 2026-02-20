"""RealTimeData class for simple OHLCV and watchlist streaming.

Provides generators that yield raw parsed JSON packets from the TradingView
WebSocket feed. For normalized price data, see :class:`Streamer.stream_realtime_price`.
"""

import json
import logging
from collections.abc import Generator
from typing import Any

from tv_scraper.core.constants import WEBSOCKET_URL
from tv_scraper.core.validators import DataValidator
from tv_scraper.streaming.stream_handler import StreamHandler
from tv_scraper.utils.helpers import format_symbol

logger = logging.getLogger(__name__)

_SCREENER_WS_URL = WEBSOCKET_URL + "?from=screener%2F"


class RealTimeData:
    """Simple streaming interface for OHLCV and watchlist data.

    Uses a dedicated WebSocket connection through :class:`StreamHandler`.
    Methods return generators that yield parsed JSON packets.
    """

    def __init__(self) -> None:
        self._handler = StreamHandler(websocket_url=_SCREENER_WS_URL)

    def get_ohlcv(
        self, exchange: str, symbol: str
    ) -> Generator[dict[str, Any], None, None]:
        """Stream OHLCV data for a single symbol.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Symbol name (e.g. ``"BTCUSDT"``).

        Yields:
            Parsed JSON packets from the TradingView WebSocket.

        Raises:
            ValidationError: If the exchange:symbol combination is invalid.
        """
        DataValidator().verify_symbol_exchange(exchange, symbol)
        exchange_symbol = format_symbol(exchange, symbol)
        qs = self._handler.quote_session
        cs = self._handler.chart_session

        self._add_symbol_to_sessions(qs, cs, exchange_symbol)
        return self._handler.receive_packets()

    def get_latest_trade_info(
        self, exchanges: list[str], symbols: list[str]
    ) -> Generator[dict[str, Any], None, None]:
        """Stream summary trade info for multiple symbols.

        Args:
            exchanges: List of exchange names.
            symbols: List of symbol names (same length as *exchanges*).

        Yields:
            Parsed JSON packets from the TradingView WebSocket.
        """
        qs = self._handler.quote_session
        exchange_symbols = [
            format_symbol(ex, sym) for ex, sym in zip(exchanges, symbols, strict=True)
        ]

        self._add_multiple_symbols_to_sessions(qs, exchange_symbols)
        return self._handler.receive_packets()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_symbol_to_sessions(
        self, quote_session: str, chart_session: str, exchange_symbol: str
    ) -> None:
        """Add a symbol to quote and chart sessions."""
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        self._handler.send_message(
            "quote_add_symbols", [quote_session, f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "resolve_symbol", [chart_session, "sds_sym_1", f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "create_series", [chart_session, "sds_1", "s1", "sds_sym_1", "1", 10, ""]
        )
        self._handler.send_message(
            "quote_fast_symbols", [quote_session, exchange_symbol]
        )
        self._handler.send_message(
            "create_study",
            [
                chart_session,
                "st1",
                "st1",
                "sds_1",
                "Volume@tv-basicstudies-246",
                {"length": 20, "col_prev_close": "false"},
            ],
        )
        self._handler.send_message("quote_hibernate_all", [quote_session])

    def _add_multiple_symbols_to_sessions(
        self, quote_session: str, exchange_symbols: list[str]
    ) -> None:
        """Add multiple symbols to the quote session."""
        first_symbol = exchange_symbols[0] if exchange_symbols else ""
        resolve_symbol = json.dumps(
            {
                "adjustment": "splits",
                "currency-id": "USD",
                "session": "regular",
                "symbol": first_symbol,
            }
        )
        self._handler.send_message(
            "quote_add_symbols", [quote_session, f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "quote_fast_symbols", [quote_session, f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "quote_add_symbols", [quote_session, *exchange_symbols]
        )
        self._handler.send_message(
            "quote_fast_symbols", [quote_session, *exchange_symbols]
        )
