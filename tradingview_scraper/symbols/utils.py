import os
import json
import logging
import random
from datetime import datetime
from importlib import resources
from typing import List

logger = logging.getLogger(__name__)


def ensure_export_directory(path='/export'):
    """Check if the export directory exists, and create it if it does not.

    Parameters
    ----------
    path : str, optional
        The path to the export directory. Defaults to '/export'.

    Raises
    ------
    Exception
        If there is an error creating the directory.
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            logger.info("Directory %s created.", path)
        except Exception as e:
            logger.error("Error creating directory %s: %s", path, e)

def generate_export_filepath(symbol, data_category, timeframe, file_extension):
    """Generate a file path for exporting data, including the current timestamp.

    This function constructs a file path based on the provided symbol, data category,
    and file extension. The generated path will include a timestamp to ensure uniqueness.

    Parameters
    ----------
    symbol : str
        The symbol to include in the file name, formatted in lowercase.
    data_category : str
        The category of data being exported, which will be prefixed in the file name.
    file_extension : str
        The file extension for the export file (e.g., '.json', '.csv').
    timeframe: str
        Timeframe of report like (e.g., '1M', '1W').

    Returns
    -------
    str
        The generated file path, structured as:
        "<current_directory>/export/<data_category>_<symbol>_<timestamp><file_extension>".
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    symbol_lower = f'{symbol.lower()}_' if symbol else ''
    timeframe = f'{timeframe}_' if timeframe else ''
    root_path = os.getcwd()
    path = os.path.join(root_path, "export", f"{data_category}_{symbol_lower}{timeframe}{timestamp}{file_extension}")
    return path

def save_json_file(data, **kwargs):
    """
    Save the provided data to a JSON file with a generated file path.

    This function creates a JSON file using the specified symbol and data category
    to generate a unique file name. The file is saved in the 'export' directory.

    Parameters
    ----------
    data : dict
        The data to be saved in the JSON file. Must be serializable to JSON format.
    **kwargs : dict
        Additional parameters for file naming:
        - symbol (str): The symbol to include in the file name, formatted to lowercase.
        - data_category (str): The category of the data, used to distinguish between different datasets.
        - timeframe (str, optional): The timeframe for the data, which can be included in the file name. Defaults to an empty string.

    Raises
    ------
    FileNotFoundError
        If the directory for the output path does not exist.
    PermissionError
        If permission is denied when trying to write to the file.
    TypeError
        If the data provided is not serializable to JSON.
    Exception
        For any unexpected errors that may occur during file writing.
    """
    symbol = kwargs.get('symbol')
    data_category = kwargs.get('data_category')
    timeframe = kwargs.get('timeframe', '')
    
    output_path = generate_export_filepath(symbol, data_category, timeframe, '.json')
    ensure_export_directory(os.path.dirname(output_path))  # Ensure the directory exists
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("JSON file saved at: %s", output_path)
    except FileNotFoundError:
        logger.error("The directory for %s does not exist.", output_path)
    except PermissionError:
        logger.error("Permission denied when trying to write to %s.", output_path)
    except TypeError as e:
        logger.error("The data provided is not serializable. %s", e)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)

def save_csv_file(data, **kwargs):
    """
    Save the provided data to a CSV file with a generated file path.

    This function creates a CSV file using the specified symbol and data category
    to generate a unique file name. The file is saved in the 'export' directory.

    Parameters
    ----------
    data : dict
        The data to be saved in the CSV file. Must be in a suitable format for a DataFrame.
    **kwargs : dict
        Additional parameters for file naming:
        - symbol (str): The symbol to include in the file name, formatted to lowercase.
        - data_category (str): The category of the data, used to distinguish between different datasets.
        - timeframe (str, optional): The timeframe for the data, which can be included in the file name. Defaults to an empty string.

    Raises
    ------
    ValueError
        If the data provided is not in a suitable format for a DataFrame.
    FileNotFoundError
        If the directory for the output path does not exist.
    PermissionError
        If permission is denied when trying to write to the file.
    Exception
        For any unexpected errors that may occur during file writing.
    """
    symbol = kwargs.get('symbol')
    data_category = kwargs.get('data_category')
    timeframe = kwargs.get('timeframe', '')

    output_path = generate_export_filepath(symbol, data_category, timeframe, '.csv')
    ensure_export_directory(os.path.dirname(output_path))  # Ensure the directory exists
    try:
        import pandas as pd
        df = pd.DataFrame.from_dict(data)
        df.to_csv(output_path, index=False)
        logger.info("CSV file saved at: %s", output_path)
    except ValueError as e:
        logger.error("The data provided is not in a suitable format for a DataFrame. %s", e)
    except FileNotFoundError:
        logger.error("The directory for %s does not exist.", output_path)
    except PermissionError:
        logger.error("Permission denied when trying to write to %s.", output_path)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)

def generate_user_agent():
    """
    Generates a random user agent string from a predefined list of Google bot user agents.

    Returns
    -------
    str
        A random Google bot user agent string.
    """
    user_agents = [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-Image/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-News; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-Video/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-AdsBot/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Google-Site-Verification/1.0; +http://www.google.com/bot.html)"
    ]
    
    return random.choice(user_agents)

def validate_string_array(data: List[str], valid_values: List[str]) -> bool:
    """
    Validates a list of strings against a list of valid values.

    This function checks if each item in the provided list of strings is present in the list of valid values.

    Parameters
    ----------
    data : list[str]
        The list of strings to validate.

    valid_values : list[str]
        The list of valid values to check against.

    Returns
    -------
    bool
        True if all items in the data list are valid, False otherwise.
    """
    
    if not data:
        return False

    for item in data:
        if item not in valid_values:
            return False
    
    return True


def validate_symbol(symbol: str) -> str:
    """Validate and format a trading symbol.

    Ensures the symbol is a non-empty string and contains an exchange prefix
    (e.g., 'NASDAQ:AAPL', 'BITSTAMP:BTCUSD').

    Parameters
    ----------
    symbol : str
        The symbol to validate.

    Returns
    -------
    str
        The validated and uppercased symbol.

    Raises
    ------
    ValueError
        If the symbol is empty, not a string, or missing an exchange prefix.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")

    symbol = symbol.strip().upper()

    if ':' not in symbol:
        raise ValueError(
            "Symbol must include exchange prefix (e.g., 'NASDAQ:AAPL', 'BITSTAMP:BTCUSD')"
        )

    return symbol


def load_text_file(relative_path: str) -> list:
    """Load lines from a text file in the package's data directory.

    Parameters
    ----------
    relative_path : str
        Path relative to the ``tradingview_scraper`` package root,
        e.g. ``'data/exchanges.txt'``.

    Returns
    -------
    list[str]
        A list of stripped lines. Returns an empty list on error.
    """
    path = str(resources.files('tradingview_scraper') / relative_path)
    if not os.path.exists(path):
        logger.error("File not found at %s.", path)
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except IOError as e:
        logger.error("Error reading file %s: %s", path, e)
        return []


def load_json_file(relative_path: str, default=None):
    """Load and parse a JSON file from the package's data directory.

    Parameters
    ----------
    relative_path : str
        Path relative to the ``tradingview_scraper`` package root,
        e.g. ``'data/timeframes.json'``.
    default : any, optional
        Value to return if the file cannot be loaded. Defaults to ``None``.

    Returns
    -------
    any
        The parsed JSON content, or *default* on error.
    """
    path = str(resources.files('tradingview_scraper') / relative_path)
    if not os.path.exists(path):
        logger.error("File not found at %s.", path)
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error("Error reading file %s: %s", path, e)
        return default
