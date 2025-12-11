# News Scraping

## Overview

The News Scraping module provides functionality to scrape financial and cryptocurrency news from TradingView. It supports scraping both headlines and detailed story content, with filtering capabilities by provider, geographic area, and sorting options.

## Why This Feature Exists

The news scraping feature exists to:

- Provide real-time financial and cryptocurrency news data
- Enable sentiment analysis and market monitoring
- Support trading decision-making with up-to-date information
- Allow filtering by specific news providers and geographic regions
- Provide both headlines and detailed article content for comprehensive analysis

## Input Specification

### NewsScraper Class Constructor

```python
NewsScraper(export_result=False, export_type='json', cookie=None)
```

- `export_result` (bool): Whether to export results to file. Default: `False`
- `export_type` (str): Export format, either `'json'` or `'csv'`. Default: `'json'`
- `cookie` (str): TradingView session cookie for authenticated requests

### scrape_headlines Method

```python
scrape_headlines(
    symbol: str,
    exchange: str,
    provider: str = None,
    area: str = None,
    sort: str = "latest",
    section: str = "all",
    language: str = "en"
)
```

#### Parameters:

- `symbol` (str, required): The trading symbol (e.g., "BTCUSD", "AAPL")
- `exchange` (str, required): The exchange (e.g., "BINANCE", "NASDAQ")
- `provider` (str, optional): News provider filter (e.g., "cointelegraph", "dow-jones")
- `area` (str, optional): Geographic area filter (e.g., "americas", "europe", "asia")
- `sort` (str, optional): Sorting order. Options: `"latest"`, `"oldest"`, `"most_urgent"`, `"least_urgent"`. Default: `"latest"`
- `section` (str, optional): News section. Options: `"all"`, `"esg"`, `"financial_statement"`, `"press_release"`. Default: `"all"`
- `language` (str, optional): Language code. Default: `"en"`

#### Constraints:

- At least `symbol` and `exchange` must be specified
- `symbol` must be used together with `exchange`
- `exchange` must be in the supported exchanges list
- `provider` must be in the supported news providers list
- `area` must be in the supported areas list
- `language` must be in the supported languages list

### scrape_news_content Method

```python
scrape_news_content(story_path: str)
```

- `story_path` (str, required): The path of the story on TradingView (e.g., "/news/story/12345")

## Output Specification

### Headlines Output Schema

The `scrape_headlines` method returns a list of news articles, where each article contains:

```python
{
    "id": str,                # Unique article ID
    "link": str,              # URL to the article
    "title": str,             # Article title
    "published": int,         # Unix timestamp of publication
    "urgency": int,           # Urgency score (0-100)
    "provider": str,          # News provider code
    "storyPath": str,         # Path for detailed content scraping
    # Additional fields may be present
}
```

### Story Content Output Schema

The `scrape_news_content` method returns a dictionary with detailed article information:

```python
{
    "breadcrumbs": str,       # Navigation breadcrumbs
    "title": str,             # Article title
    "published_datetime": str, # ISO 8601 publication datetime
    "related_symbols": [      # List of related trading symbols
        {
            "symbol": str,   # Symbol name
            "logo": str      # Logo image URL
        }
    ],
    "body": [                 # Article content
        {
            "type": str,     # "text" or "image"
            "content": str,  # Text content (for text type)
            "src": str,      # Image URL (for image type)
            "alt": str       # Alt text (for image type)
        }
    ],
    "tags": [str]             # List of article tags
}
```

## Behavioral Notes from Code and Tests

1. **Input Validation**: The system validates all inputs against supported data files before making API requests
2. **Captcha Handling**: If a captcha challenge is encountered, an error is logged and empty results are returned
3. **Sorting**: News can be sorted by publication date or urgency level
4. **Empty Results**: Returns an empty list when no news items are found
5. **Error Handling**: Raises appropriate exceptions for invalid inputs and HTTP errors
6. **Rate Limiting**: The system includes time delays between requests to avoid rate limiting

## Code Examples

### Basic Headline Scraping

```python
from tradingview_scraper.symbols.news import NewsScraper

# Create scraper instance
news_scraper = NewsScraper()

# Scrape latest news for a symbol
headlines = news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    sort='latest'
)

# Print first 5 headlines
for headline in headlines[:5]:
    print(f"{headline['title']} - {headline['provider']}")
```

### Advanced Filtering

```python
# Filter by provider and area
headlines = news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    provider='cointelegraph',
    area='americas',
    sort='most_urgent'
)

# Filter by section
esg_news = news_scraper.scrape_headlines(
    symbol='AAPL',
    exchange='NASDAQ',
    section='esg',
    sort='latest'
)
```

### Story Content Scraping

```python
# First get headlines
headlines = news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE'
)

# Scrape detailed content of first article
if headlines:
    story_path = headlines[0]['storyPath']
    content = news_scraper.scrape_news_content(story_path=story_path)

    print(f"Title: {content['title']}")
    print(f"Published: {content['published_datetime']}")
    print("Content:")
    for item in content['body']:
        if item['type'] == 'text':
            print(item['content'])
```

### Exporting Results

```python
# Create scraper with export enabled
news_scraper = NewsScraper(export_result=True, export_type='json')

# Scrape and automatically export
headlines = news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE'
)

# Results will be saved to JSON file automatically
```

## Common Mistakes and Solutions

### Mistake: Missing required parameters

```python
# Wrong - missing exchange
news_scraper.scrape_headlines(symbol='BTCUSD')

# Wrong - missing symbol
news_scraper.scrape_headlines(exchange='BINANCE')
```

**Solution**: Always provide both `symbol` and `exchange` parameters.

### Mistake: Invalid exchange or provider

```python
# Wrong - invalid exchange
news_scraper.scrape_headlines(symbol='BTCUSD', exchange='INVALID')

# Wrong - invalid provider
news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    provider='invalid_provider'
)
```

**Solution**: Check supported exchanges in [`tradingview_scraper/data/exchanges.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/exchanges.txt) and providers in [`tradingview_scraper/data/news_providers.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/news_providers.txt).

### Mistake: Invalid sort option

```python
# Wrong - invalid sort
news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    sort='invalid_sort'
)
```

**Solution**: Use only supported sort options: `"latest"`, `"oldest"`, `"most_urgent"`, `"least_urgent"`.

### Mistake: Handling captcha challenges

```python
# If you encounter captcha challenges, set a valid cookie
news_scraper = NewsScraper(cookie="your_tradingview_cookie")
```

**Solution**: Set a valid TradingView session cookie in the constructor or environment variables.

## Environment Setup

To use the news scraping functionality, ensure your environment is properly set up:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
uv sync
```

## Error Cases from Tests

The test suite covers several error scenarios:

1. **No news found**: Returns empty list when no news items are available
2. **Captcha challenges**: Logs error and returns empty results
3. **Invalid parameters**: Raises `ValueError` for unsupported exchanges, providers, or areas
4. **HTTP errors**: Raises appropriate exceptions for network issues
5. **Missing story paths**: Handles cases where story paths are not available in headlines

Refer to the test file [`tests/test_news.py`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tests/test_news.py) for detailed error handling examples.