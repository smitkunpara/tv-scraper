"""Unit tests for utils module."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tv_scraper.core.exceptions import ExportError
from tv_scraper.utils.helpers import format_symbol, generate_user_agent
from tv_scraper.utils.io import (
    ensure_export_directory,
    generate_export_filepath,
    save_csv_file,
    save_json_file,
)


class TestEnsureExportDirectory(unittest.TestCase):
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_export", "nested")
            ensure_export_directory(test_dir)
            self.assertTrue(os.path.exists(test_dir))

    def test_existing_directory_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_export_directory(tmpdir)
            self.assertTrue(os.path.exists(tmpdir))

    def test_race_condition_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_dir")
            os.makedirs(test_dir)
            ensure_export_directory(test_dir)
            self.assertTrue(os.path.exists(test_dir))


class TestGenerateExportFilepath(unittest.TestCase):
    def test_valid_json_export(self):
        path = generate_export_filepath("AAPL", "candles", "json")
        self.assertIn("candles_aapl_", path)
        self.assertTrue(path.endswith(".json"))

    def test_valid_csv_export(self):
        path = generate_export_filepath("AAPL", "candles", "csv")
        self.assertIn("candles_aapl_", path)
        self.assertTrue(path.endswith(".csv"))

    def test_with_timeframe(self):
        path = generate_export_filepath("AAPL", "candles", "json", "1h")
        self.assertIn("candles_aapl_1h_", path)

    def test_invalid_export_type(self):
        with self.assertRaises(ExportError) as ctx:
            generate_export_filepath("AAPL", "candles", "xlsx")
        self.assertIn("Invalid export_type", str(ctx.exception))

    def test_sanitize_symbol(self):
        path = generate_export_filepath("../etc/passwd", "candles", "json")
        self.assertNotIn("..", path)
        self.assertIn("etcpasswd", path)

    def test_sanitize_data_category(self):
        path = generate_export_filepath("AAPL", "../../../etc", "json")
        self.assertNotIn("..", path)

    def test_sanitize_timeframe(self):
        path = generate_export_filepath("AAPL", "candles", "json", "../../../1h")
        self.assertNotIn("..", path)


class TestSaveJsonFile(unittest.TestCase):
    def test_save_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            data = {"key": "value", "number": 42}
            save_json_file(data, filepath)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath) as f:
                loaded = eval(f.read())
            self.assertEqual(loaded, data)


class TestSaveCsvFile(unittest.TestCase):
    @patch.dict("sys.modules", {"pandas": MagicMock()})
    @patch("builtins.open", create=True)
    def test_save_csv_list(self, mock_open):
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
            save_csv_file(data, filepath)

    @patch.dict("sys.modules", {"pandas": MagicMock()})
    @patch("builtins.open", create=True)
    def test_save_csv_dict(self, mock_open):
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            data = {"a": [1, 3], "b": [2, 4]}
            save_csv_file(data, filepath)

    def test_invalid_data_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.csv")
            with self.assertRaises(ExportError) as ctx:
                save_csv_file("not valid", filepath)
            self.assertIn("must be a list or dict", str(ctx.exception))


class TestHelpers(unittest.TestCase):
    def test_generate_user_agent(self):
        ua = generate_user_agent()
        self.assertIsInstance(ua, str)
        self.assertIn("Google", ua)

    def test_format_symbol(self):
        result = format_symbol("NASDAQ", "aapl")
        self.assertEqual(result, "NASDAQ:AAPL")

    def test_format_symbol_mixed_case(self):
        result = format_symbol("nasdaq", "AApL")
        self.assertEqual(result, "NASDAQ:AAPL")


if __name__ == "__main__":
    unittest.main()
