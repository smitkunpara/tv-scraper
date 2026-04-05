"""Unit tests for authentication utilities.

Tests internal authentication functions (offline/mocked).
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.streaming.auth import (
    _decode_jwt_payload,
    _pad_base64,
    _token_cache,
    extract_jwt_token,
    get_token_info,
    get_valid_jwt_token,
)

VALID_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5OTk5OTk5OTksInVzZXJfaWQiOjEyM30.signature"


class TestPadBase64:
    """Test base64 padding utility."""

    def test_pad_base64_no_padding_needed(self) -> None:
        """Verify padding not needed for 4-char strings."""
        result = _pad_base64("abc")
        assert result == "abc="

    def test_pad_base64_one_char_needed(self) -> None:
        """Verify 1 char padding works."""
        result = _pad_base64("ab")
        assert result == "ab=="

    def test_pad_base64_two_chars_needed(self) -> None:
        """Verify 2 char padding works."""
        result = _pad_base64("a")
        assert result == "a==="

    def test_pad_base64_already_padded(self) -> None:
        """Verify already padded strings unchanged."""
        result = _pad_base64("abcd")
        assert result == "abcd"


class TestDecodeJwtPayload:
    """Test JWT payload decoding."""

    def test_decode_jwt_payload_valid_token(self) -> None:
        """Verify valid JWT decoding works."""
        result = _decode_jwt_payload(VALID_JWT)
        assert result is not None
        assert result["exp"] == 1999999999
        assert result["user_id"] == 123

    def test_decode_jwt_payload_invalid_format(self) -> None:
        """Verify invalid format returns None."""
        result = _decode_jwt_payload("not.a.jwt")
        assert result is None

    def test_decode_jwt_payload_empty_string(self) -> None:
        """Verify empty string returns None."""
        result = _decode_jwt_payload("")
        assert result is None

    def test_decode_jwt_payload_malformed(self) -> None:
        """Verify malformed token returns None."""
        result = _decode_jwt_payload("abc.def.ghi.jkl")
        assert result is None


class TestExtractJwtToken:
    """Test JWT token extraction from HTML."""

    @patch("requests.get")
    def test_extract_jwt_token_success(self, mock_get: MagicMock) -> None:
        """Verify successful token extraction."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            f"<html><body>some random text {VALID_JWT} more text</body></html>"
        )
        mock_get.return_value = mock_response

        token = extract_jwt_token("fake_cookie")
        assert token == VALID_JWT

    @patch("requests.get")
    def test_extract_jwt_token_fail_no_token(self, mock_get: MagicMock) -> None:
        """Verify error when no token found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>no token here</body></html>"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="JWT token not found"):
            extract_jwt_token("fake_cookie")

    def test_extract_jwt_token_empty_cookie(self) -> None:
        """Verify empty cookie raises error."""
        with pytest.raises(ValueError, match="TradingView cookie is required"):
            extract_jwt_token("")

    def test_extract_jwt_token_whitespace_only_cookie(self) -> None:
        """Verify whitespace-only cookie raises error."""
        with pytest.raises(ValueError, match="TradingView cookie is required"):
            extract_jwt_token("   ")

    def test_extract_jwt_token_none_cookie(self) -> None:
        """Verify None cookie raises error."""
        with pytest.raises(ValueError, match="TradingView cookie is required"):
            extract_jwt_token(None)  # type: ignore

    @patch("requests.get")
    def test_extract_jwt_token_request_exception(self, mock_get: MagicMock) -> None:
        """Verify network error raises appropriate error."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ValueError, match="Failed to fetch"):
            extract_jwt_token("fake_cookie")


class TestGetTokenInfo:
    """Test token info extraction."""

    def test_get_token_info_valid_token(self) -> None:
        """Verify valid token info extraction."""
        result = get_token_info(VALID_JWT)
        assert result["valid"] is True
        assert result["exp"] == 1999999999
        assert result["user_id"] == 123

    def test_get_token_info_invalid_token(self) -> None:
        """Verify invalid token handled."""
        result = get_token_info("not.valid.jwt")
        assert result["valid"] is False
        assert "error" in result

    def test_get_token_info_empty_string(self) -> None:
        """Verify empty string handled."""
        result = get_token_info("")
        assert result["valid"] is False


class TestGetValidJwtToken:
    """Test JWT token caching and retrieval."""

    def setup_method(self) -> None:
        """Clear token cache before each test."""
        _token_cache["token"] = None
        _token_cache["expiry"] = 0

    def teardown_method(self) -> None:
        """Clear token cache after each test."""
        _token_cache["token"] = None
        _token_cache["expiry"] = 0

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_returns_cached(self, mock_extract: MagicMock) -> None:
        """Verify cached token returned when valid."""
        future_time = 10000000000
        _token_cache["token"] = "cached_token"
        _token_cache["expiry"] = future_time

        result = get_valid_jwt_token("some_cookie")
        assert result == "cached_token"
        mock_extract.assert_not_called()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_force_refresh(self, mock_extract: MagicMock) -> None:
        """Verify force refresh bypasses cache."""
        future_time = 10000000000
        _token_cache["token"] = "cached_token"
        _token_cache["expiry"] = future_time
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie", force_refresh=True)
        assert result == VALID_JWT
        mock_extract.assert_called_once_with("some_cookie")

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_expired_cached(self, mock_extract: MagicMock) -> None:
        """Verify expired cache triggers new extraction."""
        _token_cache["token"] = "expired_token"
        _token_cache["expiry"] = 1
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie")
        assert result == VALID_JWT
        mock_extract.assert_called_once()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_no_cached(self, mock_extract: MagicMock) -> None:
        """Verify extraction when no cached token."""
        _token_cache["token"] = None
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie")
        assert result == VALID_JWT
        mock_extract.assert_called_once()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_extract_fails(self, mock_extract: MagicMock) -> None:
        """Verify extraction failure raises appropriate error."""
        mock_extract.side_effect = ValueError("Extraction failed")

        with pytest.raises(ValueError, match="Could not generate JWT token"):
            get_valid_jwt_token("some_cookie")
