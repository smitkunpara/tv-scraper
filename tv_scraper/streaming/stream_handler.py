"""Low-level WebSocket protocol handler for TradingView streaming.

Manages the WebSocket connection, session generation, message framing,
and session initialization.
"""

import json
import logging
import secrets
import string
import socket

from websocket import create_connection

from tv_scraper.core.constants import WEBSOCKET_URL

logger = logging.getLogger(__name__)

# Default WebSocket URL with chart query params
_DEFAULT_WS_URL = WEBSOCKET_URL + "?from=chart%2F&type=chart"

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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    ),
}

_QUOTE_FIELDS = [
    "ch", "chp", "current_session", "description", "local_description",
    "language", "exchange", "fractional", "is_tradable", "lp",
    "lp_time", "minmov", "minmove2", "original_name", "pricescale",
    "pro_name", "short_name", "type", "update_mode", "volume",
    "currency_code", "rchp", "rtc", "high_price", "low_price", "open_price",
    "prev_close_price", "bid", "ask", "bid_size", "ask_size",
]


class StreamHandler:
    """Low-level WebSocket manager for TradingView data streaming.

    Handles connection establishment, session generation, message framing,
    and initialization of quote/chart sessions.

    Args:
        websocket_url: WebSocket URL override. Defaults to TradingView chart URL.
        jwt_token: JWT token for authentication. ``"unauthorized_user_token"``
            allows unauthenticated access.
    """

    def __init__(
        self,
        websocket_url: str | None = None,
        jwt_token: str = "unauthorized_user_token",
    ) -> None:
        url = websocket_url or _DEFAULT_WS_URL
        
        # Create WebSocket with optimized settings for low latency
        self.ws = create_connection(
            url, 
            headers=_REQUEST_HEADERS,
            sockopt=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]  # Disable Nagle's algorithm for lower latency
        )
        
        self._initialize(jwt_token)

    # -- Session helpers ---------------------------------------------------

    @staticmethod
    def generate_session(prefix: str = "qs_") -> str:
        """Generate a random session identifier.

        Format: ``prefix`` + 12 random lowercase ASCII letters.

        Args:
            prefix: String prefix (e.g. ``"qs_"`` or ``"cs_"``).

        Returns:
            Unique session identifier string.
        """
        random_part = "".join(secrets.choice(string.ascii_lowercase) for _ in range(12))
        return prefix + random_part

    # -- Message framing ---------------------------------------------------

    @staticmethod
    def prepend_header(message: str) -> str:
        """Frame a message with the TradingView length header.

        Format: ``~m~{length}~m~{message}``

        Args:
            message: Raw message string.

        Returns:
            Framed message.
        """
        return f"~m~{len(message)}~m~{message}"

    @staticmethod
    def construct_message(func: str, param_list: list) -> str:
        """Build a JSON-RPC–style message body.

        Args:
            func: Function/command name (e.g. ``"set_locale"``).
            param_list: List of parameters.

        Returns:
            Compact JSON string ``{"m":func,"p":param_list}``.
        """
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def create_message(self, func: str, param_list: list) -> str:
        """Create a complete framed message ready for sending.

        Args:
            func: Function/command name.
            param_list: List of parameters.

        Returns:
            Header-framed JSON message string.
        """
        return self.prepend_header(self.construct_message(func, param_list))

    def send_message(self, func: str, args: list) -> None:
        """Send a framed message over the WebSocket.

        Args:
            func: Function/command name.
            args: Arguments list.
        """
        message = self.create_message(func, args)
        logger.debug("Sending message: %s", message)
        try:
            self.ws.send(message)
        except (ConnectionError, TimeoutError) as exc:
            logger.error("Failed to send message: %s", exc)

    # -- Initialization ----------------------------------------------------

    def _initialize(self, jwt_token: str) -> None:
        """Generate sessions and send all setup messages."""
        self.quote_session = self.generate_session("qs_")
        self.chart_session = self.generate_session("cs_")
        logger.info(
            "Sessions generated — quote: %s, chart: %s",
            self.quote_session,
            self.chart_session,
        )
        self._initialize_sessions(self.quote_session, self.chart_session, jwt_token)

    def _initialize_sessions(
        self, quote_session: str, chart_session: str, jwt_token: str
    ) -> None:
        """Send the 6 required session setup messages."""
        self.send_message("set_auth_token", [jwt_token])
        self.send_message("set_locale", ["en", "US"])
        self.send_message("chart_create_session", [chart_session, ""])
        self.send_message("quote_create_session", [quote_session])
        self.send_message("quote_set_fields", [quote_session, *_QUOTE_FIELDS])
        self.send_message("quote_hibernate_all", [quote_session])
