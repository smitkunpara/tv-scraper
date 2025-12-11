# Markets Module

## Overview

The Markets module provides comprehensive functionality for retrieving market data from TradingView, including symbol-to-exchange lookups and global/regional market scanning capabilities. This module consists of two main classes:

1. **SymbolMarkets**: For finding all exchanges where a specific symbol is traded
2. **Markets**: For retrieving top stocks and market overview data across various regions


## Input Specification

### SymbolMarkets Class

#### Constructor Parameters

```python
SymbolMarkets(export_result: bool = False, export_type: str = 'json')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | bool | False | Whether to export results to file |
| `export_type` | str | 'json' | Export format ('json' or 'csv') |

#### Scrape Method

```python
scrape(
    symbol: str,
    columns: Optional[List[str]] = None,
    scanner: str = 'global',
    limit: int = 150
) -> Dict
```

| Parameter | Type | Default | Description | Constraints |
|-----------|------|---------|-------------|-------------|
| `symbol` | str | Required | Symbol to search for (e.g., 'AAPL', 'BTCUSD') | Must be valid TradingView symbol |
| `columns` | List[str] | None | Specific columns to retrieve | Must be valid column names |
| `scanner` | str | 'global' | Scanner endpoint ('global', 'america', 'crypto', 'forex', 'cfd') | Must be one of supported scanners |
| `limit` | int | 150 | Maximum number of results | Must be positive integer <= 150 |

### Markets Class

#### Constructor Parameters

```python
Markets(export_result: bool = False, export_type: str = 'json')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | bool | False | Whether to export results to file |
| `export_type` | str | 'json' | Export format ('json' or 'csv') |

#### Get Top Stocks Method

```python
get_top_stocks(
    market: str = 'america',
    by: str = 'market_cap',
    columns: Optional[List[str]] = None,
    limit: int = 50
) -> Dict
```

| Parameter | Type | Default | Description | Constraints |
|-----------|------|---------|-------------|-------------|
| `market` | str | 'america' | Market to scan | Must be supported market |
| `by` | str | 'market_cap' | Sorting criteria | Must be supported sort criteria |
| `columns` | List[str] | None | Specific columns to retrieve | Must be valid column names |
| `limit` | int | 50 | Maximum number of results | Must be positive integer <= 50 |

## Supported Scanners and Markets

### SymbolMarkets Scanners

| Scanner | Endpoint | Description |
|---------|----------|-------------|
| `global` | https://scanner.tradingview.com/global/scan | Search across all markets globally |
| `america` | https://scanner.tradingview.com/america/scan | Search within American markets |
| `crypto` | https://scanner.tradingview.com/crypto/scan | Search within cryptocurrency markets |
| `forex` | https://scanner.tradingview.com/forex/scan | Search within forex markets |
| `cfd` | https://scanner.tradingview.com/cfd/scan | Search within CFD markets |

### Markets Supported Regions

| Market | Endpoint | Description |
|--------|----------|-------------|
| `america` | https://scanner.tradingview.com/america/scan | American stocks and markets |
| `australia` | https://scanner.tradingview.com/australia/scan | Australian stocks |
| `canada` | https://scanner.tradingview.com/canada/scan | Canadian stocks |
| `germany` | https://scanner.tradingview.com/germany/scan | German stocks |
| `india` | https://scanner.tradingview.com/india/scan | Indian stocks |
| `uk` | https://scanner.tradingview.com/uk/scan | UK stocks |
| `crypto` | https://scanner.tradingview.com/crypto/scan | Cryptocurrency markets |
| `forex` | https://scanner.tradingview.com/forex/scan | Forex markets |
| `global` | https://scanner.tradingview.com/global/scan | Global markets |

### Sort Criteria

