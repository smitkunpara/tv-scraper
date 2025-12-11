# Ideas Scraper

## Overview

The Ideas scraper module provides functionality to extract trading ideas from TradingView for specified symbols. It allows users to scrape published user ideas, including details such as title, description, author information, and engagement metrics.

## Why This Feature Exists

The Ideas scraper exists to:

- Collect trading ideas and analysis from TradingView's community
- Enable sentiment analysis and market research
- Provide historical context for trading decisions
- Support automated idea aggregation and monitoring
- Facilitate competitive analysis and strategy validation

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
| `startPage` | int | `1` | Starting page number | Must be ≥ 1 |
| `endPage` | int | `1` | Ending page number | Must be ≥ startPage |
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

## Behavioral Notes from Code and Tests

1. **Captcha Handling**: The scraper checks for captcha challenges in responses. If encountered, it logs an error and returns empty results.

2. **Cookie Mechanism**: Providing a valid TradingView cookie in the constructor can help bypass captcha challenges.

3. **Threading**: The scraper uses concurrent threading (max 3 workers) to scrape multiple pages simultaneously, improving performance.

4. **Rate Limiting**: There's an implicit 5-second delay between requests to avoid overwhelming TradingView servers.

5. **Error Handling**: The scraper gracefully handles various error scenarios:
   - Network request failures
   - Invalid JSON responses
   - HTTP errors
   - Invalid sort parameters

6. **Pagination**: The scraper can handle multiple pages (from `startPage` to `endPage` inclusive).

7. **Export Functionality**: When `export_result=True`, results are automatically saved as JSON or CSV files.

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

## Common Mistakes and Solutions

### Mistake: Invalid Sort Parameter

```python
# Wrong - invalid sort value
ideas = ideas_scraper.scrape(sort="newest")

# Right - use valid sort values
ideas = ideas_scraper.scrape(sort="recent")  # or "popular"
```

**Solution**: Only use `'popular'` or `'recent'` for the sort parameter.

### Mistake: Invalid Symbol

```python
# Wrong - invalid symbol format
ideas = ideas_scraper.scrape(symbol="INVALID")

# Right - use valid TradingView symbols
ideas = ideas_scraper.scrape(symbol="BTCUSD")
ideas = ideas_scraper.scrape(symbol="NASDAQ:AAPL")
```

**Solution**: Use valid TradingView symbol formats. Refer to supported symbols in the TradingView platform.

### Mistake: Captcha Challenge Not Handled

```python
# Without cookie, may encounter captcha
ideas_scraper = Ideas()
ideas = ideas_scraper.scrape()  # May return empty list due to captcha

# Solution: Use cookie
ideas_scraper = Ideas(cookie="your_session_cookie")
ideas = ideas_scraper.scrape()
```

**Solution**: Provide a valid TradingView session cookie to bypass captcha challenges.

### Mistake: Page Range Issues

```python
# Wrong - endPage before startPage
ideas = ideas_scraper.scrape(startPage=5, endPage=1)

# Right - ensure proper page ordering
ideas = ideas_scraper.scrape(startPage=1, endPage=5)
```

**Solution**: Ensure `endPage` is greater than or equal to `startPage`.

## Environment Setup

To use the Ideas scraper, ensure your environment is properly set up:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
uv sync
```

## Additional Notes

!!! note
    The Ideas scraper uses TradingView's JSON API endpoints. The response structure may change if TradingView updates their API.

!!! warning
    Excessive scraping without proper delays may result in IP bans or captcha challenges. Use cookies and reasonable page ranges.

The Ideas scraper provides a powerful way to collect and analyze trading ideas from the TradingView community, supporting both research and automated trading strategies.