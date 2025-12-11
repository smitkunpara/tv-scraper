# Fundamental Data

## Overview

The Fundamental Data module provides comprehensive access to financial fundamentals for stocks and other financial instruments. This module enables retrieval of detailed financial statements, ratios, and metrics that are essential for fundamental analysis.

## Why This Feature Exists

The fundamental data functionality exists to:

- Provide programmatic access to comprehensive financial statements and metrics
- Enable fundamental analysis and valuation modeling
- Support investment research and due diligence processes
- Facilitate comparative analysis across multiple companies
- Offer historical and current financial data for backtesting strategies
- Deliver standardized financial metrics for quantitative analysis

## Input Specification

### FundamentalGraphs Class Constructor

```python
FundamentalGraphs(export_result: bool = False, export_type: str = 'json')
```

**Parameters:**

- `export_result` (bool): Whether to export results to file. Defaults to `False`.
- `export_type` (str): Export format, either `'json'` or `'csv'`. Defaults to `'json'`.

### Symbol Validation

The module validates symbols with the following requirements:

- Must be a non-empty string
- Must include exchange prefix (e.g., `'NASDAQ:AAPL'`, `'NYSE:JPM'`)
- Exchange and symbol are case-insensitive but standardized to uppercase
- Examples: `'NASDAQ:AAPL'`, `'nyse:jpm'`, `'LSE:BP'`

### Supported Field Categories

The module organizes fundamental data into 9 comprehensive categories:

1. **Income Statement Fields** (12 fields)
2. **Balance Sheet Fields** (6 fields)
3. **Cash Flow Fields** (4 fields)
4. **Margin Fields** (8 fields)
5. **Profitability Fields** (5 fields)
6. **Liquidity Fields** (4 fields)
7. **Leverage Fields** (3 fields)
8. **Valuation Fields** (9 fields)
9. **Dividend Fields** (3 fields)

## Output Specification

### Response Structure

All methods return a standardized response format:

```python
{
    'status': 'success' or 'failed',
    'data': Dict containing the requested fundamental data,
    'error': str (only present if status is 'failed')
}
```

For comparison methods, the response includes additional structure:

```python
{
    'status': 'success' or 'failed',
    'data': List[Dict] containing fundamental data for each symbol,
    'comparison': Dict containing side-by-side comparison of metrics,
    'error': str (only present if status is 'failed')
}
```

### Field Schema and Meanings

#### Income Statement Fields

| Field | Description | Units |
|-------|-------------|-------|
| `total_revenue` | Total revenue for the period | Currency |
| `revenue_per_share_ttm` | Revenue per share (trailing twelve months) | Currency |
| `total_revenue_fy` | Total revenue (fiscal year) | Currency |
| `gross_profit` | Gross profit | Currency |
| `gross_profit_fy` | Gross profit (fiscal year) | Currency |
| `operating_income` | Operating income | Currency |
| `operating_income_fy` | Operating income (fiscal year) | Currency |
| `net_income` | Net income | Currency |
| `net_income_fy` | Net income (fiscal year) | Currency |
| `EBITDA` | Earnings Before Interest, Taxes, Depreciation, and Amortization | Currency |
| `basic_eps_net_income` | Basic earnings per share from net income | Currency |
| `earnings_per_share_basic_ttm` | Basic EPS (trailing twelve months) | Currency |
| `earnings_per_share_diluted_ttm` | Diluted EPS (trailing twelve months) | Currency |

#### Balance Sheet Fields

| Field | Description | Units |
|-------|-------------|-------|
| `total_assets` | Total assets | Currency |
| `total_assets_fy` | Total assets (fiscal year) | Currency |
| `cash_n_short_term_invest` | Cash and short-term investments | Currency |
| `cash_n_short_term_invest_fy` | Cash and short-term investments (fiscal year) | Currency |
| `total_debt` | Total debt | Currency |
| `total_debt_fy` | Total debt (fiscal year) | Currency |
| `stockholders_equity` | Stockholders' equity | Currency |
| `stockholders_equity_fy` | Stockholders' equity (fiscal year) | Currency |
| `book_value_per_share_fq` | Book value per share (fiscal quarter) | Currency |

