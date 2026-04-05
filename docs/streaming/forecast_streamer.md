# ForecastStreamer API

The `ForecastStreamer` class provides analyst forecast data for stock symbols via TradingView's WebSocket API. This includes price targets, EPS data, and revenue estimates.

## Important Limitations

- **Stock symbols only**: Forecast data is only available for stock symbols (e.g., `"NYSE:A"`, `"NASDAQ:AAPL"`).
- **Not available for**: Crypto, forex, indices, or other non-stock instruments.

## Installation

```python
from tv_scraper.streaming import ForecastStreamer
```

## Constructor

```python
fs = ForecastStreamer(
    export_result=False,        # Save results to file
    export_type="json",        # "json" or "csv"
    cookie="<TRADINGVIEW_COOKIE>",  # Optional: session cookie
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to save results to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `cookie` | `str \| None` | `None` | TradingView session cookie |

## Methods

### `get_forecast()`

Fetch analyst forecast data for stock symbols.

```python
result = fs.get_forecast(
    exchange="NYSE",
    symbol="A",
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | **required** | Exchange name (e.g., `"NYSE"`, `"NASDAQ"`) |
| `symbol` | `str` | **required** | Stock symbol (e.g., `"A"`, `"AAPL"`) |

#### Success Response

```python
{
    "status": "success",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": 114.5,
        "average_price_target": 162.8,
        "highest_price_target": 185,
        "lowest_price_target": 145,
        "median_price_target": 160,
        "yearly_eps_data": [
            {"FiscalPeriod": "2026", "Estimate": 5.9},
            {"FiscalPeriod": "2025", "Estimate": 5.2}
        ],
        "quarterly_eps_data": [
            {"FiscalPeriod": "2026-Q1", "Estimate": 1.36},
            {"FiscalPeriod": "2025-Q4", "Estimate": 1.28}
        ],
        "yearly_revenue_data": [
            {"FiscalPeriod": "2026", "Estimate": 7395056494},
            {"FiscalPeriod": "2025", "Estimate": 6823456789}
        ],
        "quarterly_revenue_data": [
            {"FiscalPeriod": "2026-Q1", "Estimate": 1807792308},
            {"FiscalPeriod": "2025-Q4", "Estimate": 1756421356}
        ]
    },
    "metadata": {
        "exchange": "NYSE",
        "symbol": "A",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "previous_close_price",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency",
            "yearly_eps_data",
            "yearly_revenue_data"
        ]
    },
    "error": null
}
```

#### Error Response - Non-Stock Symbol (Crypto)

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "BINANCE",
        "symbol": "BTCUSDT"
    },
    "error": "forecast is not available for this symbol because it is type: crypto"
}
```

#### Error Response - Non-Stock Symbol (Forex)

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "FX",
        "symbol": "EURUSD"
    },
    "error": "forecast is not available for this symbol because it is type: forex"
}
```

#### Error Response - Invalid Exchange

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "INVALID_EXCHANGE",
        "symbol": "A"
    },
    "error": "Invalid exchange: 'INVALID_EXCHANGE'. Did you mean: 'NYSE'?"
}
```

#### Error Response - Invalid Symbol

```python
{
    "status": "failed",
    "data": null,
    "metadata": {
        "exchange": "NYSE",
        "symbol": "INVALID_SYMBOL"
    },
    "error": "Symbol 'INVALID_SYMBOL' not found on exchange 'NYSE'"
}
```

#### Error Response - Partial Data (Missing Keys)

```python
{
    "status": "failed",
    "data": {
        "revenue_currency": "USD",
        "previous_close_price": null,
        "average_price_target": 162.8,
        "highest_price_target": 185,
        "lowest_price_target": 145,
        "median_price_target": 160,
        "yearly_eps_data": null,
        "quarterly_eps_data": [
            {"FiscalPeriod": "2026-Q1", "Estimate": 1.36}
        ],
        "yearly_revenue_data": null,
        "quarterly_revenue_data": [
            {"FiscalPeriod": "2026-Q1", "Estimate": 1807792308}
        ]
    },
    "metadata": {
        "exchange": "NYSE",
        "symbol": "A",
        "available_output_keys": [
            "average_price_target",
            "highest_price_target",
            "lowest_price_target",
            "median_price_target",
            "quarterly_eps_data",
            "quarterly_revenue_data",
            "revenue_currency"
        ]
    },
    "error": "failed to fetch keys: previous_close_price, yearly_eps_data, yearly_revenue_data"
}
```

### `connect()`

Create and return a connected StreamHandler with JWT token.

```python
handler = fs.connect()
```

Returns a connected `StreamHandler` instance.

## Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `revenue_currency` | `str` | Currency for revenue values (e.g., "USD") |
| `previous_close_price` | `float \| None` | Previous closing price |
| `average_price_target` | `float \| None` | Average analyst price target |
| `highest_price_target` | `float \| None` | Highest analyst price target |
| `lowest_price_target` | `float \| None` | Lowest analyst price target |
| `median_price_target` | `float \| None` | Median analyst price target |
| `yearly_eps_data` | `list \| None` | Annual EPS estimates |
| `quarterly_eps_data` | `list \| None` | Quarterly EPS estimates |
| `yearly_revenue_data` | `list \| None` | Annual revenue estimates |
| `quarterly_revenue_data` | `list \| None` | Quarterly revenue estimates |

## Usage Examples

### Basic - Get forecast for a stock

```python
from tv_scraper.streaming import ForecastStreamer

