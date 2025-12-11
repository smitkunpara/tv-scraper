# Screener

## Overview

The Screener module provides powerful functionality to screen financial instruments across multiple markets (stocks, crypto, forex, bonds, futures) with custom filters, sorting, and column selection. It enables users to find instruments that meet specific technical and fundamental criteria.

## Input Specification

### Screener Class Constructor

```python
Screener(export_result: bool = False, export_type: str = 'json')
```

**Parameters:**
- `export_result` (bool): Whether to export results to file. Defaults to `False`.
- `export_type` (str): Export format, either `'json'` or `'csv'`. Defaults to `'json'`.

### Screen Method

```python
screen(
    market: str = 'america',
    filters: Optional[List[Dict[str, Any]]] = None,
    columns: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = 'desc',
    limit: int = 50
) -> Dict
```

**Parameters:**
- `market` (str): The market to screen. Defaults to `'america'`.
- `filters` (List[Dict], optional): List of filter conditions.
- `columns` (List[str], optional): Columns to retrieve.
- `sort_by` (str, optional): Field to sort by.
- `sort_order` (str): Sort order (`'asc'` or `'desc'`). Defaults to `'desc'`.
- `limit` (int): Maximum number of results. Defaults to 50.

### Filter Specification

Each filter dictionary must contain:
- `left` (str): Field name to filter on (e.g., `'close'`, `'volume'`, `'market_cap_basic'`)
- `operation` (str): Operation type from supported operations
- `right` (Any): Value(s) to compare against

## Supported Markets

The screener supports 16 different markets:

| Market Key | Description | Scanner URL |
|------------|-------------|-------------|
| `america` | US Stocks | `https://scanner.tradingview.com/america/scan` |
| `australia` | Australian Stocks | `https://scanner.tradingview.com/australia/scan` |
| `canada` | Canadian Stocks | `https://scanner.tradingview.com/canada/scan` |
| `germany` | German Stocks | `https://scanner.tradingview.com/germany/scan` |
| `india` | Indian Stocks | `https://scanner.tradingview.com/india/scan` |
| `israel` | Israeli Stocks | `https://scanner.tradingview.com/israel/scan` |
| `italy` | Italian Stocks | `https://scanner.tradingview.com/italy/scan` |
| `luxembourg` | Luxembourg Stocks | `https://scanner.tradingview.com/luxembourg/scan` |
| `mexico` | Mexican Stocks | `https://scanner.tradingview.com/mexico/scan` |
| `spain` | Spanish Stocks | `https://scanner.tradingview.com/spain/scan` |
| `turkey` | Turkish Stocks | `https://scanner.tradingview.com/turkey/scan` |
| `uk` | UK Stocks | `https://scanner.tradingview.com/uk/scan` |
| `crypto` | Cryptocurrencies | `https://scanner.tradingview.com/crypto/scan` |
| `forex` | Forex Pairs | `https://scanner.tradingview.com/forex/scan` |
| `cfd` | CFDs | `https://scanner.tradingview.com/cfd/scan` |
| `futures` | Futures | `https://scanner.tradingview.com/futures/scan` |
| `bonds` | Bonds | `https://scanner.tradingview.com/bonds/scan` |
| `global` | Global Markets | `https://scanner.tradingview.com/global/scan` |

## Supported Filter Operations

The screener supports 15 different filter operations:

