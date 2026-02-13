"""Tests for shared utility functions in tradingview_scraper.symbols.utils."""

import os
import sys
import json
import pytest
from unittest import mock

# Add the current working directory to the system path
path = str(os.getcwd())
if path not in sys.path:
    sys.path.append(path)

from tradingview_scraper.symbols.utils import (
    validate_symbol,
    validate_string_array,
    generate_user_agent,
    load_text_file,
    load_json_file,
    ensure_export_directory,
    generate_export_filepath,
    save_json_file,
    save_csv_file,
)


class TestValidateSymbol:
    """Tests for the validate_symbol utility function."""

    def test_valid_symbol(self):
        """Test that a valid symbol is returned uppercased."""
        result = validate_symbol("NASDAQ:AAPL")
        assert result == "NASDAQ:AAPL"

    def test_valid_symbol_lowercase(self):
        """Test that a lowercase symbol is uppercased."""
        result = validate_symbol("nasdaq:aapl")
        assert result == "NASDAQ:AAPL"

    def test_valid_symbol_with_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_symbol("  NASDAQ:AAPL  ")
        assert result == "NASDAQ:AAPL"

    def test_empty_string_raises(self):
        """Test that an empty string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_symbol("")

    def test_none_raises(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_symbol(None)  # type: ignore[arg-type]

    def test_no_colon_raises(self):
        """Test that a symbol without a colon raises ValueError."""
        with pytest.raises(ValueError, match="exchange prefix"):
            validate_symbol("AAPL")

    def test_integer_raises(self):
        """Test that a non-string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_symbol(123)  # type: ignore[arg-type]


class TestValidateStringArray:
    """Tests for the validate_string_array utility function."""

    def test_valid_array(self):
        """Test validation with all valid values."""
        assert validate_string_array(["a", "b"], ["a", "b", "c"]) is True

    def test_invalid_value(self):
        """Test validation with an invalid value."""
        assert validate_string_array(["a", "x"], ["a", "b", "c"]) is False

    def test_empty_data(self):
        """Test validation with empty data list."""
        assert validate_string_array([], ["a", "b"]) is False

    def test_none_data(self):
        """Test validation with None data."""
        assert validate_string_array(None, ["a", "b"]) is False  # type: ignore[arg-type]

    def test_single_valid(self):
        """Test validation with a single valid value."""
        assert validate_string_array(["a"], ["a", "b"]) is True


class TestGenerateUserAgent:
    """Tests for the generate_user_agent utility function."""

    def test_returns_string(self):
        """Test that a string is returned."""
        ua = generate_user_agent()
        assert isinstance(ua, str)

    def test_contains_googlebot(self):
        """Test that the user agent contains Googlebot or Google-related string."""
        ua = generate_user_agent()
        assert "Google" in ua or "google" in ua


class TestLoadTextFile:
    """Tests for the load_text_file utility function."""

    def test_load_exchanges(self):
        """Test loading the exchanges.txt file."""
        result = load_text_file('data/exchanges.txt')
        assert isinstance(result, list)
        assert len(result) > 0
        assert "BINANCE" in result or "NASDAQ" in result

    def test_load_indicators(self):
        """Test loading the indicators.txt file."""
        result = load_text_file('data/indicators.txt')
        assert isinstance(result, list)
        assert len(result) > 0

    def test_nonexistent_file(self):
        """Test that a nonexistent file returns empty list."""
        result = load_text_file('data/nonexistent.txt')
        assert result == []


class TestLoadJsonFile:
    """Tests for the load_json_file utility function."""

    def test_load_timeframes(self):
        """Test loading the timeframes.json file."""
        result = load_json_file('data/timeframes.json')
        assert isinstance(result, dict)
        assert 'indicators' in result

    def test_load_languages(self):
        """Test loading the languages.json file."""
        result = load_json_file('data/languages.json')
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_load_areas(self):
        """Test loading the areas.json file."""
        result = load_json_file('data/areas.json')
        assert result is not None

    def test_nonexistent_file_returns_default(self):
        """Test that a nonexistent file returns default value."""
        result = load_json_file('data/nonexistent.json', default={"fallback": True})
        assert result == {"fallback": True}

    def test_nonexistent_file_returns_none(self):
        """Test that a nonexistent file returns None by default."""
        result = load_json_file('data/nonexistent.json')
        assert result is None