fs = ForecastStreamer()
result = fs.get_forecast(exchange="NYSE", symbol="A")

if result["status"] == "success":
    data = result["data"]
    print(f"Price targets: {data['lowest_price_target']} - {data['highest_price_target']}")
    print(f"Average target: {data['average_price_target']}")
    print(f"Median target: {data['median_price_target']}")
```

### Multiple stocks

```python
stocks = [
    ("NYSE", "A"),
    ("NASDAQ", "AAPL"),
    ("NASDAQ", "MSFT"),
]

fs = ForecastStreamer()
for exchange, symbol in stocks:
    result = fs.get_forecast(exchange=exchange, symbol=symbol)
    if result["status"] == "success":
        print(f"{exchange}:{symbol} - Avg target: {result['data']['average_price_target']}")
    else:
        print(f"{exchange}:{symbol} - Error: {result['error']}")
```

### With export

```python
fs = ForecastStreamer(export_result=True, export_type="json")
result = fs.get_forecast(exchange="NASDAQ", symbol="AAPL")
# Creates: export/forecast_aapl_20260215-120000.json
```

### Check available keys

```python
result = fs.get_forecast(exchange="NYSE", symbol="A")
if result["status"] == "success":
    available = result["metadata"]["available_output_keys"]
    print(f"Available data: {available}")
else:
    # Even on failure, we get available keys
    if "available_output_keys" in result["metadata"]:
        print(f"Partial data available: {result['metadata']['available_output_keys']}")
```

## Error Handling

All public methods return standardized response envelopes and never raise exceptions.

```python
result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")

# Always check status
if result["status"] == "failed":
    print(f"Error: {result['error']}")
    print(f"Metadata: {result['metadata']}")

    # Even on failure, partial data may be available
    if result["data"]:
        print(f"Partial data: {result['data']}")
```

## Common Error Scenarios

### 1. Crypto symbols

```python
result = fs.get_forecast(exchange="BINANCE", symbol="BTCUSDT")
# Error: "forecast is not available for this symbol because it is type: crypto"
```

### 2. Forex symbols

```python
result = fs.get_forecast(exchange="FX", symbol="EURUSD")
# Error: "forecast is not available for this symbol because it is type: forex"
```

### 3. Index symbols

```python
result = fs.get_forecast(exchange="INDEX", symbol="SPX")
# Error: "forecast is not available for this symbol because it is type: index"
```

### 4. Invalid exchange

```python
result = fs.get_forecast(exchange="INVALID", symbol="A")
# Error: "Invalid exchange: 'INVALID_EXCHANGE'. Did you mean: 'NYSE'?"
```

### 5. Invalid symbol

```python
result = fs.get_forecast(exchange="NYSE", symbol="NOTEXIST")
# Error: "Symbol 'NOTEXIST' not found on exchange 'NYSE'"
```

## Inheritance

`ForecastStreamer` extends `BaseStreamer` which extends `BaseScraper`, providing:

- `_success_response()` - Build standardized success response
- `_error_response()` - Build standardized error response
- `_export()` - Export data to file
- `validator` - DataValidator singleton for exchange/symbol validation

## Notes

- Uses WebSocket quote updates as the source of forecast data
- Output key mappings are fixed and deterministic
- Public API follows the standard envelope: `status`, `data`, `metadata`, `error`
- Some keys may be `null` if TradingView doesn't have that data for a particular symbol