| Operation | Description | Example |
|-----------|-------------|---------|
| `greater` | Greater than | `{'left': 'close', 'operation': 'greater', 'right': 100}` |
| `less` | Less than | `{'left': 'close', 'operation': 'less', 'right': 50}` |
| `egreater` | Equal or greater than | `{'left': 'volume', 'operation': 'egreater', 'right': 1000000}` |
| `eless` | Equal or less than | `{'left': 'price_earnings_ttm', 'operation': 'eless', 'right': 20}` |
| `equal` | Equal to | `{'left': 'Recommend.All', 'operation': 'equal', 'right': 1}` |
| `nequal` | Not equal to | `{'left': 'change', 'operation': 'nequal', 'right': 0}` |
| `in_range` | Within range | `{'left': 'close', 'operation': 'in_range', 'right': [50, 200]}` |
| `not_in_range` | Outside range | `{'left': 'close', 'operation': 'not_in_range', 'right': [10, 50]}` |
| `above` | Above value | `{'left': 'close', 'operation': 'above', 'right': 150}` |
| `below` | Below value | `{'left': 'close', 'operation': 'below', 'right': 50}` |
| `crosses` | Crosses value | `{'left': 'close', 'operation': 'crosses', 'right': 100}` |
| `crosses_above` | Crosses above value | `{'left': 'close', 'operation': 'crosses_above', 'right': 200}` |
| `crosses_below` | Crosses below value | `{'left': 'close', 'operation': 'crosses_below', 'right': 50}` |
| `has` | Has value | `{'left': 'name', 'operation': 'has', 'right': 'Apple'}` |
| `has_none_of` | Has none of values | `{'left': 'name', 'operation': 'has_none_of', 'right': ['Bank', 'Financial']}` |

## Default Columns by Market

### Stock Markets (Default)
```python
[
    'name', 'close', 'change', 'change_abs', 'volume',
    'Recommend.All', 'market_cap_basic', 'price_earnings_ttm',
    'earnings_per_share_basic_ttm'
]
```

### Crypto Markets
```python
[
    'name', 'close', 'change', 'change_abs', 'volume',
    'market_cap_calc', 'Recommend.All'
]
```

### Forex Markets
```python
[
    'name', 'close', 'change', 'change_abs', 'Recommend.All'
]
```

## Output Specification

The `screen()` method returns a dictionary with the following structure:

```python
{
    'status': str,          # 'success' or 'failed'
    'data': List[Dict],     # List of screened instruments (if successful)
    'total': int,           # Total number of results returned
    'totalCount': int,      # Total number of results available
    'error': str            # Error message (if failed)
}
```

Each data item contains:
- `symbol`: Instrument symbol (e.g., 'NASDAQ:AAPL')
- Dynamic fields based on requested columns

## Code Examples

### Basic Screening

```python
from tradingview_scraper.symbols.screener import Screener

# Initialize screener
screener = Screener()

# Basic screen for US stocks
result = screener.screen(market='america', limit=10)
print(f"Found {result['total']} stocks")
```

### Screening with Filters

```python
# Screen stocks with price > 100 and volume > 1M
filters = [
    {'left': 'close', 'operation': 'greater', 'right': 100},
    {'left': 'volume', 'operation': 'greater', 'right': 1000000}
]

result = screener.screen(
    market='america',
    filters=filters,
    sort_by='volume',
    sort_order='desc',
    limit=20
)

for stock in result['data']:
    print(f"{stock['symbol']}: ${stock['close']} - Vol: {stock['volume']}")
```

### Crypto Screening

```python
# Screen crypto by market cap
crypto_filters = [
    {'left': 'market_cap_calc', 'operation': 'greater', 'right': 1000000000}
]

crypto_results = screener.screen(
    market='crypto',
    filters=crypto_filters,
    columns=['name', 'close', 'market_cap_calc', 'change'],
    limit=50
)
```

### Range Filtering

```python
# Screen stocks in price range
range_filters = [
    {'left': 'close', 'operation': 'in_range', 'right': [50, 200]}
]

range_results = screener.screen(
    market='america',
    filters=range_filters,
    sort_by='close',
    sort_order='asc'
)
```

### Custom Columns and Export

```python
# Screen with custom columns and export to CSV
screener = Screener(export_result=True, export_type='csv')

custom_columns = ['name', 'close', 'volume', 'market_cap_basic', 'price_earnings_ttm']

result = screener.screen(
    market='america',
    columns=custom_columns,
    limit=30
)

# Results will be saved to a CSV file automatically
```

