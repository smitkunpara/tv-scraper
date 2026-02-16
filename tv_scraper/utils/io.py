"""I/O utilities for exporting data."""

import json
import logging
import os
from datetime import datetime
from typing import Any

from tv_scraper.core.exceptions import ExportError

logger = logging.getLogger(__name__)


def ensure_export_directory(directory: str) -> None:
    """Ensure the export directory exists, creating it if necessary.

    Args:
        directory: Path to the directory to ensure exists.

    Raises:
        ExportError: If the directory cannot be created.
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logger.info("Directory %s created.", directory)
        except Exception as e:
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
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    symbol_part = f"{symbol.lower()}_" if symbol else ""
    timeframe_part = f"{timeframe}_" if timeframe else ""
    extension = f".{export_type}"
    root_path = os.getcwd()
    return os.path.join(
        root_path, "export", f"{data_category}_{symbol_part}{timeframe_part}{timestamp}{extension}"
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
    except (TypeError, IOError, PermissionError) as e:
        raise ExportError(f"Failed to save JSON file {filepath}: {e}") from e


def save_csv_file(data: Any, filepath: str) -> None:
    """Save data to a CSV file using pandas.

    Args:
        data: Data suitable for ``pandas.DataFrame.from_dict()``.
        filepath: Full path of the output file.

    Raises:
        ExportError: If the file cannot be written.
    """
    ensure_export_directory(os.path.dirname(filepath))
    try:
        import pandas as pd

        df = pd.DataFrame.from_dict(data)
        df.to_csv(filepath, index=False)
        logger.info("CSV file saved at: %s", filepath)
    except (ValueError, IOError, PermissionError) as e:
        raise ExportError(f"Failed to save CSV file {filepath}: {e}") from e
