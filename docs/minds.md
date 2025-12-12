# Minds Community Discussions

## Overview

The Minds module provides functionality to scrape and analyze community-generated content from TradingView's Minds feature. This includes questions, discussions, trading ideas, and sentiment analysis from the TradingView community.

!!! note "Supported Data"
    For a complete list of supported exchanges and symbols, see [Supported Data](supported_data.md).

## Input Specification

### Minds Class Constructor

```python
Minds(export_result: bool = False, export_type: str = 'json')
```

**Parameters:**
- `export_result` (bool): Whether to automatically export results to file. Defaults to `False`.
- `export_type` (str): Export format, either `'json'` or `'csv'`. Defaults to `'json'`.

### get_minds() Method

```python
get_minds(symbol: str, limit: int = None) -> Dict
```

**Parameters:**
- `symbol` (str): The symbol to get discussions for (e.g., `'NASDAQ:AAPL'`). **Required.**
- `limit` (int, optional): Maximum number of results to retrieve from the first page. If `None`, fetches all available data from the first page. Defaults to `None`.

**Constraints:**
- Symbol must include exchange prefix (e.g., `'NASDAQ:AAPL'`, `'BITSTAMP:BTCUSD'`)
- Symbol must be a non-empty string
- Limit must be a positive integer if provided

## Output Specification

### Response Structure

The method returns a dictionary with the following structure:

```python
{
    'status': str,          # 'success' or 'failed'
    'data': List[Dict],     # List of mind discussions (only on success)
    'total': int,           # Total number of results retrieved
    'symbol_info': Dict,    # Information about the symbol
    'pages': int,           # Number of pages retrieved (always 1)
    'error': str            # Error message (only on failure)
}
```

### Mind Item Schema

Each item in the `data` array contains:

```python
{
    'uid': str,                     # Unique identifier
    'text': str,                    # Discussion text content
    'url': str,                     # URL to the discussion
    'author': {
        'username': str,            # Author's username
        'profile_url': str,        # URL to author's profile
        'is_broker': bool          # Whether author is a broker
    },
    'created': str,                 # Formatted creation date (YYYY-MM-DD HH:MM:SS)
    'symbols': List[str],           # List of symbols mentioned
    'total_likes': int,             # Number of likes
    'total_comments': int,          # Number of comments
    'modified': bool,               # Whether discussion was modified
    'hidden': bool                  # Whether discussion is hidden
}
```

### Symbol Info Schema

```python
{
    'short_name': str,              # Short symbol name (e.g., 'AAPL')
    'exchange': str                 # Exchange name (e.g., 'NASDAQ')
}
```

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.minds import Minds

# Initialize Minds scraper
minds = Minds()

# Get discussions for Apple from first page
aapl_discussions = minds.get_minds(
    symbol='NASDAQ:AAPL'
)

print(f"Found {aapl_discussions['total']} discussions")
for discussion in aapl_discussions['data']:
    print(f"{discussion['author']['username']}: {discussion['text'][:50]}...")
```

### Limited Discussions

```python
# Get up to 100 discussions for Bitcoin from first page
btc_discussions = minds.get_minds(
    symbol='BITSTAMP:BTCUSD',
    limit=100
)

# Find most liked discussion
most_liked = max(btc_discussions['data'], key=lambda x: x['total_likes'])
print(f"Most liked discussion: {most_liked['total_likes']} likes")
print(f"Text: {most_liked['text']}")
```

### Discussions with Export

```python
# Get discussions and export to JSON
minds_with_export = Minds(export_result=True, export_type='json')

discussions = minds_with_export.get_minds(
    symbol='NASDAQ:TSLA'
)

# This automatically saves to a JSON file
```

### Large Dataset Retrieval

```python
# Get up to 200 discussions for Apple from first page
all_discussions = minds.get_minds(
    symbol='NASDAQ:AAPL',
    limit=200
)

print(f"Retrieved {all_discussions['total']} discussions from first page")
```

### Error Handling

```python
# Handle potential errors
result = minds.get_minds(symbol='INVALID')

if result['status'] == 'failed':
    print(f"Error: {result['error']}")
    # Handle error appropriately
```

