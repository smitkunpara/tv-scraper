"""Unit tests for helper utilities.

Tests internal utility functions (offline/mocked).
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.exceptions import ExportError
from tv_scraper.utils.helpers import format_symbol, generate_user_agent
from tv_scraper.utils.io import (
    ensure_export_directory,
    generate_export_filepath,
    save_csv_file,
    save_json_file,
)


class TestEnsureExportDirectory:
    """Test export directory creation."""

    def test_creates_directory(self) -> None:
        """Verify directory creation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_export", "nested")
            ensure_export_directory(test_dir)
            assert os.path.exists(test_dir)

    def test_existing_directory_no_error(self) -> None:
        """Verify existing directory handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_export_directory(tmpdir)
            assert os.path.exists(tmpdir)

    def test_race_condition_handled(self) -> None:
        """Verify race condition handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_dir")
            os.makedirs(test_dir)
            ensure_export_directory(test_dir)
            assert os.path.exists(test_dir)

    def test_nested_directories(self) -> None:
        """Verify nested directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c", "d")
            ensure_export_directory(nested)
            assert os.path.exists(nested)


class TestGenerateExportFilepath:
    """Test export filepath generation."""

    def test_valid_json_export(self) -> None:
        """Verify JSON export path generation."""
        path = generate_export_filepath("AAPL", "candles", "json")
        assert "candles_aapl_" in path
        assert path.endswith(".json")

    def test_valid_csv_export(self) -> None:
        """Verify CSV export path generation."""
        path = generate_export_filepath("AAPL", "candles", "csv")
        assert "candles_aapl_" in path
        assert path.endswith(".csv")

    def test_with_timeframe(self) -> None:
        """Verify timeframe in path."""
        path = generate_export_filepath("AAPL", "candles", "json", "1h")
        assert "candles_aapl_1h_" in path

    def test_invalid_export_type(self) -> None:
        """Verify invalid export type raises error."""
        with pytest.raises(ExportError, match="Invalid export"):
            generate_export_filepath("AAPL", "candles", "xlsx")

    def test_sanitize_symbol(self) -> None:
        """Verify symbol sanitization."""
        path = generate_export_filepath("../etc/passwd", "candles", "json")
        assert ".." not in path
        assert "etcpasswd" in path

    def test_sanitize_data_category(self) -> None:
        """Verify data category sanitization."""
        path = generate_export_filepath("AAPL", "../../../etc", "json")
        assert ".." not in path

    def test_sanitize_timeframe(self) -> None:
        """Verify timeframe sanitization."""
        path = generate_export_filepath("AAPL", "candles", "json", "../../../1h")
        assert ".." not in path

    def test_empty_symbol(self) -> None:
        """Verify empty symbol raises error."""
        with pytest.raises(ExportError, match="Invalid symbol"):
            generate_export_filepath("", "candles", "json")

    def test_empty_data_category(self) -> None:
        """Verify empty data category raises error."""
        with pytest.raises(ExportError, match="Invalid data_category"):
            generate_export_filepath("AAPL", "", "json")


class TestSaveJsonFile:
    """Test JSON file saving."""

    def test_save_json(self) -> None:
        """Verify JSON file saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            data = {"key": "value", "number": 42}
            save_json_file(data, filepath)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                import json

                loaded = json.load(f)
            assert loaded == data

    def test_save_json_nested_data(self) -> None:
        """Verify nested data saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "nested.json")
            data = {"outer": {"inner": [1, 2, 3]}, "value": None}
            save_json_file(data, filepath)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                import json

                loaded = json.load(f)
            assert loaded == data


class TestSaveCsvFile:
    """Test CSV file saving."""

    @patch.dict("sys.modules", {"pandas": MagicMock()})
    @patch("builtins.open", create=True)
    def test_save_csv_list(self, mock_open: MagicMock) -> None:
        """Verify CSV list data saved."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
            save_csv_file(data, filepath)

    @patch.dict("sys.modules", {"pandas": MagicMock()})
    @patch("builtins.open", create=True)
    def test_save_csv_dict(self, mock_open: MagicMock) -> None:
        """Verify CSV dict data saved."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            data = {"a": [1, 3], "b": [2, 4]}
            save_csv_file(data, filepath)

    def test_invalid_data_type(self) -> None:
        """Verify invalid data type raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            with pytest.raises(ExportError, match="Data must be a list or dict"):
                save_csv_file("not valid", filepath)


class TestHelpers:
    """Test helper functions."""

    def test_generate_user_agent(self) -> None:
        """Verify user agent generation."""
        ua = generate_user_agent()
        assert isinstance(ua, str)
        assert "Googlebot" in ua or "Google-Site-Verification" in ua

    def test_format_symbol(self) -> None:
        """Verify symbol formatting."""
        result = format_symbol("NASDAQ", "aapl")
        assert result == "NASDAQ:AAPL"

    def test_format_symbol_mixed_case(self) -> None:
        """Verify mixed case symbol formatting."""
        result = format_symbol("nasdaq", "AApL")
        assert result == "NASDAQ:AAPL"

    def test_format_symbol_empty_exchange(self) -> None:
        """Verify empty exchange handling."""
        result = format_symbol("", "aapl")
        assert result == ":AAPL"

    def test_format_symbol_empty_symbol(self) -> None:
        """Verify empty symbol handling."""
        result = format_symbol("NASDAQ", "")
        assert result == "NASDAQ:"
