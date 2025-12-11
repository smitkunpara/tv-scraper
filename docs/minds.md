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
get_minds(symbol: str, sort: str = 'recent', limit: int = 50) -> Dict
```

**Parameters:**
- `symbol` (str): The symbol to get discussions for (e.g., `'NASDAQ:AAPL'`). **Required.**
- `sort` (str): Sort order. Options: `'recent'`, `'popular'`, `'trending'`. Defaults to `'recent'`.
- `limit` (int): Maximum number of results to retrieve (1-50). Defaults to `50`.

**Constraints:**
- Symbol must include exchange prefix (e.g., `'NASDAQ:AAPL'`, `'BITSTAMP:BTCUSD'`)
- Symbol must be a non-empty string
- Sort option must be one of the supported values
- Limit must be a positive integer

### get_all_minds() Method

```python
get_all_minds(symbol: str, sort: str = 'recent', max_results: int = 200) -> Dict
```

**Parameters:**
- `symbol` (str): The symbol to get discussions for. **Required.**
- `sort` (str): Sort order. Options: `'recent'`, `'popular'`, `'trending'`. Defaults to `'recent'`.
- `max_results` (int): Maximum total results to retrieve across all pages. Defaults to `200`.

**Constraints:**
- Same symbol constraints as `get_minds()`
- Maximum results limited to reasonable values to prevent excessive API calls

## Output Specification

### Response Structure

Both methods return a dictionary with the following structure:

```python
{
    'status': str,          # 'success' or 'failed'
    'data': List[Dict],     # List of mind discussions (only on success)
    'total': int,           # Total number of results
    'symbol_info': Dict,    # Information about the symbol
    'next_cursor': str,     # Cursor for pagination (get_minds only)
    'pages': int,           # Number of pages retrieved (get_all_minds only)
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

# Get recent discussions for Apple
aapl_discussions = minds.get_minds(
    symbol='NASDAQ:AAPL',
    sort='recent',
    limit=20
)

print(f"Found {aapl_discussions['total']} discussions")
for discussion in aapl_discussions['data']:
    print(f"{discussion['author']['username']}: {discussion['text'][:50]}...")
```

### Popular Discussions

```python
# Get popular discussions for Bitcoin
btc_discussions = minds.get_minds(
    symbol='BITSTAMP:BTCUSD',
    sort='popular',
    limit=15
)

# Find most liked discussion
most_liked = max(btc_discussions['data'], key=lambda x: x['total_likes'])
print(f"Most liked discussion: {most_liked['total_likes']} likes")
print(f"Text: {most_liked['text']}")
```

### Trending Discussions with Export

```python
# Get trending discussions and export to JSON
minds_with_export = Minds(export_result=True, export_type='json')

trending = minds_with_export.get_minds(
    symbol='NASDAQ:TSLA',
    sort='trending',
    limit=25
)

# This automatically saves to a JSON file
```

### Pagination with get_all_minds()

```python
# Get all available discussions (up to 200)
all_discussions = minds.get_all_minds(
    symbol='NASDAQ:AAPL',
    sort='popular',
    max_results=100
)

print(f"Retrieved {all_discussions['total']} discussions across {all_discussions['pages']} pages")
```

### Error Handling

```python
# Handle potential errors
result = minds.get_minds(symbol='INVALID', sort='recent')

if result['status'] == 'failed':
    print(f"Error: {result['error']}")
    # Handle error appropriately
```

## Common Mistakes and Solutions

### Mistake: Invalid Symbol Format

```python
# Wrong - missing exchange prefix
minds.get_minds(symbol='AAPL')

# Right - include exchange prefix
minds.get_minds(symbol='NASDAQ:AAPL')
```

**Solution**: Always use the full symbol format with exchange prefix (e.g., `'NASDAQ:AAPL'`, `'BITSTAMP:BTCUSD'`).

### Mistake: Invalid Sort Option

```python
# Wrong - unsupported sort option
minds.get_minds(symbol='NASDAQ:AAPL', sort='oldest')

# Right - use supported options
minds.get_minds(symbol='NASDAQ:AAPL', sort='recent')
```

**Solution**: Use only supported sort options: `'recent'`, `'popular'`, or `'trending'`.

### Mistake: Empty Symbol

```python
# Wrong - empty symbol
minds.get_minds(symbol='')

# Right - provide valid symbol
minds.get_minds(symbol='NASDAQ:AAPL')
```

**Solution**: Always provide a non-empty symbol string with proper format.

### Mistake: Ignoring Pagination

```python
# Wrong - assuming all results are in one call
all_results = minds.get_minds(symbol='NASDAQ:AAPL', limit=200)

# Right - use get_all_minds() for large datasets
all_results = minds.get_all_minds(symbol='NASDAQ:AAPL', max_results=200)
```

**Solution**: Use `get_all_minds()` when you need more than 50 results or want to handle pagination automatically.
