# Symbol Overview

## Overview

The Symbol Overview module provides comprehensive functionality to retrieve detailed information about financial symbols from TradingView. This includes profile data, market statistics, financial metrics, performance indicators, technical analysis, and fundamental information.

!!! note "Supported Data"
    For a complete list of supported exchanges and other data types, see [Supported Data](supported_data.md).

## Input Specification

### Overview Class Constructor

```python
Overview(export_result: bool = False, export_type: str = 'json')
```

**Parameters:**

- `export_result` (bool): Whether to export results to a file. Defaults to `False`.
- `export_type` (str): Export format, either `'json'` or `'csv'`. Defaults to `'json'`.

### Main Method: get_symbol_overview

```python
get_symbol_overview(symbol: str, fields: Optional[List[str]] = None) -> Dict
```

**Parameters:**

- `symbol` (str): The symbol to get overview for (e.g., `'NASDAQ:AAPL'`, `'BITSTAMP:BTCUSD'`).
  - **Required**: Yes
  - **Format**: Must include exchange prefix (e.g., `'NASDAQ:AAPL'`)
  - **Validation**: Must be non-empty string with exchange prefix
- `fields` (List[str], optional): Specific fields to retrieve. If `None`, retrieves all fields.

**Constraints:**

- Symbol must include exchange prefix (e.g., `'NASDAQ:AAPL'`, not just `'AAPL'`)
- Exchange must be valid and supported (see [supported_data.md](supported_data.md))
- Field names must match exactly with defined field categories

### Convenience Methods

The module provides specialized methods for specific data categories:

```python
# Profile data
get_profile(symbol: str) -> Dict

# Market statistics
get_statistics(symbol: str) -> Dict

# Financial metrics
get_financials(symbol: str) -> Dict

# Performance metrics
get_performance(symbol: str) -> Dict

# Technical indicators
get_technicals(symbol: str) -> Dict
```

## Output Specification

### Response Schema

All methods return a dictionary with the following structure:

```python
{
    'status': str,      # 'success' or 'failed'
    'data': Dict,       # Symbol overview data (if successful)
    'error': str        # Error message (if failed)
}
```

### Data Categories and Expected Fields

#### 1. Profile Data (BASIC_FIELDS)

```python
{
    'name': str,               # Symbol name (e.g., 'AAPL')
    'description': str,        # Company description
    'type': str,               # Instrument type
    'subtype': str,            # Instrument subtype
    'exchange': str,           # Exchange name
    'country': str,            # Country of origin
    'sector': str,             # Industry sector
    'industry': str,           # Specific industry
    'symbol': str              # Full symbol with exchange prefix
}
```

#### 2. Price Data (PRICE_FIELDS)

```python
{
    'close': float,            # Current price
    'change': float,           # Price change percentage
    'change_abs': float,       # Absolute price change
    'change_from_open': float, # Change from opening price
    'high': float,             # Day's high price
    'low': float,              # Day's low price
    'open': float,             # Opening price
    'volume': float,           # Trading volume
    'Value.Traded': float,     # Value traded
    'price_52_week_high': float, # 52-week high
    'price_52_week_low': float   # 52-week low
}
```

#### 3. Market Statistics (MARKET_FIELDS + VALUATION_FIELDS + DIVIDEND_FIELDS)

```python
{
    # Market Capitalization
    'market_cap_basic': float,         # Basic market cap
    'market_cap_calc': float,          # Calculated market cap
    'market_cap_diluted_calc': float,  # Diluted market cap

    # Shares Information
    'shares_outstanding': float,       # Outstanding shares
    'shares_float': float,             # Float shares
    'shares_diluted': float,           # Diluted shares

    # Valuation Ratios
    'price_earnings_ttm': float,       # P/E ratio (TTM)
    'price_book_fq': float,            # Price to book ratio
    'price_sales_ttm': float,          # Price to sales ratio
    'price_free_cash_flow_ttm': float, # Price to free cash flow

    # Earnings Information
    'earnings_per_share_basic_ttm': float,  # Basic EPS
    'earnings_per_share_diluted_ttm': float, # Diluted EPS
    'book_value_per_share_fq': float,        # Book value per share

    # Dividend Information
    'dividends_yield': float,               # Dividend yield
    'dividends_per_share_fq': float,        # Dividends per share
    'dividend_payout_ratio_ttm': float      # Payout ratio
}
```

#### 4. Financial Metrics (FINANCIAL_FIELDS)

```python
{
    'total_revenue': float,                # Total revenue
    'revenue_per_share_ttm': float,        # Revenue per share
    'net_income_fy': float,                # Net income (fiscal year)
    'gross_margin_percent_ttm': float,     # Gross margin %
    'operating_margin_ttm': float,         # Operating margin
    'net_margin_percent_ttm': float,       # Net margin %
    'return_on_equity_fq': float,          # ROE
    'return_on_assets_fq': float,          # ROA
    'return_on_investment_ttm': float,     # ROI
    'debt_to_equity_fq': float,            # Debt to equity ratio
    'current_ratio_fq': float,             # Current ratio
    'quick_ratio_fq': float,               # Quick ratio
    'EBITDA': float,                       # EBITDA
    'employees': int                        # Number of employees
}
```

