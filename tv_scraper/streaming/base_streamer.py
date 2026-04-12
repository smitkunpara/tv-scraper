"""Base streamer class providing WebSocket connection functionality.

This module provides a base class for streaming functionality that handles
WebSocket connection establishment, JWT token handling, and session management.
Provides standardized response envelope via BaseScraper inheritance.
"""

import json
import logging
import re
import secrets
import socket
import string
from collections.abc import Generator
from typing import Any

from websocket import WebSocketConnectionClosedException, create_connection

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import DEFAULT_USER_AGENT, WEBSOCKET_URL

logger = logging.getLogger(__name__)

# Default WebSocket URL with chart query params
_DEFAULT_WS_URL = WEBSOCKET_URL + "?from=chart%2F&type=chart"

# HTTP headers for WebSocket handshake
_REQUEST_HEADERS = {
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "Upgrade",
    "Host": "data.tradingview.com",
    "Origin": "https://www.tradingview.com",
    "Pragma": "no-cache",
    "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
    "Upgrade": "websocket",
    "User-Agent": DEFAULT_USER_AGENT,
}

_QUOTE_FIELDS = [
    "ch",
    "chp",
    "current_session",
    "description",
    "local_description",
    "language",
    "exchange",
    "fractional",
    "is_tradable",
    "lp",
    "lp_time",
    "minmov",
    "minmove2",
    "original_name",
    "pricescale",
    "pro_name",
    "short_name",
    "type",
    "update_mode",
    "volume",
    "currency_code",
    "rchp",
    "rtc",
    "high_price",
    "low_price",
    "open_price",
    "prev_close_price",
    "bid",
    "ask",
    "bid_size",
    "ask_size",
]


class BaseStreamer(BaseScraper):
    """Base class for streaming functionality.

    Provides WebSocket connection management with JWT token handling,
    session management, and standardized response envelope methods.

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
        self.study_id_to_name_map: dict[str, str] = {}
        self.ws: Any = None
        self.quote_session: str = ""
        self.chart_session: str = ""

    # -- Connection & Session Management -----------------------------------

    def connect(self) -> None:
        """Establish WebSocket connection and initialize streaming sessions.

        Resolves JWT token from cookie if provided, otherwise uses
        unauthorized user token. Performs initial handshake with the server.

        Raises:
            RuntimeError: If connection or JWT resolution fails.
        """
        websocket_jwt_token = "unauthorized_user_token"
        if self.cookie:
            from tv_scraper.streaming.auth import get_valid_jwt_token

            try:
                websocket_jwt_token = get_valid_jwt_token(self.cookie)
                logger.debug("JWT token resolved successfully.")
            except Exception as exc:
                logger.error("Failed to resolve JWT token from cookie: %s", exc)
                raise RuntimeError(
                    f"Failed to resolve JWT token from cookie: {exc}"
                ) from exc

        try:
            self.ws = create_connection(
                _DEFAULT_WS_URL,
                headers=_REQUEST_HEADERS,
                sockopt=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)],
                timeout=10,
                enable_multithread=True,
            )
            self._initialize_sessions(websocket_jwt_token)
        except Exception as exc:
            logger.error("Failed to connect to TradingView WebSocket: %s", exc)
            raise RuntimeError(f"WebSocket connection failed: {exc}") from exc

    def _initialize_sessions(self, jwt_token: str) -> None:
        """Initialize quote and chart sessions."""
        self.quote_session = self._generate_session("qs_")
        self.chart_session = self._generate_session("cs_")

        logger.info(
            "Sessions generated — quote: %s, chart: %s",
            self.quote_session,
            self.chart_session,
        )

        self._send_msg("set_auth_token", [jwt_token])
        self._send_msg("set_locale", ["en", "US"])
        self._send_msg("chart_create_session", [self.chart_session, ""])
        self._send_msg("quote_create_session", [self.quote_session])
        self._send_msg("quote_set_fields", [self.quote_session, *_QUOTE_FIELDS])
        self._send_msg("quote_hibernate_all", [self.quote_session])

    @staticmethod
    def _generate_session(prefix: str = "qs_") -> str:
        """Generate a random session identifier."""
        random_part = "".join(secrets.choice(string.ascii_lowercase) for _ in range(12))
        return prefix + random_part

    # -- Subscription Helpers ----------------------------------------------

    def _get_resolve_symbol_param(self, symbol: str) -> str:
        """Construct the standardized resolve_symbol JSON parameter."""
        return json.dumps(
            {"adjustment": "splits", "symbol": symbol}, separators=(",", ":")
        )

    def _subscribe_quote(self, symbol: str, fields: list[str] | None = None) -> None:
        """Register a symbol for quote updates."""
        resolve_param = self._get_resolve_symbol_param(symbol)
        if fields:
            self._send_msg("quote_set_fields", [self.quote_session, *fields])

        self._send_msg("quote_add_symbols", [self.quote_session, f"={resolve_param}"])
        self._send_msg("quote_fast_symbols", [self.quote_session, symbol])

    def _subscribe_chart(self, symbol: str, timeframe: str, numb_candles: int) -> None:
        """Register a symbol for chart/indicator updates."""
        from tv_scraper.core.validation_data import TIMEFRAMES

        mapped_tf = TIMEFRAMES.get(timeframe, "1")
        resolve_param = self._get_resolve_symbol_param(symbol)

        self._send_msg(
            "resolve_symbol", [self.chart_session, "sds_sym_1", f"={resolve_param}"]
        )
        self._send_msg(
            "create_series",
            [
                self.chart_session,
                "sds_1",
                "s1",
                "sds_sym_1",
                mapped_tf,
                numb_candles,
                "",
            ],
        )

    # -- Message Sending & Receiving ---------------------------------------

    def _send_msg(self, func: str, args: list[Any]) -> None:
        """Format and send a message over the WebSocket."""
        payload = json.dumps({"m": func, "p": args}, separators=(",", ":"))
        framed_msg = f"~m~{len(payload)}~m~{payload}"

        logger.debug("Sending message: %s", framed_msg)
        try:
            self.ws.send(framed_msg)
        except (
            ConnectionError,
            TimeoutError,
            WebSocketConnectionClosedException,
        ) as exc:
            logger.error("Failed to send message: %s", exc)
            raise RuntimeError(f"Failed to send message '{func}': {exc}") from exc

    def receive_packets(self) -> Generator[dict[str, Any], None, None]:
        """Receive and parse WebSocket data, handling heartbeats."""
        if not self.ws:
            raise RuntimeError("WebSocket is not connected. Call connect() first.")

        try:
            while True:
                try:
                    raw_result = self.ws.recv()
                    result = (
                        raw_result.decode("utf-8")
                        if isinstance(raw_result, bytes)
                        else str(raw_result)
                    )

                    # Heartbeat echo
                    if re.match(r"~m~\d+~m~~h~\d+$", result):
                        logger.debug("Heartbeat: %s", result)
                        self.ws.send(result)
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
                except TimeoutError:
                    continue
                except (ConnectionError, OSError) as exc:
                    logger.error("WebSocket error: %s", exc)
                    break
        finally:
            self.close()

    def close(self) -> None:
        """Close the WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            finally:
                self.ws = None
