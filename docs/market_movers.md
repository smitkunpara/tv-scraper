# Market Movers

## Overview

The Market Movers module provides functionality to scrape and analyze market movers data from TradingView. This includes gainers, losers, most active stocks, penny stocks, and pre/after-market movers across various financial markets.

## Input Specification

### MarketMovers Class Constructor

```python
MarketMovers(export_result: bool = False, export_type: str = 'json')
```

**Parameters:**

- `export_result` (bool): Whether to export results to a file. Defaults to `False`.
- `export_type` (str): Export format, either `'json'` or `'csv'`. Defaults to `'json'`.

### Scrape Method

```python
scrape(
    market: str = 'stocks-usa',
    category: str = 'gainers',
    fields: Optional[List[str]] = None,
    limit: int = 50
) -> Dict
```

**Parameters:**

- `market` (str): The market to scrape. Defaults to `'stocks-usa'`.
- `category` (str): The category of market movers. Defaults to `'gainers'`.
- `fields` (List[str], optional): Specific fields to retrieve. If `None`, uses default fields.
- `limit` (int): Maximum number of results to return. Defaults to 50.

**Supported Markets:**

The following markets are supported:

- `stocks-usa` - US Stock Market
- `stocks-uk` - UK Stock Market
- `stocks-india` - Indian Stock Market
- `stocks-australia` - Australian Stock Market
- `stocks-canada` - Canadian Stock Market
- `crypto` - Cryptocurrency Market
- `forex` - Forex Market
- `bonds` - Bonds Market
- `futures` - Futures Market

**Supported Categories:**

For stock markets, the following categories are available:

- `gainers` - Top gaining stocks
- `losers` - Top losing stocks
- `most-active` - Most actively traded stocks
- `penny-stocks` - Penny stocks (price < $5)
- `pre-market-gainers` - Pre-market gainers
- `pre-market-losers` - Pre-market losers
- `after-hours-gainers` - After-hours gainers
- `after-hours-losers` - After-hours losers

**Field Selection:**

Default fields include:
- `name` - Company/asset name
- `close` - Closing price
- `change` - Percentage change
- `change_abs` - Absolute change
- `volume` - Trading volume
- `market_cap_basic` - Market capitalization
- `price_earnings_ttm` - Price/Earnings ratio
- `earnings_per_share_basic_ttm` - Earnings per share
- `logoid` - Logo identifier
- `description` - Company description

You can specify custom fields by passing a list of field names.

## Output Specification

The `scrape()` method returns a dictionary with the following structure:

```python
{
    'status': str,  # 'success' or 'failed'
    'data': List[Dict],  # List of market mover data (if successful)
    'total': int,  # Total number of results (if successful)
    'error': str  # Error message (if failed)
}
```

Each item in the `data` list contains:
- `symbol` - The trading symbol (e.g., 'NASDAQ:AAPL')
- Field values as specified in the request

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.market_movers import MarketMovers

# Initialize scraper
scraper = MarketMovers()

# Get top gainers
gainers = scraper.scrape(market='stocks-usa', category='gainers', limit=20)
print(f"Found {gainers['total']} gainers")
for stock in gainers['data']:
    print(f"{stock['symbol']}: {stock['change']}%")
```

### Custom Fields and Export

```python
# Get penny stocks with custom fields and export to CSV
scraper = MarketMovers(export_result=True, export_type='csv')
penny_stocks = scraper.scrape(
    market='stocks-usa',
    category='penny-stocks',
    fields=['name', 'close', 'change', 'volume'],
    limit=100
)
```

### Pre-Market and After-Hours Data

```python
# Get pre-market gainers
premarket = scraper.scrape(
    market='stocks-usa',
    category='pre-market-gainers',
    limit=30
)

# Get after-hours losers
after_hours = scraper.scrape(
    market='stocks-usa',
    category='after-hours-losers',
    limit=30
)
```

### Multiple Markets

```python
# Compare gainers across different markets
markets = ['stocks-usa', 'stocks-uk', 'crypto']
for market in markets:
    result = scraper.scrape(market=market, category='gainers', limit=10)
    print(f"Top gainers in {market}:")
    for item in result['data'][:5]:
        print(f"  {item['symbol']}: {item['change']}%")
```

## Common Mistakes and Solutions

### Mistake: Using unsupported market

```python
# Wrong
scraper.scrape(market='invalid-market', category='gainers')

# Right
scraper.scrape(market='stocks-usa', category='gainers')
```

**Solution**: Always use one of the supported markets listed above.

### Mistake: Using unsupported category for stock markets

```python
# Wrong
scraper.scrape(market='stocks-usa', category='invalid-category')

# Right
scraper.scrape(market='stocks-usa', category='gainers')
```

**Solution**: Use only the supported categories for stock markets.

### Mistake: Requesting too many results

```python
# This might fail or return incomplete data
scraper.scrape(limit=1000)
```

**Solution**: Keep the limit reasonable (typically <= 100) to avoid API issues.

### Mistake: Not handling API errors

```python
# Wrong - no error handling
result = scraper.scrape(market='stocks-usa', category='gainers')
print(result['data'])  # This will fail if status is 'failed'
```

**Solution**: Always check the status before accessing data:

```python
result = scraper.scrape(market='stocks-usa', category='gainers')
if result['status'] == 'success':
    print(result['data'])
else:
    print(f"Error: {result['error']}")
```

## Advanced Usage Patterns

### Monitoring Market Conditions

```python
def monitor_market_conditions():
    scraper = MarketMovers()

    # Check market sentiment
    gainers = scraper.scrape(category='gainers', limit=10)
    losers = scraper.scrape(category='losers', limit=10)

    avg_gain = sum(stock['change'] for stock in gainers['data']) / len(gainers['data'])
    avg_loss = sum(abs(stock['change']) for stock in losers['data']) / len(losers['data'])

    print(f"Market sentiment: {'Bullish' if avg_gain > avg_loss else 'Bearish'}")
    print(f"Average gain: {avg_gain:.2f}%, Average loss: {avg_loss:.2f}%")
```

### Sector Analysis

```python
def analyze_sectors():
    scraper = MarketMovers()
    sectors = {}

    # Get top movers
    movers = scraper.scrape(limit=50)

    for stock in movers['data']:
        # Extract sector from description (simplified example)
        description = stock.get('description', '').lower()
        if 'tech' in description:
            sector = 'Technology'
        elif 'finance' in description or 'bank' in description:
            sector = 'Financial'
        elif 'health' in description or 'pharma' in description:
            sector = 'Healthcare'
        else:
            sector = 'Other'

        if sector not in sectors:
            sectors[sector] = {'count': 0, 'total_change': 0}

        sectors[sector]['count'] += 1
        sectors[sector]['total_change'] += stock['change']

    # Calculate average change by sector
    for sector, data in sectors.items():
        avg_change = data['total_change'] / data['count']
        print(f"{sector}: {avg_change:.2f}% average change ({data['count']} stocks)")
```

This documentation provides comprehensive coverage of the Market Movers functionality, including all supported markets, categories, field selection options, and error handling scenarios as specified in the requirements.
