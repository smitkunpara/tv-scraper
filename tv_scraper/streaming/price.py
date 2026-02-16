"""RealTimeData class for simple OHLCV and watchlist streaming.

Provides generators that yield raw parsed JSON packets from the TradingView
WebSocket feed. For normalized price data, see :class:`Streamer.stream_realtime_price`.
"""

import json
import logging
import re
import socket
from typing import Generator, List

from websocket import WebSocketConnectionClosedException

from tv_scraper.core.constants import WEBSOCKET_URL
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

    def get_ohlcv(self, exchange: str, symbol: str) -> Generator[dict, None, None]:
        """Stream OHLCV data for a single symbol.

        Args:
            exchange: Exchange name (e.g. ``"BINANCE"``).
            symbol: Symbol name (e.g. ``"BTCUSDT"``).

        Yields:
            Parsed JSON packets from the TradingView WebSocket.
        """
        exchange_symbol = format_symbol(exchange, symbol)
        qs = self._handler.quote_session
        cs = self._handler.chart_session

        self._add_symbol_to_sessions(qs, cs, exchange_symbol)
        return self._get_data()

    def get_latest_trade_info(
        self, exchanges: List[str], symbols: List[str]
    ) -> Generator[dict, None, None]:
        """Stream summary trade info for multiple symbols.

        Args:
            exchanges: List of exchange names.
            symbols: List of symbol names (same length as *exchanges*).

        Yields:
            Parsed JSON packets from the TradingView WebSocket.
        """
        qs = self._handler.quote_session
        exchange_symbols = [
            format_symbol(ex, sym) for ex, sym in zip(exchanges, symbols)
        ]

        self._add_multiple_symbols_to_sessions(qs, exchange_symbols)
        return self._get_data()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_symbol_to_sessions(
        self, quote_session: str, chart_session: str, exchange_symbol: str
    ) -> None:
        """Add a symbol to quote and chart sessions."""
        resolve_symbol = json.dumps({"adjustment": "splits", "symbol": exchange_symbol})
        self._handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        self._handler.send_message(
            "resolve_symbol", [chart_session, "sds_sym_1", f"={resolve_symbol}"]
        )
        self._handler.send_message(
            "create_series", [chart_session, "sds_1", "s1", "sds_sym_1", "1", 10, ""]
        )
        self._handler.send_message("quote_fast_symbols", [quote_session, exchange_symbol])
        self._handler.send_message(
            "create_study",
            [
                chart_session, "st1", "st1", "sds_1",
                "Volume@tv-basicstudies-246",
                {"length": 20, "col_prev_close": "false"},
            ],
        )
        self._handler.send_message("quote_hibernate_all", [quote_session])

    def _add_multiple_symbols_to_sessions(
        self, quote_session: str, exchange_symbols: List[str]
    ) -> None:
        """Add multiple symbols to the quote session."""
        first_symbol = exchange_symbols[0] if exchange_symbols else ""
        resolve_symbol = json.dumps({
            "adjustment": "splits",
            "currency-id": "USD",
            "session": "regular",
            "symbol": first_symbol,
        })
        self._handler.send_message("quote_add_symbols", [quote_session, f"={resolve_symbol}"])
        self._handler.send_message("quote_fast_symbols", [quote_session, f"={resolve_symbol}"])
        self._handler.send_message("quote_add_symbols", [quote_session] + exchange_symbols)
        self._handler.send_message("quote_fast_symbols", [quote_session] + exchange_symbols)

    def _get_data(self) -> Generator[dict, None, None]:
        """Receive and parse WebSocket data, handling heartbeats.

        Yields:
            Parsed JSON packets.
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
                except socket.timeout:
                    # Socket timeout is expected with non-blocking socket
                    # Just continue to next iteration
                    continue
                except (ConnectionError, TimeoutError, OSError) as exc:
                    logger.error("WebSocket error: %s", exc)
                    break
        finally:
            try:
                self._handler.ws.close()
            except Exception:
                pass
