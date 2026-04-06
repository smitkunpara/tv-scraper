"""Authentication module for TradingView.

Handles JWT token extraction from TradingView using cookies, token validation,
and caching.
"""

import base64
import json
import logging
import re
import threading
import time
from typing import Any, cast

import requests

from tv_scraper.core.constants import CHART_SESSION_URL, DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

# -- Token cache (module-level, thread-safe) -----------------------------------
_token_cache: dict[str, Any] = {
    "token": None,
    "expiry": 0,
}
_token_lock = threading.Lock()


def _pad_base64(data: str) -> str:
    """Add base64 padding to a string if needed."""
    padding = 4 - len(data) % 4
    return data + "=" * padding if padding < 4 else data


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode JWT payload without verification. Returns None on failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = _pad_base64(parts[1])
        return cast(dict[str, Any], json.loads(base64.urlsafe_b64decode(payload_b64)))
    except Exception:
        return None


def extract_jwt_token(cookie: str) -> str | None:
    """Extract JWT token from TradingView using provided cookies.

    Args:
        cookie: TradingView session cookies as a string.

    Returns:
        JWT token string if successful, None otherwise.

    Raises:
        ValueError: If cookies are invalid or token extraction fails.
    """
    if not cookie or not cookie.strip():
        raise ValueError("TradingView cookie is required for token extraction.")

    headers = {
        "Cookie": cookie,
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }

    try:
        response = requests.get(CHART_SESSION_URL, headers=headers, timeout=30)
        response.raise_for_status()
        html_content = response.text

        jwt_pattern = r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"
        potential_tokens: list[str] = re.findall(jwt_pattern, html_content)

        def _verify_jwt_format(token: str) -> bool:
            try:
                parts = token.split(".")
                if len(parts) != 3:
                    return False
                header_b64 = _pad_base64(parts[0])
                payload_b64 = _pad_base64(parts[1])
                header = json.loads(base64.urlsafe_b64decode(header_b64))
                json.loads(base64.urlsafe_b64decode(payload_b64))
                return "alg" in header and "typ" in header
            except Exception:
                return False

        for token in potential_tokens:
            if _verify_jwt_format(token):
                logger.info("Successfully extracted valid JWT token from TradingView.")
                return token

        raise ValueError(
            "JWT token not found in TradingView response. Ensure your cookies "
            "are valid and include a session for an authenticated user."
        )

    except requests.RequestException as e:
        raise ValueError(
            f"Failed to fetch TradingView chart page for token extraction: {e}"
        ) from e


def get_token_info(token: str) -> dict[str, Any]:
    """Decode JWT token and extract expiry + user information.

    Note: This does NOT verify the signature, only decodes the payload.
    """
    payload = _decode_jwt_payload(token)
    if payload is None:
        return {"valid": False, "error": "Invalid token format"}

    return {
        "valid": True,
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "user_id": payload.get("user_id"),
    }


def get_valid_jwt_token(cookie: str, force_refresh: bool = False) -> str:
    """Get a valid JWT token, reusing cached token if not expired.

    Args:
        cookie: TradingView cookies.
        force_refresh: Force token refresh even if cached token is valid.

    Returns:
        A valid JWT token string.

    Raises:
        ValueError: If unable to generate/extract a valid token.
    """
    with _token_lock:
        current_time = int(time.time())

        cached_token = _token_cache["token"]
        cached_expiry = _token_cache["expiry"]

        if not force_refresh and cached_token and cached_expiry > (current_time + 60):
            return cast(str, cached_token)

        try:
            token = extract_jwt_token(cookie)
            if not token:
                raise ValueError("Failed to extract JWT token.")

            token_info = get_token_info(token)
            if not token_info.get("valid"):
                raise ValueError(f"Invalid token extracted: {token_info.get('error')}")

            _token_cache["token"] = token
            _token_cache["expiry"] = token_info.get("exp", current_time + 3600)
            return token

        except (ValueError, requests.RequestException, OSError) as e:
            logger.error("Token resolution failed: unable to obtain valid token")
            raise ValueError(f"Could not generate JWT token from cookies: {e}") from e
