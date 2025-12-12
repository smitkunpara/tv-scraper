"""Module providing a function to scrape Minds community discussions from TradingView."""

from typing import Optional, Dict, List
from datetime import datetime

import requests

from tradingview_scraper.symbols.utils import (
    save_csv_file,
    save_json_file,
    generate_user_agent,
)


class Minds:
    """
    A class to scrape Minds community discussions and insights from TradingView.

    This class provides functionality to retrieve community-generated content including
    questions, discussions, trading ideas, and sentiment from TradingView's Minds feature.

    Attributes:
        export_result (bool): Flag to determine if results should be exported to file.
        export_type (str): Type of export format ('json' or 'csv').
        headers (dict): HTTP headers for requests.

    Example:
        >>> minds = Minds(export_result=True, export_type='json')
        >>> discussions = minds.get_minds(symbol='NASDAQ:AAPL', limit=20)
        >>> print(discussions['data'])
    """

    # Minds API endpoint
    MINDS_API_URL = 'https://www.tradingview.com/api/v1/minds/'

    def __init__(self, export_result: bool = False, export_type: str = 'json'):
        """
        Initialize the Minds scraper.

        Args:
            export_result (bool): Whether to export results to a file. Defaults to False.
            export_type (str): Export format ('json' or 'csv'). Defaults to 'json'.
        """
        self.export_result = export_result
        self.export_type = export_type
        self.headers = {"User-Agent": generate_user_agent()}

    def _validate_symbol(self, symbol: str) -> str:
        """
        Validate and format symbol.

        Args:
            symbol (str): The symbol to validate.

        Returns:
            str: Formatted symbol.

        Raises:
            ValueError: If symbol is invalid.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

        symbol = symbol.strip().upper()

        # Add exchange prefix if not present
        if ':' not in symbol:
            raise ValueError(
                "Symbol must include exchange prefix (e.g., 'NASDAQ:AAPL', 'BITSTAMP:BTCUSD')"
            )

        return symbol

    def _parse_mind(self, item: Dict) -> Dict:
        """
        Parse a single mind item.

        Args:
            item (Dict): Raw mind item from API.

        Returns:
            Dict: Parsed mind data.
        """
        # Parse author info
        author = item.get('author', {})
        author_data = {
            'username': author.get('username'),
            'profile_url': f"https://www.tradingview.com{author.get('uri', '')}",
            'is_broker': author.get('is_broker', False),
        }

        # Parse created date
        created = item.get('created', '')
        try:
            created_datetime = datetime.fromisoformat(
                created.replace('Z', '+00:00')
            )
            created_formatted = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            created_formatted = created

        # Parse symbols mentioned
        symbols = item.get('symbols', {})
        symbols_list = list(symbols.values()) if symbols else []

        # Build parsed data
        parsed = {
            'uid': item.get('uid'),
            'text': item.get('text', ''),
            'url': item.get('url', ''),
            'author': author_data,
            'created': created_formatted,
            'symbols': symbols_list,
            'total_likes': item.get('total_likes', 0),
            'total_comments': item.get('total_comments', 0),
            'modified': item.get('modified', False),
            'hidden': item.get('hidden', False),
        }

        return parsed

    def get_minds(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Get Minds discussions for a symbol from the first page.

        This method retrieves community discussions for the specified symbol
        from the first page only (no pagination).

        Args:
            symbol (str): The symbol to get discussions for (e.g., 'NASDAQ:AAPL').
            limit (int, optional): Maximum number of results to retrieve from the first page.

        Returns:
            dict: A dictionary containing:
                - status (str): 'success' or 'failed'
                - data (List[Dict]): List of minds discussions
                - total (int): Total number of results retrieved
                - symbol_info (Dict): Information about the symbol
                - pages (int): Number of pages retrieved (always 1)
                - error (str): Error message if failed

        Example:
            >>> minds = Minds()
            >>>
            >>> # Get discussions for Apple from first page
            >>> aapl_minds = minds.get_minds(symbol='NASDAQ:AAPL')
            >>>
            >>> # Get up to 50 discussions for Bitcoin from first page
            >>> btc_minds = minds.get_minds(symbol='BITSTAMP:BTCUSD', limit=50)
        """
        try:
            # Validate inputs
            symbol = self._validate_symbol(symbol)

            # Build parameters
            params = {
                'symbol': symbol,
            }

            # Make request
            response = requests.get(
                self.MINDS_API_URL,
                params=params,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                return {
                    'status': 'failed',
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

            json_response = response.json()
            results = json_response.get('results', [])

            if not results:
                return {
                    'status': 'failed',
                    'error': f'No discussions found for symbol: {symbol}'
                }

            # Parse data
            parsed_data = [self._parse_mind(item) for item in results]

            # Apply limit if specified
            if limit is not None and len(parsed_data) > limit:
                parsed_data = parsed_data[:limit]

            # Get symbol info
            meta = json_response.get('meta', {})
            symbol_info = meta.get('symbols_info', {}).get(symbol, {})

            # Export if requested
            if self.export_result and parsed_data:
                self._export(
                    data=parsed_data,
                    symbol=symbol.replace(':', '_'),
                    data_category='minds'
                )

            return {
                'status': 'success',
                'data': parsed_data,
                'total': len(parsed_data),
                'pages': 1,
                'symbol_info': symbol_info
            }

        except ValueError as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
        except requests.RequestException as e:
            return {
                'status': 'failed',
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Request failed: {str(e)}'
            }

    def _export(
        self,
        data: List[Dict],
        symbol: Optional[str] = None,
        data_category: Optional[str] = None
    ) -> None:
        """
        Export scraped data to file.

        Args:
            data (List[Dict]): The data to export.
            symbol (str, optional): Symbol identifier for the filename.
            data_category (str, optional): Data category for the filename.
        """
        if self.export_type == 'json':
            save_json_file(data=data, symbol=symbol, data_category=data_category)
        elif self.export_type == 'csv':
            save_csv_file(data=data, symbol=symbol, data_category=data_category)
