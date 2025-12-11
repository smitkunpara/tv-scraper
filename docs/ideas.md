# Ideas Scraper

## Overview

The Ideas scraper module provides functionality to extract trading ideas from TradingView for specified symbols. It allows users to scrape published user ideas, including details such as title, description, author information, and engagement metrics.

!!! note "Supported Data"
    For a complete list of supported exchanges and symbols, see [Supported Data](supported_data.md).

## Input Specification

### Constructor Parameters

```python
Ideas(export_result=False, export_type='json', cookie=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | bool | `False` | Whether to automatically export results to file |
| `export_type` | str | `'json'` | Export format, either `'json'` or `'csv'` |
| `cookie` | str | `None` | TradingView session cookie for bypassing captcha challenges |

### Scrape Method Parameters

```python
scrape(symbol="BTCUSD", startPage=1, endPage=1, sort="popular")
```

| Parameter | Type | Default | Description | Constraints |
|-----------|------|---------|-------------|-------------|
| `symbol` | str | `"BTCUSD"` | Trading symbol to scrape ideas for | Must be a valid TradingView symbol |
| `startPage` | int | `1` | Starting page number | Must be >= 1 |
| `endPage` | int | `1` | Ending page number | Must be >= startPage |
| `sort` | str | `"popular"` | Sorting criteria | Must be either `'popular'` or `'recent'` |

## Output Specification

The scraper returns a list of dictionaries, where each dictionary represents a trading idea with the following structure:

```python
{
    "title": str,                # Idea title
    "description": str,          # Idea description/content
    "preview_image": list,       # List of preview image URLs
    "chart_url": str,            # URL to the associated chart
    "comments_count": int,       # Number of comments
    "views_count": int,          # Number of views
    "author": str,               # Author username
    "likes_count": int,          # Number of likes
    "timestamp": int             # Unix timestamp of publication
}
```

### Output Schema Details

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | The title of the trading idea |
| `description` | str | The main content/description of the idea |
| `preview_image` | list | List of URLs to preview images (may be empty) |
| `chart_url` | str | URL to the TradingView chart associated with the idea |
| `comments_count` | int | Number of comments on the idea |
| `views_count` | int | Number of views the idea has received |
| `author` | str | Username of the idea author |
| `likes_count` | int | Number of likes the idea has received |
| `timestamp` | int | Unix timestamp indicating when the idea was published |

## Code Examples

### Basic Scrape

```python
from tradingview_scraper.symbols.ideas import Ideas

# Create scraper instance
ideas_scraper = Ideas()

# Scrape popular ideas for BTCUSD (default symbol)
ideas = ideas_scraper.scrape()
print(f"Found {len(ideas)} ideas")
```

### Pagination Example

```python
# Scrape ideas across multiple pages
ideas_scraper = Ideas()
ideas = ideas_scraper.scrape(
    symbol="NASDAQ:AAPL",
    startPage=1,
    endPage=5,
    sort="recent"
)
print(f"Found {len(ideas)} recent ideas for AAPL")
```

### Export Example

```python
# Scrape and export to JSON
ideas_scraper = Ideas(export_result=True, export_type='json')
ideas = ideas_scraper.scrape(
    symbol="ETHUSD",
    startPage=1,
    endPage=3
)

# Scrape and export to CSV
ideas_scraper = Ideas(export_result=True, export_type='csv')
ideas = ideas_scraper.scrape(symbol="BTCUSD")
```

### Cookie Bypass Example

```python
# Use cookie to bypass captcha challenges
ideas_scraper = Ideas(cookie="your_tradingview_session_cookie")
ideas = ideas_scraper.scrape(
    symbol="BTCUSD",
    sort="popular",
    startPage=1,
    endPage=10
)
```

## Additional Notes

!!! note
    The Ideas scraper uses TradingView's JSON API endpoints. The response structure may change if TradingView updates their API.

!!! warning
    Excessive scraping without proper delays may result in IP bans or captcha challenges. Use cookies and reasonable page ranges.

The Ideas scraper provides a powerful way to collect and analyze trading ideas from the TradingView community, supporting both research and automated trading strategies.