### Advanced Multi-Condition Screening

```python
# Complex screening with multiple conditions
advanced_filters = [
    {'left': 'close', 'operation': 'greater', 'right': 50},
    {'left': 'volume', 'operation': 'greater', 'right': 500000},
    {'left': 'price_earnings_ttm', 'operation': 'eless', 'right': 30},
    {'left': 'change', 'operation': 'greater', 'right': 0}  # Positive change
]

advanced_results = screener.screen(
    market='america',
    filters=advanced_filters,
    sort_by='change',
    sort_order='desc',
    limit=15
)
```

## Common Mistakes and Solutions

### Mistake: Using unsupported market

```python
# Wrong
result = screener.screen(market='europe')

# Right
result = screener.screen(market='germany')  # or other supported market
```

**Solution**: Check the supported markets list or use one of the 16 valid market keys.

### Mistake: Invalid filter operation

```python
# Wrong
filters = [{'left': 'close', 'operation': 'higher', 'right': 100}]

# Right
filters = [{'left': 'close', 'operation': 'greater', 'right': 100}]
```

**Solution**: Use only the 15 supported filter operations listed above.

### Mistake: Missing required filter fields

```python
# Wrong - missing 'operation' field
filters = [{'left': 'close', 'right': 100}]

# Right - all required fields present
filters = [{'left': 'close', 'operation': 'greater', 'right': 100}]
```

**Solution**: Ensure each filter has `left`, `operation`, and `right` fields.

### Mistake: Invalid column names

```python
# Wrong - using non-existent column
result = screener.screen(columns=['name', 'invalid_column'])

# Right - using valid columns
result = screener.screen(columns=['name', 'close', 'volume'])
```

**Solution**: Use valid column names from the default lists or check TradingView's available fields.

### Mistake: Exceeding API limits

```python
# This might fail due to rate limiting
for i in range(100):
    result = screener.screen(limit=50)
    time.sleep(0.1)  # Too short delay
```

**Solution**: Add appropriate delays between requests and respect TradingView's API limits.

## Advanced Usage Patterns

### Combining Multiple Filters

```python
# Find high-volume, reasonably-priced growth stocks
growth_filters = [
    {'left': 'close', 'operation': 'in_range', 'right': [20, 100]},
    {'left': 'volume', 'operation': 'greater', 'right': 1000000},
    {'left': 'change', 'operation': 'greater', 'right': 2},  # >2% change
    {'left': 'price_earnings_ttm', 'operation': 'eless', 'right': 25}
]

growth_stocks = screener.screen(
    market='america',
    filters=growth_filters,
    sort_by='change',
    sort_order='desc'
)
```

### Market Comparison Screening

```python
# Compare results across different markets
markets = ['america', 'uk', 'germany']
results = {}

for market in markets:
    results[market] = screener.screen(
        market=market,
        filters=[{'left': 'close', 'operation': 'greater', 'right': 50}],
        limit=5
    )

# Analyze and compare results
for market, result in results.items():
    print(f"{market.upper()}: {result['total']} stocks > $50")
```

### Technical Analysis Screening

```python
# Screen for stocks with specific technical characteristics
# Note: This requires using technical indicator columns
tech_filters = [
    {'left': 'close', 'operation': 'greater', 'right': 'EMA50'},  # Price above 50-day EMA
    {'left': 'RSI', 'operation': 'in_range', 'right': [30, 70]}   # RSI in neutral range
]

# You would need to ensure these columns are available in your plan
tech_results = screener.screen(
    market='america',
    filters=tech_filters,
    columns=['name', 'close', 'volume', 'RSI']
)
```

!!! note
    Some technical indicator columns may require premium TradingView accounts. Free accounts have limited access to advanced technical data.

!!! warning
    Always validate your filters and parameters before running screens. Invalid combinations can lead to empty results or API errors.
