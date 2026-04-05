"""I/O utilities for exporting data."""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any

from tv_scraper.core.exceptions import ExportError

logger = logging.getLogger(__name__)

ALLOWED_EXPORT_TYPES = frozenset({"json", "csv"})


def _sanitize_filename_part(part: str, name: str) -> str:
    """Sanitize a filename component to prevent path traversal."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", part)
    if not sanitized:
        raise ExportError(
            f"Invalid {name}: contains no valid characters after sanitization"
        )
    return sanitized


def ensure_export_directory(directory: str) -> None:
    """Ensure the export directory exists, creating it if necessary.

    Args:
        directory: Path to the directory to ensure exists.

    Raises:
        ExportError: If the directory cannot be created.
    """
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        raise ExportError(f"Error creating directory {directory}: {e}") from e


def generate_export_filepath(
    symbol: str,
    data_category: str,
    export_type: str,
    timeframe: str | None = None,
) -> str:
    """Generate a file path for exporting data, including a timestamp.

    Args:
        symbol: The symbol name (will be lowercased).
        data_category: The data category prefix.
        export_type: File extension type (``"json"`` or ``"csv"``).
        timeframe: Optional timeframe suffix (e.g. ``"1M"``, ``"1W"``).

    Returns:
        Full file path like ``export/category_symbol_timeframe_20260215-120000.json``.

    Raises:
        ExportError: If export_type is invalid or filename components are invalid.
    """
    if export_type not in ALLOWED_EXPORT_TYPES:
        raise ExportError(
            f"Invalid export_type '{export_type}'. Must be one of {list(ALLOWED_EXPORT_TYPES)}"
        )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    symbol_part = f"{_sanitize_filename_part(symbol, 'symbol').lower()}_"
    timeframe_part = (
        f"{_sanitize_filename_part(timeframe, 'timeframe')}_" if timeframe else ""
    )
    extension = f".{export_type}"
    return os.path.join(
        os.getcwd(),
        "export",
        f"{_sanitize_filename_part(data_category, 'data_category')}_{symbol_part}{timeframe_part}{timestamp}{extension}",
    )


def save_json_file(data: Any, filepath: str) -> None:
    """Save data to a JSON file.

    Args:
        data: The data to serialize to JSON.
        filepath: Full path of the output file.

    Raises:
        ExportError: If the file cannot be written.
    """
    ensure_export_directory(os.path.dirname(filepath))
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("JSON file saved at: %s", filepath)
    except (OSError, TypeError, PermissionError) as e:
        raise ExportError(f"Failed to save JSON file {filepath}: {e}") from e


def save_csv_file(data: Any, filepath: str) -> None:
    """Save data to a CSV file using pandas.

    Args:
        data: Data suitable for ``pandas.DataFrame.from_dict()``.
        filepath: Full path of the output file.

    Raises:
        ExportError: If the file cannot be written.
    """
    if not isinstance(data, (list, dict)):
        raise ExportError(
            f"Data must be a list or dict for CSV export, got {type(data).__name__}"
        )

    ensure_export_directory(os.path.dirname(filepath))
    try:
        import pandas as pd
    except ImportError as e:
        raise ExportError(f"pandas is required for CSV export: {e}") from e

    try:
        df = pd.DataFrame.from_dict(data)
        df.to_csv(filepath, index=False)
        logger.info("CSV file saved at: %s", filepath)
    except (OSError, ValueError, PermissionError) as e:
        raise ExportError(f"Failed to save CSV file {filepath}: {e}") from e
