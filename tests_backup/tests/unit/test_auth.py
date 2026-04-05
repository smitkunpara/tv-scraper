import unittest
from unittest.mock import MagicMock, patch

from tv_scraper.streaming.auth import (
    _decode_jwt_payload,
    _pad_base64,
    _token_cache,
    extract_jwt_token,
    get_token_info,
    get_valid_jwt_token,
)

VALID_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5OTk5OTk5OTksInVzZXJfaWQiOjEyM30.signature"


class TestAuthHelpers(unittest.TestCase):
    def test_pad_base64_no_padding_needed(self):
        result = _pad_base64("abc")
        self.assertEqual(result, "abc=")

    def test_pad_base64_one_char_needed(self):
        result = _pad_base64("ab")
        self.assertEqual(result, "ab==")

    def test_pad_base64_two_chars_needed(self):
        result = _pad_base64("a")
        self.assertEqual(result, "a===")

    def test_pad_base64_already_padded(self):
        result = _pad_base64("abcd")
        self.assertEqual(result, "abcd")

    def test_decode_jwt_payload_valid_token(self):
        result = _decode_jwt_payload(VALID_JWT)
        self.assertIsNotNone(result)
        self.assertEqual(result["exp"], 1999999999)
        self.assertEqual(result["user_id"], 123)

    def test_decode_jwt_payload_invalid_format(self):
        result = _decode_jwt_payload("not.a.jwt")
        self.assertIsNone(result)

    def test_decode_jwt_payload_empty_string(self):
        result = _decode_jwt_payload("")
        self.assertIsNone(result)


class TestExtractJwtToken(unittest.TestCase):
    @patch("requests.get")
    def test_extract_jwt_token_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            f"<html><body>some random text {VALID_JWT} more text</body></html>"
        )
        mock_get.return_value = mock_response

        token = extract_jwt_token("fake_cookie")
        self.assertEqual(token, VALID_JWT)

    @patch("requests.get")
    def test_extract_jwt_token_fail_no_token(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>no token here</body></html>"
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            extract_jwt_token("fake_cookie")

    def test_extract_jwt_token_empty_cookie(self):
        with self.assertRaises(ValueError):
            extract_jwt_token("")

    def test_extract_jwt_token_whitespace_only_cookie(self):
        with self.assertRaises(ValueError):
            extract_jwt_token("   ")

    def test_extract_jwt_token_none_cookie(self):
        with self.assertRaises(ValueError):
            extract_jwt_token(None)  # type: ignore

    @patch("requests.get")
    def test_extract_jwt_token_request_exception(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        with self.assertRaises(ValueError) as ctx:
            extract_jwt_token("fake_cookie")
        self.assertIn("Failed to fetch", str(ctx.exception))


class TestGetTokenInfo(unittest.TestCase):
    def test_get_token_info_valid_token(self):
        result = get_token_info(VALID_JWT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["exp"], 1999999999)
        self.assertEqual(result["user_id"], 123)

    def test_get_token_info_invalid_token(self):
        result = get_token_info("not.valid.jwt")
        self.assertFalse(result["valid"])
        self.assertIn("error", result)

    def test_get_token_info_empty_string(self):
        result = get_token_info("")
        self.assertFalse(result["valid"])


class TestGetValidJwtToken(unittest.TestCase):
    def setUp(self):
        _token_cache["token"] = None
        _token_cache["expiry"] = 0

    def tearDown(self):
        _token_cache["token"] = None
        _token_cache["expiry"] = 0

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_returns_cached(self, mock_extract):
        future_time = 10000000000
        _token_cache["token"] = "cached_token"
        _token_cache["expiry"] = future_time

        result = get_valid_jwt_token("some_cookie")
        self.assertEqual(result, "cached_token")
        mock_extract.assert_not_called()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_force_refresh(self, mock_extract):
        future_time = 10000000000
        _token_cache["token"] = "cached_token"
        _token_cache["expiry"] = future_time
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie", force_refresh=True)
        self.assertEqual(result, VALID_JWT)
        mock_extract.assert_called_once_with("some_cookie")

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_expired_cached(self, mock_extract):
        _token_cache["token"] = "expired_token"
        _token_cache["expiry"] = 1
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie")
        self.assertEqual(result, VALID_JWT)
        mock_extract.assert_called_once()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_no_cached(self, mock_extract):
        _token_cache["token"] = None
        mock_extract.return_value = VALID_JWT

        result = get_valid_jwt_token("some_cookie")
        self.assertEqual(result, VALID_JWT)
        mock_extract.assert_called_once()

    @patch("tv_scraper.streaming.auth.extract_jwt_token")
    def test_get_valid_jwt_token_extract_fails(self, mock_extract):
        mock_extract.side_effect = ValueError("Extraction failed")

        with self.assertRaises(ValueError) as ctx:
            get_valid_jwt_token("some_cookie")
        self.assertIn("Could not generate JWT token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