class TestExportFunctions:
    """Tests for export-related utility functions."""

    def test_generate_export_filepath(self):
        """Test that export filepath is generated correctly."""
        path = generate_export_filepath("BTCUSD", "indicators", "1d", ".json")
        assert "indicators_btcusd_1d_" in path
        assert path.endswith(".json")

    def test_generate_export_filepath_no_symbol(self):
        """Test filepath generation with no symbol."""
        path = generate_export_filepath(None, "news", "", ".csv")
        assert "news_" in path
        assert path.endswith(".csv")

    def test_ensure_export_directory(self, tmp_path):
        """Test that export directory is created."""
        test_dir = str(tmp_path / "test_export")
        ensure_export_directory(test_dir)
        assert os.path.exists(test_dir)

    def test_save_json_file(self, tmp_path):
        """Test saving data to JSON file."""
        test_data = {"key": "value"}
        with mock.patch('tradingview_scraper.symbols.utils.generate_export_filepath',
                       return_value=str(tmp_path / "test.json")):
            save_json_file(test_data, symbol="TEST", data_category="test")
            # Verify file was created
            output_file = tmp_path / "test.json"
            assert output_file.exists()
            with open(output_file) as f:
                saved_data = json.load(f)
            assert saved_data == test_data

    def test_save_csv_file(self, tmp_path):
        """Test saving data to CSV file."""
        test_data = [{"col1": "val1", "col2": "val2"}]
        with mock.patch('tradingview_scraper.symbols.utils.generate_export_filepath',
                       return_value=str(tmp_path / "test.csv")):
            save_csv_file(test_data, symbol="TEST", data_category="test")
            output_file = tmp_path / "test.csv"
            assert output_file.exists()


class TestEarningsIndexMapping:
    """Tests to verify the earnings index mapping fix in CalendarScraper."""

    @mock.patch('tradingview_scraper.symbols.cal.requests.post')
    def test_earnings_default_mapping_correct(self, mock_post):
        """Test that default earnings field mapping correctly uses offset indices."""
        from tradingview_scraper.symbols.cal import CalendarScraper

        # Build mock data with 22 fields matching default_fetch_values order
        mock_event_data = [
            1700000000,     # [0] earnings_release_next_date
            1699900000,     # [1] earnings_release_date (skipped in TypedDict)
            "apple-logo",   # [2] logoid
            "Apple Inc",    # [3] name
            "Technology",   # [4] description
            3.89,           # [5] earnings_per_share_fq
            4.05,           # [6] earnings_per_share_forecast_next_fq
            0.12,           # [7] eps_surprise_fq
            3.18,           # [8] eps_surprise_percent_fq
            94836000000,    # [9] revenue_fq
            95000000000,    # [10] revenue_forecast_next_fq
            2950000000000,  # [11] market_cap_basic
            1,              # [12] earnings_release_time
            2,              # [13] earnings_release_next_time
            3.85,           # [14] earnings_per_share_forecast_fq
            93000000000,    # [15] revenue_forecast_fq
            "USD",          # [16] fundamental_currency_code
            "america",      # [17] market
            0,              # [18] earnings_publication_type_fq
            1,              # [19] earnings_publication_type_next_fq
            1836000000,     # [20] revenue_surprise_fq
            1.97,           # [21] revenue_surprise_percent_fq
        ]

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = mock.Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "s": "NASDAQ:AAPL",
                    "d": mock_event_data
                }
            ]
        }
        mock_post.return_value = mock_response

        scraper = CalendarScraper()
        result = scraper.scrape_earnings()

        assert len(result) == 1
        event = result[0]
        assert event.get("full_symbol") == "NASDAQ:AAPL"
        # Key test: verify logoid maps to index 2 (not index 1)
        assert event.get("logoid") == "apple-logo"
        assert event.get("name") == "Apple Inc"
        assert event.get("description") == "Technology"
        assert event.get("earnings_per_share_fq") == 3.89
        assert event.get("fundamental_currency_code") == "USD"
        assert event.get("market") == "america"
        assert event.get("revenue_surprise_percent_fq") == 1.97
