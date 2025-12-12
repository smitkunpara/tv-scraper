import os
import sys
import pytest
from unittest import mock

# Add the current working directory to the system path
path = str(os.getcwd())
if path not in sys.path:
    sys.path.append(path)

from tradingview_scraper.symbols.minds import Minds


class TestMinds:
    @pytest.fixture
    def minds(self):
        """Fixture to create an instance of Minds for testing."""
        return Minds(export_result=False)

    def test_validate_symbol_valid(self, minds):
        """Test validation of valid symbols."""
        assert minds._validate_symbol('NASDAQ:AAPL') == 'NASDAQ:AAPL'
        assert minds._validate_symbol('bitstamp:btcusd') == 'BITSTAMP:BTCUSD'
        assert minds._validate_symbol(' NYSE:TSLA ') == 'NYSE:TSLA'

    def test_validate_symbol_invalid(self, minds):
        """Test validation of invalid symbols."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            minds._validate_symbol('')

        with pytest.raises(ValueError, match="must include exchange prefix"):
            minds._validate_symbol('AAPL')

    @mock.patch('tradingview_scraper.symbols.minds.requests.get')
    def test_get_minds_success(self, mock_get, minds):
        """Test successful retrieval of minds."""
        # Mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'text': 'Test discussion about AAPL',
                    'symbols': {'AAPL': 'NASDAQ:AAPL'},
                    'uid': 'test123',
                    'url': 'https://www.tradingview.com/minds/test',
                    'author': {
                        'username': 'testuser',
                        'uri': '/u/testuser/',
                        'is_broker': False
                    },
                    'created': '2025-01-07T12:00:00+00:00',
                    'total_likes': 10,
                    'total_comments': 5,
                    'modified': False,
                    'hidden': False
                }
            ],
            'next': '',
            'meta': {
                'symbol': 'NASDAQ:AAPL',
                'symbols_info': {
                    'NASDAQ:AAPL': {
                        'short_name': 'AAPL',
                        'exchange': 'NASDAQ'
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        # Get minds
        result = minds.get_minds(symbol='NASDAQ:AAPL', limit=10)

        # Assertions
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 1
        assert result['data'][0]['text'] == 'Test discussion about AAPL'
        assert result['data'][0]['author']['username'] == 'testuser'
        assert 'symbol_info' in result
        assert result['symbol_info']['short_name'] == 'AAPL'

    @mock.patch('tradingview_scraper.symbols.minds.requests.get')
    def test_get_minds_no_data(self, mock_get, minds):
        """Test getting minds with no data."""
        # Mock response with empty results
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [],
            'meta': {}
        }
        mock_get.return_value = mock_response
        result = minds.get_minds(symbol='NASDAQ:INVALID')

        # Assertions
        assert result['status'] == 'failed'
        assert 'error' in result

    @mock.patch('tradingview_scraper.symbols.minds.requests.get')
    def test_get_minds_http_error(self, mock_get, minds):
        """Test getting minds with HTTP error."""
        # Mock error response
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        result = minds.get_minds(symbol='NASDAQ:AAPL')

        # Assertions
        assert result['status'] == 'failed'
        assert 'error' in result

    @mock.patch('tradingview_scraper.symbols.minds.requests.get')
    def test_get_minds_request_exception(self, mock_get, minds):
        """Test getting minds with request exception."""
        # Mock exception
        mock_get.side_effect = Exception('Connection error')

        result = minds.get_minds(symbol='NASDAQ:AAPL')

        # Assertions
        assert result['status'] == 'failed'
        assert 'error' in result

    def test_invalid_symbol_format(self, minds):
        """Test getting minds with invalid symbol format."""
        result = minds.get_minds(symbol='AAPL')

        # Assertions
        assert result['status'] == 'failed'
        assert 'must include exchange prefix' in result['error']

    def test_empty_symbol(self, minds):
        """Test getting minds with empty symbol."""
        result = minds.get_minds(symbol='')

        # Assertions
        assert result['status'] == 'failed'
        assert 'must be a non-empty string' in result['error']

    def test_parse_mind(self, minds):
        """Test parsing of a mind item."""
        raw_item = {
            'text': 'Test discussion',
            'symbols': {'AAPL': 'NASDAQ:AAPL'},
            'uid': 'test123',
            'url': 'https://test.com',
            'author': {
                'username': 'testuser',
                'uri': '/u/testuser/',
                'is_broker': False
            },
            'created': '2025-01-07T12:00:00+00:00',
            'total_likes': 10,
            'total_comments': 5,
            'modified': False,
            'hidden': False
        }

        parsed = minds._parse_mind(raw_item)

        assert parsed['text'] == 'Test discussion'
        assert parsed['author']['username'] == 'testuser'
        assert parsed['total_likes'] == 10
        assert parsed['symbols'] == ['NASDAQ:AAPL']

    def test_get_mind_large_numbers_real_api(self, minds):
        """Test getting minds with large limit using real API."""
        result = minds.get_minds(symbol='NASDAQ:AAPL', limit=150)

        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) <= 150