| Criteria | API Field | Description |
|----------|-----------|-------------|
| `market_cap` | `market_cap_basic` | Sort by market capitalization |
| `volume` | `volume` | Sort by trading volume |
| `change` | `change` | Sort by price change percentage |
| `price` | `close` | Sort by current price |
| `volatility` | `Volatility.D` | Sort by daily volatility |

## Output Specification

### SymbolMarkets Response Schema

```python
{
    'status': str,           # 'success' or 'failed'
    'data': List[Dict],      # List of market data
    'total': int,            # Number of results returned
    'totalCount': int,       # Total available results
    'error': str             # Error message (if failed)
}
```

Each data item contains:

```python
{
    'symbol': str,           # Full symbol with exchange prefix
    'name': str,             # Symbol name
    'close': float,          # Current price
    'change': float,         # Percentage change
    'change_abs': float,     # Absolute change
    'volume': float,         # Trading volume
    'exchange': str,         # Exchange name
    'type': str,             # Instrument type
    'description': str,      # Description
    'currency': str,         # Currency
    'market_cap_basic': float # Market capitalization
}
```

### Markets Response Schema

```python
{
    'status': str,           # 'success' or 'failed'
    'data': List[Dict],      # List of stock data
    'total': int,            # Number of results returned
    'totalCount': int,       # Total available results
    'error': str             # Error message (if failed)
}
```

Each data item contains:

```python
{
    'symbol': str,           # Full symbol with exchange prefix
    'name': str,             # Company name
    'close': float,          # Current price
    'change': float,         # Percentage change
    'change_abs': float,     # Absolute change
    'volume': float,         # Trading volume
    'Recommend.All': float,  # Overall recommendation score
    'market_cap_basic': float, # Market capitalization
    'price_earnings_ttm': float, # P/E ratio
    'earnings_per_share_basic_ttm': float, # EPS
    'sector': str,           # Sector classification
    'industry': str          # Industry classification
}
```


## Code Examples

### Basic Symbol Markets Lookup

```python
from tradingview_scraper.symbols.symbol_markets import SymbolMarkets

# Find all markets where Apple stock is traded
markets = SymbolMarkets()
result = markets.scrape(symbol='AAPL')

if result['status'] == 'success':
    print(f"AAPL is traded on {result['total']} markets:")
    for market in result['data']:
        print(f"- {market['symbol']} on {market['exchange']}")
        print(f"  Price: ${market['close']}, Volume: {market['volume']}")
```

### Regional Symbol Search

```python
# Find AAPL only in American markets
american_markets = markets.scrape(
    symbol='AAPL',
    scanner='america',
    limit=50
)

# Find BTCUSD in crypto markets
btc_markets = markets.scrape(
    symbol='BTCUSD',
    scanner='crypto',
    limit=25
)
```

### Custom Columns and Export

```python
# Get specific columns and export to JSON
markets = SymbolMarkets(export_result=True, export_type='json')
result = markets.scrape(
    symbol='TSLA',
    columns=['name', 'close', 'volume', 'exchange'],
    scanner='global',
    limit=100
)
```

### Top Stocks by Market Cap

```python
from tradingview_scraper.symbols.markets import Markets

# Get top 20 stocks by market cap in America
markets = Markets()
top_stocks = markets.get_top_stocks(
    market='america',
    by='market_cap',
    limit=20
)

if top_stocks['status'] == 'success':
    print("Top 20 stocks by market cap:")
    for i, stock in enumerate(top_stocks['data'][:5], 1):
        print(f"{i}. {stock['symbol']} - ${stock['close']}B cap")
```

### Top Stocks by Volume

```python
# Get most active stocks by trading volume
most_active = markets.get_top_stocks(
    market='america',
    by='volume',
    limit=15
)

# Get biggest movers (gainers/losers)
biggest_movers = markets.get_top_stocks(
    market='america',
    by='change',
    limit=25
)
```

### Custom Columns for Market Data

