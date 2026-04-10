# Fundamentals

## Overview

`Fundamentals` fetches fundamental fields for a single `exchange:symbol`
from the TradingView scanner `GET /symbol` endpoint.

Public API surface in this class is currently:

- `get_fundamentals(exchange, symbol, fields=None)`

There are no category-specific helper methods (such as
`get_income_statement()` or `get_margins()`) implemented in this class.

## Constructor

```python
Fundamentals(
        export_result: bool = False,
        export_type: str = "json",   # "json" or "csv"
        timeout: int = 10,             # integer in [1, 300]
        cookie: str | None = None,
)
```

| Parameter | Type | Default | Behavior |
|---|---|---|---|
| `export_result` | `bool` | `False` | When `True`, successful data is exported via `_export()`. |
| `export_type` | `str` | `"json"` | Must be `"json"` or `"csv"`; invalid values raise `ValueError` at init. |
| `timeout` | `int` | `10` | Request timeout in seconds; must be an integer in `[1, 300]`. |
| `cookie` | `str \| None` | `None` | Optional cookie header; if `None`, `TRADINGVIEW_COOKIE` env var is used. |

## Method

### `get_fundamentals(exchange, symbol, fields=None)`

```python
get_fundamentals(
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        fields: list[str] | None = None,
) -> dict[str, Any]
```

| Parameter | Type | Required | Behavior |
|---|---|---|---|
| `exchange` | `str` | Yes | Passed to live exchange/symbol verification before data fetch. |
| `symbol` | `str` | Yes | Passed to live exchange/symbol verification before data fetch. |
| `fields` | `list[str] \| None` | No | `None` or `[]` means all fields in `ALL_FIELDS`; otherwise validates each requested field name. |

## Request Behavior

Each successful call path performs two HTTP GET calls to
`https://scanner.tradingview.com/symbol`:

1. Symbol verification (`verify_symbol_exchange`):
     - `symbol={EXCHANGE}:{SYMBOL}` (uppercased internally)
     - `fields=market`
     - `no_404=false`
2. Fundamentals fetch (`_fetch_symbol_fields`):
     - `symbol={EXCHANGE}:{SYMBOL}` (validated uppercase values)
     - `fields=<comma-separated requested fields>`
     - `no_404=true`

Additional request behavior:

- Headers include a browser `User-Agent` by default.
- If `cookie` is provided (or loaded from `TRADINGVIEW_COOKIE`), it is sent as
    the `cookie` header.
- Captcha pages are detected and returned as error responses.

## Field Behavior

### Selection and Validation Rules

- If `fields is None`, all 60 fields in `ALL_FIELDS` are requested.
- If `fields == []`, all 60 fields are also requested (`fields` is treated as
    falsy and replaced with `ALL_FIELDS`).
- If `fields` is not `None` and not a Python `list`, request fails with:
    - `Fields must be a list of strings or None.`
- Field names are case-sensitive.
- Duplicate requested field names are allowed by validation.
    - Result data is a dictionary, so duplicate keys collapse to one key.

### Field Sets

| Category | Count |
|---|---:|
| Income statement | 13 |
| Balance sheet | 9 |
| Cash flow | 7 |
| Margins | 8 |
| Profitability | 5 |
| Liquidity | 4 |
| Leverage | 3 |
| Valuation | 8 |
| Dividends | 3 |
| **Total (`ALL_FIELDS`)** | **60** |

Income statement:

`total_revenue`, `revenue_per_share_ttm`, `total_revenue_fy`, `gross_profit`, `gross_profit_fy`, `operating_income`, `operating_income_fy`, `net_income`, `net_income_fy`, `EBITDA`, `basic_eps_net_income`, `earnings_per_share_basic_ttm`, `earnings_per_share_diluted_ttm`

Balance sheet:

`total_assets`, `total_assets_fy`, `cash_n_short_term_invest`, `cash_n_short_term_invest_fy`, `total_debt`, `total_debt_fy`, `stockholders_equity`, `stockholders_equity_fy`, `book_value_per_share_fq`

Cash flow:

`cash_f_operating_activities`, `cash_f_operating_activities_fy`, `cash_f_investing_activities`, `cash_f_investing_activities_fy`, `cash_f_financing_activities`, `cash_f_financing_activities_fy`, `free_cash_flow`

Margins:

