# Technicals (Technical Indicators)

## Overview

`Technicals` fetches indicator values from TradingView scanner endpoint for one `exchange:symbol` pair.

It uses:
- local validation (`exchange`, `symbol`, `timeframe`, indicator names)
- live symbol verification (`verify_symbol_exchange`)
- a single HTTP request to `https://scanner.tradingview.com/symbol`

## Import

```python
from tv_scraper.scrapers.market_data import Technicals
```

## Constructor

```python
Technicals(export_result: bool = False, export_type: str = "json", timeout: int = 10)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `export_result` | `bool` | `False` | Export successful `data` to file. |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"`. |
| `timeout` | `int` | `10` | Request timeout in seconds. |

## Method Signature

```python
get_technicals(
    exchange: EXCHANGE_LITERAL,
    symbol: str,
    timeframe: TIMEFRAME_LITERAL = "1d",
    technical_indicators: list[str] | None = None,
    all_indicators: bool = False,
    fields: list[str] | None = None,
) -> dict[str, Any]
```

`exchange` and `symbol` are required (no defaults in implementation).

## Parameters

| Parameter | Type | Default | Implementation behavior |
|---|---|---|---|
| `exchange` | `EXCHANGE_LITERAL` | — | Checked by `validate_exchange`; case-insensitive validation. |
| `symbol` | `str` | — | Checked by `validate_symbol`; must be non-empty after `strip()`. |
| `timeframe` | `TIMEFRAME_LITERAL` | `"1d"` | Checked by `validate_timeframe` against supported keys. |
| `technical_indicators` | `list[str] \| None` | `None` | Used only when `all_indicators=False`; validated with `validate_indicators`. |
| `all_indicators` | `bool` | `False` | When `True`, uses full `INDICATORS` constant and ignores `technical_indicators` for request construction. |
| `fields` | `list[str] \| None` | `None` | Optional post-fetch output filter. Not validator-checked. |

Supported values:
- exchanges: [Supported Exchanges](../supported_data.md#supported-exchanges)
- indicators: [Supported Indicators](../supported_data.md#supported-indicators)
- timeframes: [Supported Timeframes](../supported_data.md#supported-timeframes)

## Validation and Execution Order

Validation and control flow in method order:

1. `validate_exchange(exchange)`
2. `validate_symbol(exchange, symbol)`
3. `validate_timeframe(timeframe)`
4. Indicator selection: if `all_indicators=True`, uses `list(INDICATORS)`; else validates and uses `technical_indicators`; if neither is provided, raises `ValidationError("No indicators provided. Use technical_indicators or set all_indicators=True.")`.
5. `verify_symbol_exchange(exchange, symbol)` (live HTTP check; runs after local checks).

Important precedence behavior:
- If both `all_indicators=True` and `technical_indicators` are provided, request uses all indicators.
- `technical_indicators` is still preserved in metadata when explicitly passed and non-`None`.

## Timeframe Handling and Key Mapping

Internal timeframe map (`TIMEFRAMES`):

| Input timeframe | API suffix value |
|---|---|
| `1m` | `1` |
| `5m` | `5` |
| `15m` | `15` |
| `30m` | `30` |
| `1h` | `60` |
| `2h` | `120` |
| `4h` | `240` |
| `1d` | `1D` |
| `1w` | `1W` |
| `1M` | `1M` |

Request field key construction:
- Non-daily (`timeframe_value != "1D"`): append suffix, e.g. `RSI|60`, `MACD.macd|240`.
- Daily (`1d`): no suffix is appended (uses plain indicator keys).

Response key normalization:
- For non-daily requests, `_revise_response` strips `|...` suffix from keys before returning `data`.
- For daily (`1D`) and empty suffix, keys are returned unchanged.

## Request and Data Mapping

Request details:

```text
GET https://scanner.tradingview.com/symbol
params:
  symbol=<EXCHANGE>:<SYMBOL>
  fields=<comma-joined indicator keys>
  no_404=true
```

Mapping behavior:
- Result values are read via `json_response.get(requested_key)` for each requested key.
- Missing keys are returned as `None` values in `data` for those indicators.

`fields` filtering behavior:
- Applied after suffix stripping.
- Each entry in `fields` is normalized with regex `re.sub(r"\|.*", "", field)`.
- Filtering runs only when `fields` is truthy (`if fields:`).
- `fields=[]` does not filter anything (treated as false).
- Unknown field names are silently ignored; if no names match, response is success with `data={}`.

## Response Envelope and Metadata

Public method is decorated with `@catch_errors`. Responses are always envelope-shaped:

```json
{
  "status": "success | failed",
  "data": {"...": "..."},
  "metadata": {},
  "error": null
}
```

On failure, `data` is usually `null` and `error` is a string message.

Metadata behavior:
- Metadata is auto-captured from bound method arguments with defaults applied.
- Only non-`None` arguments are included.
- Typical keys: `exchange`, `symbol`, `timeframe`, `all_indicators`.
- `technical_indicators` and `fields` appear only when passed as non-`None`.

Success example:

```json
{
  "status": "success",
  "data": {
    "RSI": 54.21,
    "MACD.macd": 0.15,
    "MACD.signal": 0.08
  },
  "metadata": {
    "exchange": "NASDAQ",
    "symbol": "AAPL",
    "timeframe": "4h",
    "technical_indicators": ["RSI", "MACD.macd", "MACD.signal"],
    "all_indicators": false
  },
  "error": null
}
```

Error example:

```json
{
  "status": "failed",
  "data": null,
  "metadata": {
    "exchange": "INVALID_EXCHANGE",
    "symbol": "AAPL",
    "timeframe": "1d",
    "technical_indicators": ["RSI"],
    "all_indicators": false
  },
  "error": "Invalid exchange: 'INVALID_EXCHANGE'. Valid exchanges include: ..."
}
```

## Error and Edge Cases

Returned as `status="failed"` (not raised to caller):

- Invalid exchange
- Empty/invalid symbol
- Invalid timeframe
- Invalid indicator(s)
- No indicators provided when `all_indicators=False`
- Live symbol verification failure (not found or network issues)
- Request errors from `_request`, including captcha challenge, network error, JSON parse error, and empty HTTP body
- Parsed JSON is empty dict (`Empty response for EXCHANGE:SYMBOL with timeframe ...`)

Additional behavior to be aware of:
- Method may return success even if some requested indicators are missing; those values become `None`.
- Metadata preserves original caller input casing even though verification logic uppercases internally.

## Usage Examples

Specific indicators:

```python
from tv_scraper.scrapers.market_data import Technicals

scraper = Technicals()
result = scraper.get_technicals(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="4h",
    technical_indicators=["RSI", "EMA50", "MACD.macd"],
)

print(result["status"])
print(result["data"])
```

All indicators mode:

```python
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    all_indicators=True,
)

print(len(result["data"]))
```

Fields filtering:

```python
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1h",
    technical_indicators=["RSI", "MACD.macd", "Stoch.K"],
    fields=["RSI", "MACD.macd"],
)

print(result["data"])
```