```python
# Get specific columns for analysis
custom_columns = ['name', 'close', 'volume', 'market_cap_basic', 'sector']
result = markets.get_top_stocks(
    market='america',
    by='market_cap',
    columns=custom_columns,
    limit=10
)
```

### Cross-Market Analysis

```python
# Compare top stocks across different regions
regions = ['america', 'uk', 'germany', 'india']

for region in regions:
    result = markets.get_top_stocks(
        market=region,
        by='market_cap',
        limit=5
    )
    print(f"\nTop 5 stocks in {region.upper()}:")
    for stock in result['data']:
        print(f"- {stock['symbol']}: ${stock['close']} ({stock['change']}%) ")
```

## Common Mistakes and Solutions

### Mistake: Using unsupported scanner

```python
# Wrong
result = markets.scrape(symbol='AAPL', scanner='europe')

# Right
result = markets.scrape(symbol='AAPL', scanner='global')
```

**Solution**: Use only supported scanners: 'global', 'america', 'crypto', 'forex', 'cfd'

### Mistake: Invalid market for top stocks

```python
# Wrong
result = markets.get_top_stocks(market='europe')

# Right
result = markets.get_top_stocks(market='germany')
```

**Solution**: Check supported markets list before calling the method

### Mistake: Invalid sort criteria

```python
# Wrong
result = markets.get_top_stocks(by='price_change')

# Right
result = markets.get_top_stocks(by='change')
```

**Solution**: Use supported criteria: 'market_cap', 'volume', 'change', 'price', 'volatility'

### Mistake: Exceeding limit constraints

```python
# Wrong - SymbolMarkets limit too high
result = markets.scrape(symbol='AAPL', limit=200)

# Right
result = markets.scrape(symbol='AAPL', limit=150)
```

**Solution**: Respect the maximum limits: 150 for SymbolMarkets, 50 for Markets

### Mistake: Not handling API failures

```python
# Wrong - No error checking
result = markets.scrape(symbol='INVALID')
print(result['data'])  # This will crash

# Right - Always check status
result = markets.scrape(symbol='INVALID')
if result['status'] == 'success':
    print(result['data'])
else:
    print(f"Error: {result['error']}")
```

**Solution**: Always check the 'status' field before accessing data

## Advanced Usage Patterns

### Multi-Symbol Market Analysis

```python
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
markets = SymbolMarkets()

for symbol in symbols:
    result = markets.scrape(symbol=symbol, scanner='global', limit=50)
    if result['status'] == 'success':
        print(f"\n{symbol} is traded on {result['total']} markets:")
        exchanges = [item['exchange'] for item in result['data']]
        print(f"Exchanges: {', '.join(exchanges)}")
```

### Market Arbitrage Detection

```python
# Find price differences for the same symbol across exchanges
result = markets.scrape(symbol='BTCUSD', scanner='crypto', limit=50)

if result['status'] == 'success' and len(result['data']) > 1:
    prices = {item['exchange']: item['close'] for item in result['data']}
    min_price = min(prices.values())
    max_price = max(prices.values())
    spread = max_price - min_price

    print(f"BTCUSD arbitrage opportunity: ${spread:.2f} spread")
    print(f"Buy at: {[k for k, v in prices.items() if v == min_price]}")
    print(f"Sell at: {[k for k, v in prices.items() if v == max_price]}")
```

### Sector Analysis

```python
# Analyze top stocks by sector
result = markets.get_top_stocks(
    market='america',
    by='market_cap',
    limit=100
)

if result['status'] == 'success':
    sectors = {}
    for stock in result['data']:
        sector = stock.get('sector', 'Unknown')
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(stock['symbol'])

    print("Sector distribution:")
    for sector, symbols in sectors.items():
        print(f"- {sector}: {len(symbols)} stocks")
```

This documentation provides comprehensive coverage of the Markets module functionality, including symbol-to-exchange lookups, global/regional scanning behaviors, top lists (market cap, volume, change, volatility), and test-driven behaviors as required.