#### Cash Flow Fields

| Field | Description | Units |
|-------|-------------|-------|
| `cash_f_operating_activities` | Cash flow from operating activities | Currency |
| `cash_f_operating_activities_fy` | Cash flow from operating activities (fiscal year) | Currency |
| `cash_f_investing_activities` | Cash flow from investing activities | Currency |
| `cash_f_investing_activities_fy` | Cash flow from investing activities (fiscal year) | Currency |
| `cash_f_financing_activities` | Cash flow from financing activities | Currency |
| `cash_f_financing_activities_fy` | Cash flow from financing activities (fiscal year) | Currency |
| `free_cash_flow` | Free cash flow | Currency |

#### Margin Fields

| Field | Description | Units |
|-------|-------------|-------|
| `gross_margin` | Gross margin | Percentage |
| `gross_margin_percent_ttm` | Gross margin percentage (trailing twelve months) | Percentage |
| `operating_margin` | Operating margin | Percentage |
| `operating_margin_ttm` | Operating margin (trailing twelve months) | Percentage |
| `pretax_margin_percent_ttm` | Pretax margin percentage (trailing twelve months) | Percentage |
| `net_margin` | Net margin | Percentage |
| `net_margin_percent_ttm` | Net margin percentage (trailing twelve months) | Percentage |
| `EBITDA_margin` | EBITDA margin | Percentage |

#### Profitability Fields

| Field | Description | Units |
|-------|-------------|-------|
| `return_on_equity` | Return on equity | Percentage |
| `return_on_equity_fq` | Return on equity (fiscal quarter) | Percentage |
| `return_on_assets` | Return on assets | Percentage |
| `return_on_assets_fq` | Return on assets (fiscal quarter) | Percentage |
| `return_on_investment_ttm` | Return on investment (trailing twelve months) | Percentage |

#### Liquidity Fields

| Field | Description | Units |
|-------|-------------|-------|
| `current_ratio` | Current ratio | Ratio |
| `current_ratio_fq` | Current ratio (fiscal quarter) | Ratio |
| `quick_ratio` | Quick ratio | Ratio |
| `quick_ratio_fq` | Quick ratio (fiscal quarter) | Ratio |

#### Leverage Fields

| Field | Description | Units |
|-------|-------------|-------|
| `debt_to_equity` | Debt to equity ratio | Ratio |
| `debt_to_equity_fq` | Debt to equity ratio (fiscal quarter) | Ratio |
| `debt_to_assets` | Debt to assets ratio | Ratio |

#### Valuation Fields

| Field | Description | Units |
|-------|-------------|-------|
| `market_cap_basic` | Market capitalization (basic) | Currency |
| `market_cap_calc` | Market capitalization (calculated) | Currency |
| `market_cap_diluted_calc` | Market capitalization (diluted, calculated) | Currency |
| `enterprise_value_fq` | Enterprise value (fiscal quarter) | Currency |
| `price_earnings_ttm` | Price to earnings ratio (trailing twelve months) | Ratio |
| `price_book_fq` | Price to book ratio (fiscal quarter) | Ratio |
| `price_sales_ttm` | Price to sales ratio (trailing twelve months) | Ratio |
| `price_free_cash_flow_ttm` | Price to free cash flow ratio (trailing twelve months) | Ratio |

#### Dividend Fields

| Field | Description | Units |
|-------|-------------|-------|
| `dividends_yield` | Dividend yield | Percentage |
| `dividends_per_share_fq` | Dividends per share (fiscal quarter) | Currency |
| `dividend_payout_ratio_ttm` | Dividend payout ratio (trailing twelve months) | Percentage |

## Behavioral Notes from Code and Tests

### Symbol Validation

1. **Exchange Prefix Requirement**: All symbols must include an exchange prefix (e.g., `'NASDAQ:AAPL'`). Symbols without prefixes will fail validation.