#### 5. Performance Metrics (PERFORMANCE_FIELDS + VOLATILITY_FIELDS)

```python
{
    # Performance Metrics
    'Perf.W': float,   # Weekly performance
    'Perf.1M': float,  # 1-month performance
    'Perf.3M': float,  # 3-month performance
    'Perf.6M': float,  # 6-month performance
    'Perf.Y': float,   # Yearly performance
    'Perf.YTD': float, # Year-to-date performance

    # Volatility Metrics
    'Volatility.D': float,   # Daily volatility
    'Volatility.W': float,   # Weekly volatility
    'Volatility.M': float,   # Monthly volatility
    'beta_1_year': float     # 1-year beta
}
```

#### 6. Technical Indicators (TECHNICAL_FIELDS + VOLATILITY_FIELDS)

```python
{
    # Recommendations
    'Recommend.All': str,    # Overall recommendation

    # Momentum Indicators
    'RSI': float,            # Relative Strength Index
    'CCI20': float,          # Commodity Channel Index
    'ADX': float,            # Average Directional Index
    'Stoch.K': float,        # Stochastic %K

    # MACD
    'MACD.macd': float,      # MACD line

    # Volatility
    'ATR': float             # Average True Range

    # Additional volatility fields from VOLATILITY_FIELDS
    'Volatility.D': float,   # Daily volatility
    'Volatility.W': float,   # Weekly volatility
    'Volatility.M': float,   # Monthly volatility
    'beta_1_year': float     # 1-year beta
}
```

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.overview import Overview

# Initialize overview scraper
overview = Overview()

# Get full overview for Apple stock
result = overview.get_symbol_overview(symbol='NASDAQ:AAPL')

if result['status'] == 'success':
    print(f"Symbol: {result['data']['symbol']}")
    print(f"Name: {result['data']['name']}")
    print(f"Current Price: {result['data']['close']}")
    print(f"Market Cap: {result['data']['market_cap_basic']}")
else:
    print(f"Error: {result['error']}")
```

### Custom Fields

```python
# Get specific fields only
custom_fields = ['name', 'close', 'volume', 'market_cap_basic', 'change']
result = overview.get_symbol_overview(
    symbol='BITSTAMP:BTCUSD',
    fields=custom_fields
)

if result['status'] == 'success':
    data = result['data']
    print(f"BTC Price: ${data['close']}")
    print(f"24h Volume: {data['volume']}")
    print(f"24h Change: {data['change']}%")
```

### Using Convenience Methods

```python
# Get profile information
profile = overview.get_profile('NASDAQ:AAPL')
if profile['status'] == 'success':
    print(f"Company: {profile['data']['name']}")
    print(f"Sector: {profile['data']['sector']}")
    print(f"Industry: {profile['data']['industry']}")

# Get financial metrics
financials = overview.get_financials('NASDAQ:AAPL')
if financials['status'] == 'success':
    print(f"Revenue: ${financials['data']['total_revenue']:,.2f}")
    print(f"Net Income: ${financials['data']['net_income_fy']:,.2f}")
    print(f"ROE: {financials['data']['return_on_equity_fq']}%")

# Get technical indicators
technicals = overview.get_technicals('NASDAQ:AAPL')
if technicals['status'] == 'success':
    print(f"RSI: {technicals['data']['RSI']}")
    print(f"Recommendation: {technicals['data']['Recommend.All']}")
```

### Exporting Results

```python
# Export results to JSON
overview_export = Overview(export_result=True, export_type='json')
result = overview_export.get_symbol_overview('NASDAQ:AAPL')

# Export results to CSV
csv_exporter = Overview(export_result=True, export_type='csv')
result = csv_exporter.get_symbol_overview('BITSTAMP:BTCUSD')
```

## Common Mistakes and Solutions

### Mistake: Invalid Symbol Format

```python
# Wrong - missing exchange prefix
result = overview.get_symbol_overview('AAPL')

# Right - include exchange prefix
result = overview.get_symbol_overview('NASDAQ:AAPL')
```

**Solution**: Always include the exchange prefix in the symbol format `'EXCHANGE:SYMBOL'`.

### Mistake: Using Unsupported Exchange

```python
# Wrong - unsupported exchange
result = overview.get_symbol_overview('INVALID:SYMBOL')

# Right - use supported exchange
result = overview.get_symbol_overview('NASDAQ:AAPL')
```

**Solution**: Check [supported_data.md](supported_data.md) for the complete list of supported exchanges.

### Mistake: Invalid Field Names

```python
# Wrong - invalid field name
result = overview.get_symbol_overview('NASDAQ:AAPL', fields=['invalid_field'])

# Right - use valid field names
result = overview.get_symbol_overview('NASDAQ:AAPL', fields=['close', 'volume'])
```

**Solution**: Use field names from the defined field categories in the module.

### Mistake: Not Handling Response Status

```python
# Wrong - not checking status
result = overview.get_symbol_overview('NASDAQ:AAPL')
print(result['data']['close'])  # May fail if status is 'failed'

# Right - check status first
result = overview.get_symbol_overview('NASDAQ:AAPL')
if result['status'] == 'success':
    print(result['data']['close'])
else:
    print(f"Error: {result['error']}")
```

**Solution**: Always check the `status` field before accessing the `data` field.
