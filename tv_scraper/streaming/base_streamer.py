"""Base streamer class providing WebSocket connection functionality.

This module provides a base class for streaming functionality that handles
WebSocket connection establishment, JWT token handling, and session management.
Provides standardized response envelope via BaseScraper inheritance.
"""

import logging

from tv_scraper.core.base import BaseScraper
from tv_scraper.streaming.stream_handler import StreamHandler

logger = logging.getLogger(__name__)


class BaseStreamer(BaseScraper):
    """Base class for streaming functionality.

    Provides WebSocket connection management with JWT token handling and
    inherits standardized response envelope methods from BaseScraper.

    Args:
        export_result: Whether to export data to file after retrieval.
        export_type: Export format — ``"json"`` or ``"csv"``.
        cookie: TradingView session cookies for authentication.
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

    def connect(self) -> StreamHandler:
        """Create and return a connected StreamHandler with JWT token.

        Resolves JWT token from cookie if provided, otherwise uses
        unauthorized user token.

        Returns:
            Connected StreamHandler instance.

        Raises:
            Exception: If JWT token resolution fails.
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

        return StreamHandler(jwt_token=websocket_jwt_token)