`gross_margin`, `gross_margin_percent_ttm`, `operating_margin`, `operating_margin_ttm`, `pretax_margin_percent_ttm`, `net_margin`, `net_margin_percent_ttm`, `EBITDA_margin`

Profitability:

`return_on_equity`, `return_on_equity_fq`, `return_on_assets`, `return_on_assets_fq`, `return_on_investment_ttm`

Liquidity:

`current_ratio`, `current_ratio_fq`, `quick_ratio`, `quick_ratio_fq`

Leverage:

`debt_to_equity`, `debt_to_equity_fq`, `debt_to_assets`

Valuation:

`market_cap_basic`, `market_cap_calc`, `market_cap_diluted_calc`, `enterprise_value_fq`, `price_earnings_ttm`, `price_book_fq`, `price_sales_ttm`, `price_free_cash_flow_ttm`

Dividends:

`dividends_yield`, `dividends_per_share_fq`, `dividend_payout_ratio_ttm`

Note:

- `DEFAULT_COMPARISON_FIELDS` exists as a class constant but is not used by
    `get_fundamentals()`.

## Response and Data Mapping

All responses use the standard envelope:

```python
{
        "status": "success" | "failed",
        "data": dict[str, Any] | None,
        "metadata": dict[str, Any],
        "error": str | None,
}
```

Successful `data` mapping:

- Always includes `"symbol": "{VALIDATED_EXCHANGE}:{VALIDATED_SYMBOL}"`
    (uppercase normalized by live verifier).
- For each requested field, value is read via `json_response.get(field)`.
- If a field is missing in API response, it is still present in output with
    value `None`.

Example success envelope:

```python
{
        "status": "success",
        "data": {
                "symbol": "NASDAQ:AAPL",
                "total_revenue": 416161000000,
                "net_income": 108000000000,
        },
        "metadata": {
                "exchange": "NASDAQ",
                "symbol": "AAPL",
                "fields": ["total_revenue", "net_income"],
                "data_category": "fundamentals",
        },
        "error": None,
}
```

## Metadata Behavior

Metadata content depends on where validation/error occurs:

| Scenario | Metadata keys typically present |
|---|---|
| Success or fetch-stage failure (`_fetch_symbol_fields`) | `exchange`, `symbol`, `fields`, `data_category` |
| Early failure in `get_fundamentals` (`fields` type/name validation) | `exchange`, `symbol`, `fields` (no `data_category`) |

Notes:

- Metadata uses function argument values captured by decorators.
- `metadata.exchange` and `metadata.symbol` are the values passed into
    `get_fundamentals()` (not forced to uppercase there).
- `data.symbol` is uppercase-normalized after verifier success.

## Error Behavior

Representative failures and message forms:

| Condition | `status` | `data` | Error message form |
|---|---|---|---|
| `fields` is not `list`/`None` | `failed` | `None` | `Fields must be a list of strings or None.` |
| Invalid field name(s) | `failed` | `None` | `Invalid field: ... Allowed field: ...` |
| Invalid exchange | `failed` | `None` | `Invalid exchange: '...'. ...` |
| Empty/invalid symbol | `failed` | `None` | `Symbol must be a non-empty string for exchange '...'.` |
| Unknown exchange:symbol (404 during verify) | `failed` | `None` | `Symbol '...' not found on exchange '...'. ...` |
| Verify retries exhausted | `failed` | `None` | `Could not verify 'EXCHANGE:SYMBOL' after 2 attempt(s): ...` |
| Captcha challenge | `failed` | `None` | `TradingView requested a captcha challenge.` |
| Network/HTTP request error | `failed` | `None` | `Network error: ...` |
| Empty HTTP body | `failed` | `None` | `Empty response from server.` |
| JSON decode failure | `failed` | `None` | `Failed to parse API response: ...` |
| Empty parsed payload (`{}` / falsy) | `failed` | `None` | `No data returned from API.` |
| API-level error payload | `failed` | `None` | `API error: ...` |

## Quick Examples

```python
from tv_scraper.scrapers.market_data import Fundamentals

scraper = Fundamentals()

# All 60 fields (same behavior for fields=None or fields=[])
all_fields = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")

# Specific field subset
subset = scraper.get_fundamentals(
        exchange="NASDAQ",
        symbol="AAPL",
        fields=["total_revenue", "net_income", "price_earnings_ttm"],
)
```