2. **Case Standardization**: Symbols are automatically converted to uppercase and stripped of whitespace.

3. **Error Handling**: Invalid symbols return a failed status with descriptive error messages.

### Data Retrieval

1. **Field Selection**: When no specific fields are requested, the module retrieves all 53 available fundamental fields.

2. **HTTP Requests**: The module uses TradingView's scanner API with a 10-second timeout.

3. **Rate Limiting**: No explicit rate limiting is implemented, but TradingView may impose limits on frequent requests.

4. **Error Conditions**: The module handles various error scenarios including:
   - Invalid symbols
   - HTTP errors (non-200 status codes)
   - Network connectivity issues
   - Empty or missing data responses

### Export Functionality

1. **File Formats**: Supports JSON and CSV export formats.

2. **File Naming**: Export files use the symbol name (with colon replaced by underscore) and data category in the filename.

3. **Automatic Export**: When `export_result=True`, data is automatically exported after retrieval.

### Comparison Functionality

1. **Default Fields**: When comparing multiple symbols without specifying fields, the module uses a standard set of key metrics:
   - `total_revenue`, `net_income`, `EBITDA`
   - `market_cap_basic`, `price_earnings_ttm`
   - `return_on_equity_fq`, `debt_to_equity_fq`

2. **Comparison Structure**: Returns both individual symbol data and a side-by-side comparison dictionary.

3. **Error Handling**: If no data is retrieved for any symbol, the comparison fails with an appropriate error message.

## Code Examples

### Basic Usage

```python
from tradingview_scraper.symbols.fundamental_graphs import FundamentalGraphs

# Initialize the scraper
fundamentals = FundamentalGraphs()

# Get all fundamental data for Apple
aapl_data = fundamentals.get_fundamentals(symbol='NASDAQ:AAPL')
print(aapl_data['data'])
```

### Specific Field Retrieval

```python
# Get only specific fields
revenue_data = fundamentals.get_fundamentals(
    symbol='NASDAQ:AAPL',
    fields=['total_revenue', 'net_income', 'EBITDA', 'market_cap_basic']
)
```

### Category-Specific Methods

```python
# Get income statement data
income_stmt = fundamentals.get_income_statement(symbol='NASDAQ:AAPL')

# Get balance sheet data
balance_sheet = fundamentals.get_balance_sheet(symbol='NASDAQ:AAPL')

# Get cash flow data
cash_flow = fundamentals.get_cash_flow(symbol='NASDAQ:AAPL')

# Get margin data
margins = fundamentals.get_margins(symbol='NASDAQ:AAPL')

# Get profitability ratios
profitability = fundamentals.get_profitability(symbol='NASDAQ:AAPL')

# Get liquidity ratios
liquidity = fundamentals.get_liquidity(symbol='NASDAQ:AAPL')

# Get leverage ratios
leverage = fundamentals.get_leverage(symbol='NASDAQ:AAPL')

# Get valuation metrics
valuation = fundamentals.get_valuation(symbol='NASDAQ:AAPL')

# Get dividend information
dividends = fundamentals.get_dividends(symbol='NASDAQ:AAPL')
```

### Multi-Symbol Comparison

```python
# Compare fundamentals across multiple companies
comparison = fundamentals.compare_fundamentals(
    symbols=['NASDAQ:AAPL', 'NASDAQ:MSFT', 'NASDAQ:GOOGL'],
    fields=['total_revenue', 'net_income', 'market_cap_basic', 'price_earnings_ttm']
)

# Access comparison data
for field, symbol_data in comparison['comparison'].items():
    print(f"{field}:")
    for symbol, value in symbol_data.items():
        print(f"  {symbol}: {value}")
```

### Export Functionality

