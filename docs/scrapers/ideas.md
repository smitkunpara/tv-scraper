# Ideas Scraper

## Overview

The Ideas scraper fetches TradingView symbol ideas from:

- `/symbols/{EXCHANGE}-{SYMBOL}/ideas/` for page 1
- `/symbols/{EXCHANGE}-{SYMBOL}/ideas/page-{N}/` for page N > 1

It supports:

- Input validation via shared validators
- Multi-page scraping with ThreadPoolExecutor
- Sorting by `popular` or `recent`
- Optional export (JSON/CSV) through BaseScraper

## Constructor

```python
from tv_scraper.scrapers.social import Ideas

scraper = Ideas(
    export_result=False,
    export_type="json",
    timeout=10,
    cookie=None,
    max_workers=3,
)
```

| Parameter | Type | Default | Behavior |
|-----------|------|---------|----------|
| `export_result` | `bool` | `False` | If `True`, successful results are exported via `_export(...)`. |
| `export_type` | `str` | `"json"` | Must be `"json"` or `"csv"` (validated in BaseScraper). |
| `timeout` | `int` | `10` | Per-request timeout in seconds (must be an integer from 1 to 300, validated in BaseScraper). |
| `cookie` | `str \| None` | `None` | If `None`, BaseScraper falls back to `TRADINGVIEW_COOKIE` env var. |
| `max_workers` | `int` | `3` | Stored as `self._max_workers = max(1, max_workers)` (minimum clamped to `1`). |

## get_ideas

```python
result = scraper.get_ideas(
    exchange="NASDAQ",
    symbol="AAPL",
    start_page=1,
    end_page=3,
    sort_by="popular",
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `EXCHANGE_LITERAL` | required | Exchange used in validation and URL slug generation. |
| `symbol` | `str` | required | Symbol used in validation and URL slug generation. |
| `start_page` | `int` | `1` | First page (inclusive), must be >= 1. |
| `end_page` | `int` | `1` | Last page (inclusive), must be >= `start_page`. |
| `sort_by` | `"popular" \| "recent"` | `"popular"` | Sort mode. |

### Validation

`get_ideas` performs validation in this order:

1. `start_page >= 1` or raises ValidationError.
2. `end_page >= start_page` or raises ValidationError.
3. `validators.verify_symbol_exchange(exchange, symbol)`.
4. `validators.validate_choice("sort_by", sort_by, {"popular", "recent"})`.

Because `get_ideas` is decorated with `@catch_errors`, validation errors are returned in the standard failed envelope instead of being raised to callers.

## Concurrency And Page Collection Behavior

For `start_page..end_page` (inclusive), `get_ideas`:

1. Creates one future per page using `ThreadPoolExecutor(max_workers=self._max_workers)`.
2. Consumes futures with `as_completed(..., timeout=self.timeout * 2)`.
3. Reads each result as `(page_items, error_msg)` from `_scrape_page` using `future.result(timeout=self.timeout)`.

Important behavior:

- Result order follows future completion order, not page order.
- If a page returns an error message, that page is added to `failed_pages`.
- If any page fails, final response is `status="failed"` and `data=None`.
- On failed pages, already collected articles are counted in metadata (`total`) but are not returned in `data`.
- If `as_completed` times out globally, the decorator converts that unexpected exception into a failed envelope with `error` prefixed by `Unexpected error:`.
- If a page response payload is not a dictionary, that page is logged and treated as an empty page (`[]`) rather than a failed page.

## Sorting Behavior

`_scrape_page` always sends:

- `component-data-only=1`

And conditionally sends:

- `sort=recent` only when `sort_by == "recent"`

For `sort_by="popular"`, no explicit `sort` query parameter is sent.

## Failed Page Handling

Page-level failures are tracked as a Python list of tuples:

- `(page_number, error_message)`

If `failed_pages` is non-empty, `get_ideas` returns:

- `status: "failed"`
- `data: null`
- `error: "Failed pages: ... Articles collected so far: ..."`
- `metadata` containing call arguments plus `total`, `pages`, and `failed_pages`

## Idea Output Schema

Each idea item is mapped by `_map_idea` as:

```json
{
  "title": "string",
  "description": "string",
  "preview_image": [],
  "chart_url": "string",
  "comments_count": 0,
  "views_count": 0,
  "author": "string",
  "likes_count": 0,
  "timestamp": 0
}
```

Mapping defaults when fields are missing:

- Strings default to `""`
- Counts default to `0`
- `preview_image` defaults to `[]`

## Response Envelope

All responses follow the BaseScraper envelope:

```json
{
  "status": "success | failed",
  "data": "payload or null",
  "metadata": {},
  "error": "string or null"
}
```

### Success Example

```json
{
  "status": "success",
  "data": [
    {
      "title": "Idea title",
      "description": "Body",
      "preview_image": [],
      "chart_url": "/chart/abc",
      "comments_count": 2,
      "views_count": 10,
      "author": "trader",
      "likes_count": 5,
      "timestamp": 1700000000
    }
  ],
  "metadata": {
    "exchange": "NASDAQ",
    "symbol": "AAPL",
    "start_page": 1,
    "end_page": 1,
    "sort_by": "popular",
    "total": 1,
    "pages": 1
  },
  "error": null
}
```

### Failed Pages Example

```json
{
  "status": "failed",
  "data": null,
  "metadata": {
    "exchange": "NASDAQ",
    "symbol": "AAPL",
    "start_page": 1,
    "end_page": 2,
    "sort_by": "popular",
    "total": 1,
    "pages": 2,
    "failed_pages": [[2, "Network error: ..."]]
  },
  "error": "Failed pages: [(2, 'Network error: ...')]. Articles collected so far: 1"
}
```
