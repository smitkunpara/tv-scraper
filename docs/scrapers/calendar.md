# Calendar Scraper

## Overview

`Calendar` fetches dividend and earnings events from TradingView's scanner endpoint:

- `POST https://scanner.tradingview.com/global/scan?label-product=calendar-dividends`
- `POST https://scanner.tradingview.com/global/scan?label-product=calendar-earnings`

It inherits from `ScannerScraper` (and `BaseScraper`) and returns the standard response envelope (`status`, `data`, `metadata`, `error`).

Implementation note:

- `get_dividends` and `get_earnings` are not decorated with `@catch_errors`.
- In this class, failed envelopes are returned explicitly for field-validation failures and `_request` failures.
- Unexpected runtime exceptions are not explicitly normalized by these methods.

## Constructor

```python
from tv_scraper.scrapers.events import Calendar

scraper = Calendar(
        export_result=False,
        export_type="json",
        timeout=10,
        cookie=None,
)
```

`Calendar` does not define its own `__init__`; it uses `BaseScraper.__init__`.

| Parameter | Type | Default | Behavior |
|-----------|------|---------|----------|
| `export_result` | `bool` | `False` | If `True`, successful results are exported via `_export(...)`. |
| `export_type` | `str` | `"json"` | Must be one of `"json"` or `"csv"`; otherwise constructor raises `ValueError`. |
| `timeout` | `int` | `10` | Request timeout in seconds; must be an `int` between `1` and `300`, else constructor raises `ValueError`. |
| `cookie` | `str \| None` | `None` | If `None`, falls back to `TRADINGVIEW_COOKIE` environment variable. |

## Public Methods

### get_dividends

```python
def get_dividends(
        timestamp_from: int | None = None,
        timestamp_to: int | None = None,
        markets: list[str] | None = None,
        fields: list[str] | None = None,
        lang: str = "en",
) -> dict[str, Any]
```

Uses:

- `label-product=calendar-dividends`
- date filter `left="dividend_ex_date_recent,dividend_ex_date_upcoming"`
- `DEFAULT_DIVIDEND_FIELDS` when custom fields are not used

### get_earnings

```python
def get_earnings(
        timestamp_from: int | None = None,
        timestamp_to: int | None = None,
        markets: list[str] | None = None,
        fields: list[str] | None = None,
        lang: str = "en",
) -> dict[str, Any]
```

Uses:

- `label-product=calendar-earnings`
- date filter `left="earnings_release_date,earnings_release_next_date"`
- `DEFAULT_EARNINGS_FIELDS` when custom fields are not used

## Default Timestamp Window Behavior

When timestamps are omitted, `_fetch_events(...)` computes:

```python
midnight = int(datetime.datetime.now().timestamp())
midnight -= midnight % 86400
```

Then:

- `timestamp_from = midnight - 3 * 86400` (if `timestamp_from is None`)
- `timestamp_to = midnight + 3 * 86400 + 86400 - 1` (if `timestamp_to is None`)

So the default range is:

- from `midnight - 259200`
- to `midnight + 345599`

Notes:

- If only one side is provided, only the missing side is defaulted.
- There is no range/order validation (for example, `timestamp_from > timestamp_to` is not rejected here).

## Fields, Markets, Lang, and Validation

### fields handling

- Starts with method-specific defaults (`DEFAULT_DIVIDEND_FIELDS` / `DEFAULT_EARNINGS_FIELDS`).
- Validation only runs when `fields` is truthy.
- Validation call: `validators.validate_fields(fields, default_fields, field_name="fields")`.
- If validation fails, method returns a failed envelope immediately and does not call `_request`.
- `fields=None` or `fields=[]` uses full defaults.

### markets handling

- `markets` is added to payload only when truthy:
    - `payload["markets"] = markets`
- `markets=None` or `markets=[]` means no `markets` key in payload.
- No market value validation is performed in this scraper.

### lang handling

- Always sent as `payload["options"]["lang"] = lang`.
- No language validation is performed in this scraper.

### validation scope summary

This scraper validates only custom `fields` content (when provided as truthy input). It does not validate:

- timestamp type/range/order
- market names
- language values

## Request Payload Schema

Shared payload sent to scanner:

```json
{
    "columns": ["field1", "field2"],
    "filter": [
        {
            "left": "<method-specific columns>",
            "operation": "in_range",
            "right": [1704067200, 1735689600]
        }
    ],
    "ignore_unknown_fields": false,
    "options": {
        "lang": "en"
    }
}
```

Optional key:

```json
{
    "markets": ["america", "uk"]
}
```

HTTP call:

```python
json_response, error_msg = self._request(
        "POST",
        url,
        json_payload=payload,
)
```

## Response Data Mapping

`json_response.get("data", [])` is expected to be a list of scanner rows:

```json
{
    "s": "EXCHANGE:SYMBOL",
    "d": [value_0, value_1, ...]
}
```

Mapped output item shape:

```json
{
    "symbol": "EXCHANGE:SYMBOL",
    "<field_0>": "d[0] or null",
    "<field_1>": "d[1] or null"
}
```

Mapping details:

- `symbol` comes from row key `s` (falls back to empty string if missing).
- Each requested column is mapped by index from `d`.
- Missing `d` entries are filled with `None`.
- If API `data` is not a list, it is replaced with `[]`.

## Response Envelope and Metadata

### Success response

```json
{
    "status": "success",
    "data": [],
    "metadata": {
        "event_type": "dividends",
        "total": 0,
        "timestamp_from": 1704067200,
        "timestamp_to": 1735689600,
        "markets": ["america"]
    },
    "error": null
}
```

On success, metadata keys added by calendar methods are:

- `event_type` (`"dividends"` or `"earnings"`)
- `total` (`len(data)`)
- `timestamp_from`
- `timestamp_to`
- `markets` only when `markets` input is truthy

### Failed response (handled failures)

Field validation failure or `_request` failure returns:

```json
{
    "status": "failed",
    "data": null,
    "metadata": {
        "event_type": "dividends"
    },
    "error": "..."
}
```

Handled failure metadata includes `event_type`; it does not add `timestamp_from`, `timestamp_to`, or `markets`.

## Default Field Lists

### DEFAULT_DIVIDEND_FIELDS

- `dividend_ex_date_recent`
- `dividend_ex_date_upcoming`
- `logoid`
- `name`
- `description`
- `dividends_yield`
- `dividend_payment_date_recent`
- `dividend_payment_date_upcoming`
- `dividend_amount_recent`
- `dividend_amount_upcoming`
- `fundamental_currency_code`
- `market`

### DEFAULT_EARNINGS_FIELDS

- `earnings_release_next_date`
- `earnings_release_date`
- `logoid`
- `name`
- `description`
- `earnings_per_share_fq`
- `earnings_per_share_forecast_next_fq`
- `eps_surprise_fq`
- `eps_surprise_percent_fq`
- `revenue_fq`
- `revenue_forecast_next_fq`
- `market_cap_basic`
- `earnings_release_time`
- `earnings_release_next_time`
- `earnings_per_share_forecast_fq`
- `revenue_forecast_fq`
- `fundamental_currency_code`
- `market`
- `earnings_publication_type_fq`
- `earnings_publication_type_next_fq`
- `revenue_surprise_fq`
- `revenue_surprise_percent_fq`