```python
# Initialize with export enabled
fundamentals_exporter = FundamentalGraphs(export_result=True, export_type='json')

# Get data and automatically export to JSON
aapl_data = fundamentals_exporter.get_fundamentals(symbol='NASDAQ:AAPL')

# Compare and export to CSV
fundamentals_exporter.export_type = 'csv'
comparison = fundamentals_exporter.compare_fundamentals(
    symbols=['NASDAQ:AAPL', 'NASDAQ:MSFT']
)
```

### Advanced Usage

```python
# Analyze profitability trends across tech companies
tech_companies = ['NASDAQ:AAPL', 'NASDAQ:MSFT', 'NASDAQ:GOOGL', 'NASDAQ:AMZN', 'NASDAQ:META']

profitability_fields = [
    'return_on_equity_fq',
    'return_on_assets_fq',
    'return_on_investment_ttm',
    'net_margin_percent_ttm',
    'operating_margin_ttm'
]

profitability_comparison = fundamentals.compare_fundamentals(
    symbols=tech_companies,
    fields=profitability_fields
)

# Calculate average ROE across tech sector
roe_values = [
    data['return_on_equity_fq']
    for data in profitability_comparison['data']
    if 'return_on_equity_fq' in data
]
average_roe = sum(roe_values) / len(roe_values) if roe_values else 0
```

## Common Mistakes and Solutions

### Mistake: Invalid Symbol Format

```python
# Wrong - missing exchange prefix
result = fundamentals.get_fundamentals(symbol='AAPL')

# Right - include exchange prefix
result = fundamentals.get_fundamentals(symbol='NASDAQ:AAPL')
```

**Solution**: Always include the exchange prefix in the format `EXCHANGE:SYMBOL`.

### Mistake: Using Invalid Fields

```python
# Wrong - using non-existent field
result = fundamentals.get_fundamentals(
    symbol='NASDAQ:AAPL',
    fields=['invalid_field']
)

# Right - use valid field names
result = fundamentals.get_fundamentals(
    symbol='NASDAQ:AAPL',
    fields=['total_revenue', 'net_income']
)
```

**Solution**: Refer to the field categories or use the predefined category methods.

### Mistake: Empty or Invalid Symbol

```python
# Wrong - empty string
result = fundamentals.get_fundamentals(symbol='')

# Wrong - None
result = fundamentals.get_fundamentals(symbol=None)

# Right - valid symbol
result = fundamentals.get_fundamentals(symbol='NASDAQ:AAPL')
```

**Solution**: Always provide a valid, non-empty symbol string with exchange prefix.

### Mistake: Network Connectivity Issues

```python
# Handle potential network errors
result = fundamentals.get_fundamentals(symbol='NASDAQ:AAPL')

if result['status'] == 'failed':
    if 'Connection error' in result['error']:
        # Implement retry logic or fallback
        print("Network error, retrying...")
        time.sleep(5)
        result = fundamentals.get_fundamentals(symbol='NASDAQ:AAPL')
```

**Solution**: Implement proper error handling and retry logic for network-related issues.

### Mistake: No Data Available

```python
# Handle cases where no data is returned
result = fundamentals.get_fundamentals(symbol='INVALID:SYMBOL')

if result['status'] == 'failed':
    if 'No data found' in result['error']:
        # Handle missing data scenario
        print(f"No fundamental data available for {symbol}")
```

**Solution**: Check the error message and handle missing data scenarios gracefully.

## Environment Setup

To work with fundamental data, ensure your environment is properly set up:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
uv sync
```

## Test-Verified Constraints

Based on the test suite, the following constraints are verified:

1. **Symbol Validation**: Symbols must include exchange prefix and be non-empty strings
2. **Field Categories**: All field categories contain the expected number of fields
3. **Response Structure**: All methods return consistent status/data/error structure
4. **Error Handling**: Proper error messages for invalid inputs and network issues
5. **Comparison Logic**: Multi-symbol comparison works with custom field selection
6. **Real Data Testing**: Module successfully retrieves real fundamental data for major companies

The module has been tested with real data for major companies like Apple (AAPL) and Microsoft (MSFT), confirming its ability to retrieve comprehensive fundamental metrics from TradingView's API.