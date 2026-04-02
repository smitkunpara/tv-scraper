import unittest
from unittest.mock import MagicMock, patch

from tv_scraper.streaming.auth import extract_jwt_token


class TestAuth(unittest.TestCase):
    @patch("requests.get")
    def test_extract_jwt_token_success(self, mock_get):
        # Mock a successful response with a fake JWT
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE5OTk5OTk5OTksInVzZXJfaWQiOjEyM30.signature"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            f"<html><body>some random text {fake_jwt} more text</body></html>"
        )
        mock_get.return_value = mock_response

        token = extract_jwt_token("fake_cookie")
        self.assertEqual(token, fake_jwt)

    @patch("requests.get")
    def test_extract_jwt_token_fail(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>no token here</body></html>"
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            extract_jwt_token("fake_cookie")


if __name__ == "__main__":
    unittest.main()
