"""HTTP utilities for tv_scraper."""

import logging
from typing import Any

import requests

from tv_scraper.core.constants import DEFAULT_TIMEOUT
from tv_scraper.core.exceptions import NetworkError

logger = logging.getLogger(__name__)


def make_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    """Make an HTTP request with error handling.

    Args:
        url: The URL to request.
        method: HTTP method (GET, POST, etc.).
        headers: Optional request headers.
        params: Optional query parameters.
        json_data: Optional JSON body for POST requests.
        timeout: Request timeout in seconds.

    Returns:
        The HTTP response.

    Raises:
        NetworkError: If the request fails due to connection issues or timeout.
    """
    response: requests.Response | None = None
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout as e:
        raise NetworkError(f"Request timed out after {timeout}s: {url}") from e
    except requests.exceptions.ConnectionError as e:
        raise NetworkError(f"Connection error for {url}: {e}") from e
    except requests.exceptions.HTTPError as e:
        status = response.status_code if response is not None else "unknown"
        raise NetworkError(f"HTTP error {status} for {url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Request failed for {url}: {e}") from e
